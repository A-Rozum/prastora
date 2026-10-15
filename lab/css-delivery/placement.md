# Ordinary stylesheet placement: measured result

Measured on 2026-10-14. Keep the deployed two-file critical CSS baseline for expertise-law.eu. Ordinary screen stylesheets before the closing body tag demonstrably allow painting while those styles are pending, but this small footer split did not consistently accelerate these pages. End-of-body delivery remains an optional per-layout choice for genuinely noncritical styles.

## Implementation already deployed

Rudy source `102ea08838f35951511240daffc9961c59d00718` uses Prastora's existing `.field-error` and `aria-describedby`, plus generic `.form-status`, for native and server validation. Rudy's separate enquiries stylesheet and parallel error markers were removed. Shared form feedback remains critical. The framework provides semantic error/success colours; PHP submission processing stays in Rudy.

The release tool in Prastora composes explicitly selected modules and optionally minifies with pinned Lightning CSS 1.33.0. Rudy invokes it during release preparation, checks source/output hashes, and ships canonical prebuilt files. Readable modules remain editable; no compilation runs during a PHP request. Each deployed layout links `core.css` plus either `site.css` or `member.css`. The tiny directory reset is included in site.css.

| Bundle | Readable bytes | Minified bytes | Readable gzip bytes | Minified gzip bytes |
|---|---:|---:|---:|---:|
| Core | 5854 | 4170 | 2127 | 1630 |
| Association/site | 43804 | 34544 | 8783 | 7198 |
| Member | 36949 | 28692 | 7804 | 6160 |

The Association pair decreased from 49,658 to 38,714 raw bytes (about 22%), and from 10,910 to 8,828 gzip bytes (about 19%). Gzip figures are deterministic local comparisons, not exact HTTP transfers including headers on every host.

Prastora's browser checks covered 24 combinations of default/institution themes, light/dark schemes, three widths and readable/minified CSS. Rudy checks covered native/server errors, network/non-JSON failure, retained retry data and native POST. Deployment verification covered 17 dependent routes and four changed resources. A further public probe verified all three layouts, two CSS links, associated error slots, no legacy markers, noindex/nofollow, CSS MIME/cache headers and conditional HTTP 304. Backend mail and quarantine behavior was unchanged.

- [Verified deployment](https://github.com/A-Rozum/hosting/blob/main/results/rudy-update-38642184371.txt)
- [Public layout/resource probe](https://github.com/A-Rozum/hosting/blob/main/results/prastora-feedback-verify.txt)

## Placement method and provenance

The corrected harness source is [9551c6b2081d84e2b017a38eff34b9a8792496a4](https://github.com/A-Rozum/prastora/commit/9551c6b2081d84e2b017a38eff34b9a8792496a4). [Hosting run 38644961479](https://github.com/A-Rozum/hosting/actions/runs/38644961479) completed successfully; [raw results](placement-results.json) are copied unchanged from [the archived hosting report](https://github.com/A-Rozum/hosting/blob/main/results/css-comparison-38644961479.json). Measurement timestamp: `2026-10-14T22:08:04.065Z`.

Public home and member HTML snapshots were captured after deployment. Session tokens were stripped; isolated HTTPS fixtures retained noindex/nofollow and disabled submission/network form calls. No test enquiries were delivered. This measures static resources on the real hosting over HTTP/2, excluding dynamic PHP request processing.

Compare three variants:

| Variant | Critical links | Footer link |
|---|---|---|
| head | Original core + site/member in head | Included in site/member |
| tail-head | Core + reduced site/member in head | Ordinary stylesheet in head |
| tail-body | Same core + same reduced site/member in head | Same ordinary stylesheet immediately before closing body |

The two split variants have identical CSS contents and differ only in link position. No media=print, preload, inline onload or loader is used. Core stays intact. CSSOM extraction keeps cascade layers/source order and moves only leading explicit footer selectors; mixed selectors involving buttons/navigation stay critical. Footer files contain 851 bytes on home and 790 on member.

The first iteration used an overly broad selector classifier and moved mixed interactive rules. Its [preserved report](https://github.com/A-Rozum/hosting/blob/main/results/css-comparison-38642535831.json) is superseded for attribution of early geometry differences. The classifier was corrected and unit-tested before this separate final run. Those remaining differences must not all be attributed to a specific footer rule: the harness records differing geometry keys, not enough script/scroll state to establish that cause.

Chromium 141.0.7390.37, Playwright 1.56.1. Profiles:

| Profile | Viewport | Configured latency | Download throughput | CPU multiplier |
|---|---|---:|---:|---:|
| Mobile | 390 × 844 | 150 ms | 1.6 Mbps | 4× |
| Desktop | 1280 × 900 | 20 ms | 10 Mbps | 1× |

Three interleaved repeats cover cold HTTP cache, repeated navigation and navigation from home to the other layout: 90 timing records. Canonical CSS uses no-cache conditional revalidation; cold does not guarantee fresh DNS/TLS. These small samples are exploratory medians, not real-user percentiles or proof of a small performance difference. They are not directly comparable with PageSpeed or WebPageTest profiles. The recorded blocking_ms is excess long-task duration after FCP within the harness window, not Lighthouse TBT.

## Correctness with the footer stylesheet held

The harness deliberately holds the footer response, waits for the critical sheets, and checks for actual FCP rather than assuming that measurable DOM geometry means the user saw a frame. It then releases the stylesheet and compares final geometry. Tests cover four widths, two schemes and normal/form/footer fragments on both pages.

| Split variant | Painted while footer held | Early geometry differences | Final geometry differences |
|---|---:|---:|---:|
| tail-head | 0 / 48 | 0 / 48 | 0 / 48 |
| tail-body | 48 / 48 | 32 / 48 | 0 / 48 |

All 16 normal top-of-page tail-body entries matched sampled early geometry. The 32 differences occurred on direct form/footer fragments (`#request`, `#contact`, `#css-lab-footer`); these supported entry paths prevent treating the entire split as unconditionally safe. After CSS arrived, sampled geometry matched in every case. Six additional no-JavaScript cases loaded the expected two or three stylesheets. Total: 102 quality records. Geometry sampling is not a pixel-by-pixel screenshot equivalence claim.

## Timing

Cold medians below are **FCP / LCP in milliseconds**:

| Profile / page | Two files in head | Footer split, all in head | Footer split, footer before body end |
|---|---:|---:|---:|
| mobile / home | 612 / 612 | 644 / 644 | 648 / 648 |
| mobile / member | 596 / 672 | 632 / 684 | 608 / 672 |
| desktop / home | 272 / 272 | 280 / 280 | 268 / 268 |
| desktop / member | 220 / 272 | 240 / 276 | 240 / 296 |

Ordinary timing runs recorded small CLS values (cold medians approximately 0.0001–0.0003). Holding CSS for quality checks is a separate deliberate delay.

The browser reported every measured tail-head stylesheet as render-blocking and every tail-body stylesheet as non-blocking. That does not postpone the download until after the first paint. For example, on mobile home the tail-body request began at median 306.5 ms and completed at 478.3 ms, before median FCP of 648 ms. In the matching tail-head variant the request began at 263.8 ms, ended at 443.2 ms, and FCP was 644 ms.

There is no consistent speed win over the two-file baseline. Mobile member FCP improved by 24 ms compared with the same three files all in head, but remained 12 ms behind the original two-file baseline. Desktop home was slightly faster; desktop member LCP was slower. Those small differences across three repeats do not justify a general speed claim, especially with another request for under 1 KB of footer CSS.

## Selected policy

- Critical theme, navigation, main content and native/server form feedback remain in head. Release composition uses shared core plus selected site/layout modules.
- Keep the current site's two canonical stylesheet links; no forced third/fourth file solely to satisfy a file-count target.
- An explicitly noncritical screen bundle may use an ordinary link before the closing body tag. Check direct fragments, supported early interactions and slow CSS as well as ordinary timings before selecting it for a layout.
- Print-only styles use media=print. On-demand/asynchronous activation is a separate strategy requiring its own readiness/failure behavior.
- Link position alone does not guarantee that network fetching happens last. Re-evaluate changed dependencies, preserving noindex during experiments.

See [CSS delivery](../../methods/css-delivery.md) for release/tool configuration and [the earlier six-way comparison](comparison.md) for the broader initial selection. The earlier data predates this form unification/minification release and is not mixed into these medians.
