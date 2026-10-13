# Shared elements of templates
Every template has the utility strip at the top and the cookie consent bar at the bottom, copied from templates/product.html. Other components are used as needed.

Real-company and real-site prototypes include `<meta name="robots" content="noindex, nofollow">` in the head. Register each preview path pattern in `check.py` (`PREVIEW_GLOBS`). This applies to every language, service, article and member mini-site page, including custom designs. The gate checks HTML heads, not stylesheet files. Keep the directive on preview copies; enable indexing only for an explicitly requested production release.

Keep canonical asset filenames and stylesheet URLs on prototype sites. Use temporary cache-busting URLs only on explicit user request and restore the canonical URLs when that temporary use ends.
