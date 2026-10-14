# Forms and feedback

Use the existing `.field`, `.field-error`, `.field-hint` and `.field-row` component classes. Associate messages through the input's `aria-describedby`; multiple IDs can include both a hint and an error. Business code supplies text and states, not a second set of styling selectors.

Untouched required fields are not shown as errors. Native `:user-invalid` and explicit `aria-invalid="true"` receive the same field treatment. A nonempty `.field-error` is visible under either state; empty error slots remain hidden and occupy no space. Server validation must set aria-invalid as well as the message. A corrected input clears its explicit state/message through the form controller; ordinary HTML validation remains available without JavaScript.

Use `.form-status` for the operation result, with `data-state="sending|error|success|idle"`. An error uses role=alert; progress and success use role=status, with an appropriate live region when updated. Do not rely on red alone: show explanatory text and focus the applicable field or status region. If an operation fails without a known field, show a form-level error; a site can additionally identify its message field as the place to resume.

The core supplies default --error and --success colours. Themes can override these semantic tokens for their schemes. Pending submission uses form aria-busy=true; a disabled control alone does not mean an operation is running. The full feedback styles are part of the form module and load with its critical layout, including direct links to the form and server-rendered responses.
