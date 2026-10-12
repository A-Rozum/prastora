# Prepare image assets

Use `tools/images.py` for raster crops, resize, WebP conversion and byte budgets. It accepts paths from the caller's working directory and works for Prastora templates and independent sites, including Rudy. Install `Pillow>=10` in the agent's Python environment; visitors need no Python dependency.

```sh
python3 /path/to/prastora/tools/images.py inspect source.jpg
python3 /path/to/prastora/tools/images.py convert source.jpg public/images/person.webp --size 640x640 --focal 0.6,0.35 --zoom 1.2 --quality 84 --min-quality 76 --max-bytes 65536
```

Inspect the source first. Focal coordinates are normalized in the image after EXIF orientation; 0,0 is top-left and 1,1 bottom-right. `--zoom` narrows the cover crop around that point. For exact framing use `--crop x,y,width,height` in oriented source pixels. Cover preserves the target aspect ratio without stretching. Contain retains the whole image with padding; use `--fit contain` and optionally `--background white`. Transparency is preserved unless a background is requested. `--lossless` suits graphics.

No enlargement is performed unless `--allow-upscale` is explicit. Prefer a larger source when detail is insufficient. A failed byte budget leaves the existing output unchanged; adjust dimensions or the budget rather than lowering quality without inspection. Existing derivatives require `--overwrite`; the original is never overwritten.

Portrait cards use a square 1:1 frame. Create 320x320 and 640x640 derivatives from the same crop, use `srcset`, supply width and height, and load below-the-fold photos lazily. Check each face at both card size and full resolution. Record the source and crop in the site's asset manifest; keep originals outside public assets. Use the site's reusable SVG placeholder when no portrait exists.

The converter normalizes embedded color profiles to sRGB, uses Lanczos resampling and WebP method 6, and removes source EXIF/GPS and comments from derivatives. It prints JSON dimensions, crop box, chosen quality, byte count and checksum for inspection and reproducibility.

## Asset names

Use `<name>-<role>-<ratio>-<width>w.<format>`, for example `alaksiej-michalevic-portrait-1x1-320w.webp`. `name` is a stable first-name–surname identifier for a person, preferably their published professional spelling; store it as `asset_name` in the site's expert data. Choose it once rather than transliterating it afresh from each caption. Non-person images use a descriptive subject, such as `courtroom`. Use lowercase ASCII words separated by hyphens.

`role` describes the intended composition: `portrait` for an expert's head-and-shoulders photo, `hero` for a page banner, `article` for an in-content image, and `thumbnail` for a compact preview. Choose another clear role when needed; a different crop intended for another placement gets its own role. Reduce ratios to their simplest form (`1x1`, `4x5`, `16x9`). Width is the actual output width, not a device label; the extension records the encoding.

The converter derives ratio, width and extension from the requested output. With `--name` and `--role`, the output argument is a directory:

```sh
python3 /path/to/prastora/tools/images.py convert source.jpg public/images --name alaksiej-michalevic --role portrait --size 320x320 --crop 472,0,976,976
python3 /path/to/prastora/tools/images.py convert source.jpg public/images --name alaksiej-michalevic --role portrait --size 640x640 --crop 472,0,976,976
```

Current expertise cards use `portrait-1x1-320w` and profiles use `portrait-1x1-640w`; both sizes also participate in responsive `srcset`. A future tall profile image can use `portrait-4x5-640w`, while a wide banner uses `hero-16x9-1280w`. Record the role, source, crop and generated paths in the asset manifest. Keep originals unchanged outside public assets. SVG placeholders use a descriptive name without a raster width. An explicit WebP filename remains available for callers with their own naming convention.
