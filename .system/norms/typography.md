Plyń base typography: in prose produced in the system – text an agent generates, writes or edits, in repositories, on sites and in replies – each problematic character has one permitted form.

- Dash: `–` (U+2013), with spaces between words and without them in ranges (2026–2027); never `—` or `―`.
- Double quotation marks: `"` (U+0022); never `«` `»` `“` `”` `„` `‟`.
- Single quotation marks and apostrophe: `'` (U+0027); never `‘` `’` `‚` `‛` `‹` `›`.

Code keeps what the code needs: code files, code blocks and inline code in prose, and front matter.

A project outside Plyń uses this base unless its owner sets other rules for it in typography.yaml at the project's root: `dash: em` or `dash: keep` leaves dashes as written, `quotes: keep` leaves quotation marks as written, `hook: <path>` names the project's own commit hook for any further rules. These rules apply in that project only.

The tools apply the base at every commit made in an agent's environment and at every landing.
