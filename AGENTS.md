Static HTML/CSS, no build. GitHub Pages serves main.

Deliberate, keep unless told otherwise:
- Root font-size = 100vw / --scale-units, set per regime. No clamp, caps or max-width containers; --scale-min stays 0. Jumps between regimes are intended.
- Media queries in em only.
- CSS lengths in rem only.
- JS only where HTML/CSS have no equivalent, with a working no-JS fallback.
- CSS lives in css/ by layer: core.css, themes/ (custom properties only), components/, pages/ (demo compositions), dev/ (development aids). Pages link only what they use, in that order.
- Width breakpoints: only the regime queries listed in core.css. Regime-based show/hide: .desktop-only / .mobile-only.

Gate: `python3 check.py` exits 0.
Visual check: `tools/snap.py` (base before, diff after). Only pages linking the changed files (--css) and only the regimes the change touches.
