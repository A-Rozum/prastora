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
