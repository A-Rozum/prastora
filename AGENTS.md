# Project scope

- Prastora is an independent experimental CSS toolkit. Do not modify legal-status, framework or HTML archives when working here.
- Public-facing copy is English and describes the toolkit, its approach and page patterns, not a fictional company. Keep claims proportional to implemented features.
- core.css contains reusable layout primitives; theme.css contains demonstration branding and composition.
- Keep full-width proportional rem scaling (128 units desktop, 64 mobile, 160 wide screens). Typography follows the tested mobile sizes from legal-status. No default max-width container or upper scale cap. --scale-min is an optional configurable floor, not enabled by default.
- index, service, article, catalog and product are static examples, not a CMS or shop. No client JavaScript, third-party fonts, trackers or embeds. Forms are disabled until a real backend is configured. Do not imply placeholder links, media or prices are real.
- Shared headers are duplicated deliberately for this first static pass; keep navigation consistent across all five pages. Consider build-time templates later, not browser injection.
- User-approved temporary exception: assets/viewport.js and viewport.css display the layout viewport in CSS pixels on all five pages for device review. Keep them separate from core; the site works without this script. Remove their HTML hooks and checker exception when retiring diagnostics.
- Do not use px for CSS dimensions. Component sizes use rem; media queries use em (50em / 125em) to keep thresholds independent of the viewport-linked root scale. The utility strip includes an English-only language control and disabled sign-in example, not real translation or authentication.
- Use logical CSS properties and test whole-page RTL and mixed Arabic/Chinese content. Translation routing is not implemented; future translations must preserve page identity.
- .aligned is opt-in for cards with one heading and --items list rows. It is not suitable for arbitrary card markup; ordinary lists use .prose.
- Test 320, 360, 390, 423, 609, 800, 801, 1280, 1463, 1999, 2000 and 2560 CSS pixels. Check menu, disclosures, wrapping, SVG placeholders, keyboard focus and overflow. Do not treat geometry checks as physical phone testing.
- Never publish a new remote repository without confirming its destination and visibility with the user.
