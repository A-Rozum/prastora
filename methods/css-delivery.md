# CSS delivery

A delivery decision belongs to a page/layout and its supported states, not permanently to a component. The same component can be offscreen on one page and immediately visible on another. Keep ordinary stylesheet links as the safe default. Link only used modules; preserve the layer declaration and source order described in [CSS layering](../norms/css-layering.md).

## Optional release bundles

A deployment can combine selected CSS into canonical files with `tools/styles.py`. Source modules remain separately editable and directly usable in HTML; Prastora does not require a frontend build. Generate during preparation of a release, never while serving a PHP request. Start with shared/site and layout bundles when that improves measured cold and cross-layout navigation. One file per entire page is an alternative to measure, not a universal rule.

A trusted JSON plan uses `format: 1` and `bundles`, mapping each output URL to an ordered list of source URLs. Run:

```
python3 tools/styles.py site-styles.json --root public > style-sources.json
python3 tools/styles.py site-styles.json --root public --check
```

The root is the site's asset root (`.` for this repository). The tool emits source/output hashes as provenance and checks generated contents deterministically. Inputs use explicit module lists and root-relative, absolute or data CSS URLs. Imports and relative URLs fail with an actionable error rather than silently breaking after relocation. Templates reference the chosen canonical output paths. Existing deployment verification follows those output dependencies. Use revalidation (ETag/Last-Modified and suitable Cache-Control) to refresh canonical URLs; do not use immutable long caching for files whose names remain unchanged.

## Non-blocking styles

Only defer rules that are unnecessary for the initial viewport, direct fragment navigation, early interaction and server-rendered errors. Reserve geometry in critical CSS. Theme, main content, navigation and form error feedback are ordinarily critical. A component opening later may load its styles on demand, but its interaction must await successful stylesheet readiness.

The `media="print"` pattern starts a low-priority fetch without blocking screen rendering; after load an external listener changes media to the intended value. This is asynchronous application, not a promise that downloading starts last. A noscript stylesheet in the same cascade position preserves native behavior. Inline `onload` requires a CSP exception, so avoid it under restrictive CSP. Handle cached sheets, failure and late completion explicitly. The experiment loader in [lab/css-delivery](../lab/css-delivery/) is a prototype, not a required production dependency.

Viewport-extracted critical CSS is also optional. Its coverage must include all regimes, both themes, direct fragment navigation, menus, validation and response states. Invalidate the generated critical rules whenever their HTML, CSS or asset dependencies change. Pair inline styles with CSP hashes/nonces and a full stylesheet fallback; never weaken the entire style policy to make an optimisation work.

## Verification and other resource hints

Compare interleaved repeated runs under declared network/CPU profiles: cold cache, repeat navigation and a different layout. Record FCP/LCP, layout shifts, bytes and requests, as well as correctness with slow/failed deferred CSS and without JavaScript. Small noisy improvements are not a reason to introduce a failure mode. Scope later checks to affected layouts and dependencies.

`fetchpriority` changes a priority hint; it does not remove stylesheet render blocking. Preloading CSS already discoverable near the start of head is often redundant; indiscriminate preloading can compete with the main image. HTTP 103 Early Hints can start known critical requests during server processing, but needs support from the actual serving chain. It is an optional hosting capability. `content-visibility: auto` can reduce rendering of offscreen content; it does not remove blocking CSS downloads and needs appropriate size reservation and accessibility checks.

Sources and reproducible measurements: [CSS delivery experiment](../lab/css-delivery/README.md).
