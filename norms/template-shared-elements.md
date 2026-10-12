# Shared elements of templates
Every template has the utility strip at the top and the cookie consent bar at the bottom, copied from templates/product.html. Other components are used as needed.

Real-company and real-site prototypes include `<meta name="robots" content="noindex">` in the head. Register each preview path pattern in `check.py` (`PREVIEW_GLOBS`). Keep the directive on preview copies when preparing an indexable production copy.

Keep canonical asset filenames and stylesheet URLs on prototype sites. Use temporary cache-busting URLs only on explicit user request and restore the canonical URLs when that temporary use ends.
