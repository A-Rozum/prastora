Static HTML/CSS, no build. GitHub Pages serves main.

Deliberate, keep unless told otherwise:
- Root font-size = 100vw / --scale-units, set per regime. No clamp, caps or max-width containers; --scale-min stays 0. Jumps between regimes are intended.
- CSS lengths in rem only.
- JS only where HTML/CSS have no equivalent, with a working no-JS fallback.
- CSS lives in css/ by layer: core.css, themes/ (custom properties only), components/, pages/ (CSS of one page, same name as the page), dev/ (development aids). Pages link only what they use, in that order.
- HTML: framework pages in the root, component catalogue in components/, demo templates in templates/.
- Copy in English, lively and varied in register. Humour and self-irony woven into the text's logic, never bolted on; tease gently, never mock others. Templates use plausible fictional content of their field, marked as demo.

Gate: `python3 check.py` exits 0.
Visual check: `tools/snap.py` (base before, diff after). Only pages linking the changed files (--css) and only the regimes the change touches.
