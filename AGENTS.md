Static HTML/CSS, no build. GitHub Pages serves main.

Deliberate, keep unless told otherwise:
- Root font-size = 100vw / --scale-units, set per regime. No clamp, caps or max-width containers; --scale-min stays 0. Jumps between regimes are intended.
- Media queries in em only.
- CSS lengths in rem only.
- JS only where HTML/CSS have no equivalent, with a working no-JS fallback.
- CSS lives in css/ by layer: core.css, themes/ (custom properties only), components/, pages/ (demo compositions), dev/ (development aids). Pages link only what they use, in that order.

Gate: `python3 check.py` exits 0.
Verify in proportion to risk: one width per scale regime is enough unless a change targets a regime boundary.
