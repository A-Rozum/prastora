Static HTML/CSS, no build. GitHub Pages serves main.

Deliberate, keep unless told otherwise:
- Root font-size = 100vw / --scale-units, set per regime. No clamp, caps or max-width containers; --scale-min stays 0. Jumps between regimes are intended.
- Media queries in em only.
- CSS lengths in rem only.
- Pages must work without JS. Use JS only where HTML/CSS have no equivalent.

Gate: `python3 check.py` exits 0.
