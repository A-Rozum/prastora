#!/usr/bin/env python3
"""Portable image preparation for Prastora and sites built with it. Requires Pillow."""
import argparse
import hashlib
import io
import json
import math
import os
from pathlib import Path
import tempfile

from PIL import Image, ImageCms, ImageColor, ImageOps, features


def pair(value):
    try:
        result = tuple(float(x) for x in value.split(","))
    except ValueError as exc:
        raise argparse.ArgumentTypeError("Use two numbers separated by a comma") from exc
    if len(result) != 2 or not all(math.isfinite(x) and 0 <= x <= 1 for x in result):
        raise argparse.ArgumentTypeError("Focal coordinates must be between 0 and 1")
    return result


def size(value):
    try:
        result = tuple(int(x) for x in value.lower().split("x"))
    except ValueError as exc:
        raise argparse.ArgumentTypeError("Use WIDTHxHEIGHT") from exc
    if len(result) != 2 or min(result) < 1:
        raise argparse.ArgumentTypeError("Dimensions must be positive integers")
    return result


def rectangle(value):
    try:
        result = tuple(int(x) for x in value.split(","))
    except ValueError as exc:
        raise argparse.ArgumentTypeError("Use x,y,width,height") from exc
    if len(result) != 4 or min(result[:2]) < 0 or min(result[2:]) < 1:
        raise argparse.ArgumentTypeError("Crop needs non-negative x,y and positive width,height")
    return result


def load_image(path):
    with Image.open(path) as source:
        if getattr(source, "n_frames", 1) != 1:
            raise ValueError("Animated inputs need an explicitly selected still frame")
        original_size = source.size
        image = ImageOps.exif_transpose(source)
        image.load()
        profile = source.info.get("icc_profile")
        alpha = image.convert("RGBA").getchannel("A") if (
            "A" in image.getbands() or "transparency" in image.info
        ) else None
        if profile:
            color = image if image.mode in ("RGB", "CMYK", "L") else image.convert("RGB")
            image = ImageCms.profileToProfile(
                color, ImageCms.ImageCmsProfile(io.BytesIO(profile)),
                ImageCms.createProfile("sRGB"), outputMode="RGB",
            )
        else:
            image = image.convert("RGB")
        if alpha is not None:
            image.putalpha(alpha)
        return image, original_size


def prepare(image, target, fit="cover", focal=(.5, .5), zoom=1, crop=None,
            allow_upscale=False, background=None):
    if not math.isfinite(zoom) or zoom < 1:
        raise ValueError("Zoom must be at least 1")
    if fit == "contain" and (zoom != 1 or focal != (.5, .5)):
        raise ValueError("Focal point and zoom apply to cover mode")
    origin = (0, 0)
    if crop:
        x, y, width, height = crop
        if x + width > image.width or y + height > image.height:
            raise ValueError("Crop extends beyond the oriented image")
        image = image.crop((x, y, x + width, y + height))
        origin = (x, y)
    width, height = image.size
    tw, th = target
    if fit == "cover":
        ratio = tw / th
        cw, ch = (height * ratio, height) if width / height > ratio else (width, width / ratio)
        cw, ch = cw / zoom, ch / zoom
        left = min(max(focal[0] * width - cw / 2, 0), width - cw)
        top = min(max(focal[1] * height - ch / 2, 0), height - ch)
        if not allow_upscale and (tw > cw + .01 or th > ch + .01):
            raise ValueError("Requested size would upscale the crop; use a smaller size or --allow-upscale")
        box = (left, top, left + cw, top + ch)
        result = image.resize(target, Image.Resampling.LANCZOS, box=box)
        box = [round(v + origin[i % 2], 3) for i, v in enumerate(box)]
    else:
        scale = min(tw / width, th / height)
        if scale > 1 and not allow_upscale:
            raise ValueError("Requested size would upscale the image; use --allow-upscale")
        scaled = image.resize((max(1, round(width * scale)), max(1, round(height * scale))),
                              Image.Resampling.LANCZOS)
        rgba = image.mode == "RGBA" and background is None
        result = Image.new("RGBA" if rgba else "RGB", target,
                           (0, 0, 0, 0) if rgba else ImageColor.getrgb(background or "white"))
        if scaled.mode == "RGBA" and result.mode == "RGB":
            result.paste(scaled, ((tw - scaled.width) // 2, (th - scaled.height) // 2), scaled)
        else:
            result.paste(scaled, ((tw - scaled.width) // 2, (th - scaled.height) // 2))
        box = [origin[0], origin[1], origin[0] + width, origin[1] + height]
    if background is not None and result.mode == "RGBA":
        flattened = Image.new("RGB", result.size, ImageColor.getrgb(background))
        flattened.paste(result, mask=result.getchannel("A"))
        result = flattened
    # Fresh image removes EXIF, GPS, comments and source profiles after sRGB conversion.
    clean = Image.new(result.mode, result.size)
    clean.paste(result)
    return clean, box


def encode(image, quality=84, min_quality=72, max_bytes=None, lossless=False):
    if not features.check("webp"):
        raise ValueError("Pillow needs WebP support")
    if not 0 <= min_quality <= quality <= 100:
        raise ValueError("Use 0 <= min-quality <= quality <= 100")
    if max_bytes is not None and max_bytes < 1:
        raise ValueError("max-bytes must be positive")
    for q in ([quality] if lossless or not max_bytes else range(quality, min_quality - 1, -1)):
        buffer = io.BytesIO()
        image.save(buffer, "WEBP", quality=q, method=6, lossless=lossless, exact=True)
        data = buffer.getvalue()
        if max_bytes is None or len(data) <= max_bytes:
            return data, q
    raise ValueError("Byte budget cannot be met at the chosen dimensions and minimum quality")


def convert(source, destination, target, **options):
    source, destination = Path(source), Path(destination)
    overwrite = options.pop("overwrite", False)
    if source.resolve() == destination.resolve():
        raise ValueError("Source and destination must differ")
    if destination.suffix.lower() != ".webp":
        raise ValueError("Destination must use .webp")
    if destination.exists() and not overwrite:
        raise ValueError("Destination exists; choose a new name or --overwrite")
    image, original_size = load_image(source)
    oriented_size = image.size
    encoding = {k: options.pop(k) for k in ("quality", "min_quality", "max_bytes", "lossless") if k in options}
    result, box = prepare(image, target, **options)
    data, quality = encode(result, **encoding)
    destination.parent.mkdir(parents=True, exist_ok=True)
    # Encode completely before touching an existing derivative.
    fd, temporary = tempfile.mkstemp(prefix="image-", suffix=".webp", dir=destination.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
        if overwrite:
            os.replace(temporary, destination)
        else:
            # Exclusive creation also protects against a competing writer.
            os.link(temporary, destination)
            os.unlink(temporary)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return {"source": str(source), "output": str(destination), "source_size": original_size,
            "oriented_size": oriented_size, "crop_box": box, "size": result.size,
            "format": "WEBP", "quality": quality, "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest(), "alpha": result.mode == "RGBA"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    inspect = sub.add_parser("inspect", help="Report dimensions, orientation and format")
    inspect.add_argument("source", type=Path)
    command = sub.add_parser("convert", help="Crop, resize, normalize and optimize a WebP derivative")
    command.add_argument("source", type=Path)
    command.add_argument("output", type=Path)
    command.add_argument("--size", type=size, required=True, metavar="WIDTHxHEIGHT")
    command.add_argument("--fit", choices=("cover", "contain"), default="cover")
    command.add_argument("--focal", type=pair, default=(.5, .5), metavar="X,Y")
    command.add_argument("--zoom", type=float, default=1)
    command.add_argument("--crop", type=rectangle, metavar="X,Y,WIDTH,HEIGHT")
    command.add_argument("--background", help="Flatten transparency onto a CSS color")
    command.add_argument("--allow-upscale", action="store_true")
    command.add_argument("--quality", type=int, default=84)
    command.add_argument("--min-quality", type=int, default=72)
    command.add_argument("--max-bytes", type=int)
    command.add_argument("--lossless", action="store_true")
    command.add_argument("--overwrite", action="store_true")
    args = vars(parser.parse_args())
    action = args.pop("command")
    try:
        if action == "inspect":
            path = args["source"]
            with Image.open(path) as im:
                result = {"source": str(path), "size": im.size,
                          "oriented_size": ImageOps.exif_transpose(im).size,
                          "format": im.format, "mode": im.mode,
                          "frames": getattr(im, "n_frames", 1),
                          "bytes": path.stat().st_size, "icc": bool(im.info.get("icc_profile"))}
        else:
            source, output, target = args.pop("source"), args.pop("output"), args.pop("size")
            result = convert(source, output, target, **args)
    except (OSError, ValueError, ImageCms.PyCMSError) as exc:
        parser.exit(1, f"Image preparation failed: {exc}\n")
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()

