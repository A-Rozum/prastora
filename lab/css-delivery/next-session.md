# Continuation: early structure and lazy styling

## Agreed direction

Use `lazy.css` as the canonical name for styles applied after initial content rendering. Late delivery does not imply that the styles are dispensable. `print.css` is a required part of page presentation; its detailed design and extraction are reserved for a separate session. Keep `media="print"` for print styles and an ordinary screen stylesheet link before the closing body tag for the proposed lazy experiment.

The target roles are core.css (shared base), site/layout CSS (selected initial rules), lazy.css (later rules), and print.css (print presentation). Source modules remain readable and grouped by component; output roles need not require separate source files per component. Composition/minification takes place during release preparation.

Initial styles should establish stable geometry through grids, spacing, positioning, media proportions and appropriate text metrics. Dynamic text, different languages and screen regimes must remain supported; fixed heights for arbitrary text are not the general solution. Keep sufficient initial contrast, visible controls, focus and validation feedback. Shadows, ornaments and other refinements can be late only where they do not carry essential information. Classification depends on context and dependencies, including custom properties and cascade order.

The previous footer experiment found transient differences on fragment navigation. That is a reason to examine the split and its early layout rules, not a general rejection of end-of-body CSS. The general experiment below has not been implemented or measured.

## Confirmed state to retain

- [Completed measurements and deployed minification/form changes](placement.md), with [raw corrected results](placement-results.json).
- Shared .field-error/.form-status feedback belongs to Prastora; submission processing remains in Rudy.
- Current expertise-law.eu layouts use two prebuilt critical links in head, with canonical names and cache revalidation. This handoff makes no runtime or hosting changes.
- Experimental pages retain noindex/nofollow.
- Existing hosting Actions-to-SSH comparison workflow and checked release tools are available. Use affected/dependent checks and isolated fixtures with submission disabled.

## First action next session

Start with a small generic Prastora fixture rather than another extraction of the site's footer. Define and implement the early/late rule split explicitly before measuring it.

Include a responsive grid, cards with unequal text lengths, media with reserved proportions, navigation and a form. Exercise light/dark schemes, supported screen regimes, short/long texts and more than one language. Preserve geometry, reading and usability with lazy.css intentionally held, then compare final appearance and ordinary load timings. Cover top entry, direct fragments, early interaction and JavaScript-disabled loading.

Compare identical rules delivered together with rules split into early CSS plus lazy.css. Separate file-count/network effects from stylesheet position by retaining the matched all-in-head control. Assess actual paints and request timing in addition to geometry. Keep print.css refinement as separate work.

Use the result to decide the reusable Prastora rule classification and release-plan integration for Rudy. Avoid assigning all declarations of a property or all rules of a component to one phase automatically. This session records the direction and point of return; the experiment is deferred to the next session.

## Release transition and rebuild automation: next-session scope

The transition from editable source modules to delivery files already occurs during release preparation. In Rudy, templates/styles.json explicitly maps ordered sources to core/site/member outputs; the pinned Prastora tools/styles.py generates/minifies them and emits hashes in tools/styles-manifest.json. CI currently rejects missing or stale outputs before runtime assembly. This is deterministic composition from a maintained plan; the general core/site/lazy/print split and unattended refresh of that plan are not yet implemented.

After validating the generic early/late experiment, extend the existing preparation mechanism rather than adding a separate build system:

- Keep one authoritative delivery description per site/layout, using shared Prastora component metadata where appropriate. Record rule roles and dependencies explicitly, including components that supply both initial and lazy rules. Decide the concrete representation with the experiment; do not reclassify styles from scratch for every edit.
- Resolve the selected components and dependencies into canonical core.css, site/layout CSS, lazy.css and print.css. A role describes timing, not dispensability; print presentation is required. Preserve source order, layer declarations and custom-property dependencies.
- Add automatic generation to release preparation: resolve the existing delivery description, rebuild affected outputs when inputs/configuration/tool versions change, minify, and record provenance. CI should verify freshness/reproducibility of the prepared artifacts.
- Reuse and first discover Rudy's existing runtime preparation and hosting update mechanism. The deployed release includes ready assets; PHP requests do not build CSS.
- Integrate template link generation or verification with the same delivery description so file contents and loading positions stay consistent.
- Require classification when introducing or materially changing a component's delivery behavior. Ordinary source edits reuse that classification. New unclassified rules remain initially loaded until classified, rather than being silently deferred by a property-name/viewport heuristic.
- Check affected outputs and consuming layouts/states, including required print assets. Avoid full-site testing after every unrelated change.

Deliver a stable preparation command/integration that an agent can invoke without manually deciding which source goes into which output on every rebuild. Keep readable modular sources in development. This automation is authorized for the same next session, after the classification experiment; no implementation is requested in the current handoff-only session.
