# First pass

After the Remwork rename and English copy rewrite, local reference checks again passed (five pages, zero errors). Browser geometry was rechecked at all 12 widths below in LTR and RTL with disclosures expanded: 120 configurations, no visible element overflow found. The starter's code samples wrap within their containers. This recheck does not establish accessibility or physical-device readability.

Five static page examples, two CSS files and a shared SVG sprite. No client JavaScript or external requests are required. check.py checks local references, fragments, duplicate IDs and absence of script tags; run with `python check.py`.

Browser geometry checked at 320, 360, 390, 423, 609, 800, 801, 1280, 1463, 1999, 2000 and 2560 CSS pixels for all five pages, both LTR and RTL (120 configurations): no visible element overflow found. Expanded mobile menus checked on all pages at 320, 423 and 609px: no overflow. Enter opened the main page's native menu. Corresponding subgrid list rows had matching top coordinates at 423px. Arabic/Chinese text samples were inserted temporarily in the browser; Arabic quote border appeared on the right. SVG artwork was visible in a desktop screenshot.

These are not physical device or translation quality tests. Full keyboard traversal, screen readers, print output, measured cold-load performance and browser zoom remain to be reviewed. The scaling follows the existing site: mobile/desktop and wide-screen breakpoints still change sizes abruptly at 800/801 and 1999/2000. Viewport-only scaling may counteract browser zoom; this is not solved in the first pass. At 423px the normal text computes to about 13.7px; at 320px about 10.4px. The optional --scale-min floor can be discussed separately.

Placeholders, product statuses and prices are illustrative. No real enquiry processing, shopping cart, payment, translations, locale routing or external video integration is implemented. The first five pages intentionally include only a team section, not a separate team page. Remaining page types can be added after review.
