# CSS delivery experiment

Completed: [initial comparison and selected baseline](comparison.md), [initial raw measurements](results.json), then [ordinary head/body placement, form unification and release minification](placement.md) with [corrected placement measurements](placement-results.json). Production uses two minified critical files in head. End-of-body styles are an optional measured per-layout choice; the separate non-blocking loader remains a lab prototype.

Question: Which stylesheet delivery policy improves first rendering while preserving Prastora's geometry, cascade, themes and native HTML behavior?

The comparison captures read-only public Association and member HTML from expertise-law.eu. Session tokens are removed; isolated fixture headers disable submission and network form calls. All variants use the same content and assets. Compare normal module links, deferred form modules, deferred enquiry-state styling, browser-selected critical CSS, one complete bundle and shared/page bundles. The stylesheet loader uses external event listeners under a restrictive CSP, preserves DOM link order and returns explicit readiness/failure. A noscript link supplies native styles.

`capture.py` prepares fixtures. `compare.mjs generate` samples critical rules across mobile, desktop, wide and short layouts in both schemes. This is a candidate extraction strategy, not a claim that viewport-only coverage proves complete correctness. `compare.mjs measure` checks first-paint styling with deferred CSS held, deep anchors, final geometry and native no-JS styles. It then interleaves three runs per strategy/profile, recording cold, repeated and cross-layout navigation under declared network/CPU conditions on the actual HTTPS hosting. Source data records the exact browser, captures and profiles; bundle outputs are derived fixture files.

Run through the existing `A-Rozum/hosting/.github/workflows/css-compare.yml` mechanism with a checked source commit. Measurements are committed to hosting/results and then analysed here. Fixtures are reproducible temporary files and removed after the run. Production selection follows evidence; default styles remain ordinary blocking links until an applicable delivery plan has been checked.

Sources:
- https://github.com/filamentgroup/loadCSS
- https://modpagespeed.com/docs/filters/prioritize_critical_css/
- https://web.dev/articles/fetch-priority
- https://web.dev/articles/defer-non-critical-css
- https://developer.chrome.com/docs/performance/insights/render-blocking
- https://www.catchpoint.com/webpagetest/results?publicurl=https%3A%2F%2Fpublic.catchpoint.com%2FUI%2FEntry%2FWPTITP%2FARRM-D-E-B2AD3_JjfKYYXHIAA-N

The provided WebPageTest desktop run uses Chrome 152 on WiFi 240/120 Mbps, 2 ms configured RTT, Council Bluffs (USA), 2026-10-14 18:20:47 UTC. FCP/LCP 655 ms, CLS 0, first byte 288 ms, start render 600 ms, speed index 610 ms, document complete 643 ms, total 674 ms, 17 requests and 29,298 bytes. Its waterfall identifies 10 CSS files plus theme-init as render-blocking; favicon.ico is an additional implicit request. These values describe that profile, not mobile performance or PHP processing alone.
