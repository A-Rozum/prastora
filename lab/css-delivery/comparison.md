# CSS delivery comparison — 2026-10-14

Selected baseline: ordinary blocking shared/layout bundles. Non-blocking CSS remains an explicit, checked enhancement for genuinely noncritical states.

## Method and limits

Six strategies; 180 timing records (three interleaved repetitions per profile/strategy/navigation case), 172 correctness cases. Chromium 141.0.7390.37; HTTPS HTTP/2 on expertise-law.eu. Mobile: 390×844, 150 ms RTT, 1.6 Mbps download, CPU slowdown 4×. Desktop: 1280×900, 20 ms RTT, 10 Mbps, CPU 1×. Browser device/network throttling is synthetic; this is not a field percentile or a Lighthouse score. Source HTML is read-only public snapshots; fixtures disable submission and are noindex/nofollow. PHP rendering and real enquiry transactions are outside this isolated CSS comparison. No JS checks verify applicable style counts and console errors, not every possible interaction.

All fixtures use no-cache with conditional revalidation, a deliberate canonical-URL delivery policy. Cold means an empty HTTP cache in a fresh browser context, not necessarily cold DNS/TLS. Three samples give directional evidence, not statistical certainty. TTFB varies and explains some timing variation. Blocking time is the recorded excess long-task duration after FCP, not Lighthouse TBT. Source data and profiles are in [results.json](results.json); experiment source 931c5150369e3ce6c1513b9a0d15c8e45c6604ec; [workflow]( https://github.com/A-Rozum/hosting/actions/runs/38621323976 ). The measurement completed successfully; the workflow’s final Git push collided with a concurrent main update. Its artifact was recovered without rerunning measurements; archival pushing now retries after rebasing.

## First paint / main content

Median milliseconds. Each cell is FCP / LCP.

| Strategy | Mobile home | Mobile member | Desktop home | Desktop member | CSS requests | First-paint checks with differences |
|---|---:|---:|---:|---:|---:|---:|
| Ordinary modules | 760 / 760 | 708 / 768 | 388 / 388 | 392 / 404 | 10 | baseline |
| Deferred forms + enquiry states | 732 / 732 | 688 / 780 | 372 / 372 | 304 / 356 | 10 | 16/32 |
| Deferred enquiry states only | 792 / 792 | 692 / 792 | 424 / 424 | 344 / 364 | 10 | 16/32 |
| Automatic inline critical CSS | 612 / 612 | 512 / 604 | 368 / 368 | 312 / 332 | 10 | 32/32 |
| One complete layout bundle | 680 / 680 | 656 / 716 | 380 / 380 | 296 / 344 | 1 | 0/32 |
| Shared + layout bundles | 716 / 716 | 644 / 700 | 328 / 328 | 312 / 360 | 2 | 0/32 |

## Cache reuse

| Strategy | Mobile repeated home FCP | Mobile member after home FCP / LCP | Member-after-home transferred bytes |
|---|---:|---:|---:|
| Ordinary modules | 512 | 500 / 580 | 34917 |
| One complete layout bundle | 452 | 512 / 556 | 39720 |
| Shared + layout bundles | 448 | 440 / 500 | 32449 |

## Correctness and decision

All final sampled geometry matched after full CSS arrived. Both bundle candidates also matched first-paint geometry in every sampled regime/theme and direct-fragment case. No-JS cases applied all expected style files and reported no console errors. Ordinary/bundled timing runs had tiny observed shifts (below 0.001); avoid claiming literal zero based on this sample.

Deferring forms altered layout on all 16 direct-fragment cases. Even deferring only enquiry states altered form/row height and email position in those cases: empty feedback elements need their hiding rules immediately. Early error presentation is also a critical contract; an enhancement cannot assume its feedback styles will have loaded. Keep both modules blocking.

The viewport-sampled automatic critical candidate omitted necessary layout/state rules: all 32 first-paint cases differed and timing CLS was around 0.21. This rejects this extractor/profile, not the entire critical-CSS technique. Reliable automatic coverage needs structure/interaction/state knowledge and regeneration when dependencies change; its complexity is unjustified here. It also transfers more total bytes because inline rules accompany full external CSS.

One full bundle slightly wins some first visits, but duplicates shared rules for each layout. Shared/layout bundles retain common bytes on partner navigation (about 32.4 KB versus 39.7 KB for one bundle in the mobile cross-layout case), preserve native behavior and require no additional browser script. On mobile home, first-paint median improves from 760 to 716 ms; repeated home from 512 to 448 ms; member after home from 500/580 to 440/500 ms. These are observed medians, not guaranteed savings on every connection.

## Framework and engine boundaries

Prastora: optional deterministic release bundler and delivery method; editable modules and ordinary HTML remain available without a mandatory build. Rudy: a trusted site/layout delivery plan, generated canonical assets included in its checked release and ordinary Fenom links. No CSS compilation, viewport analysis or visitor beacons during PHP requests. Deployment verification follows resulting asset dependencies. Deferred loading is explicit per-context, with CSP-safe listeners and native fallback when a later component actually needs it.

See [CSS delivery](../../methods/css-delivery.md) and the [experiment README](README.md) for sources and the provided WebPageTest interpretation.
