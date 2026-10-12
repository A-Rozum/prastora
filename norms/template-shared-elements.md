# Shared elements of templates
Every template has the utility strip at the top and the cookie consent bar at the bottom, copied from templates/product.html. Other components are used as needed.

Real-company and real-site prototypes include `<meta name="robots" content="noindex">` in the head. Register each preview path pattern in `check.py` (`PREVIEW_GLOBS`). Keep the directive on preview copies when preparing an indexable production copy.
