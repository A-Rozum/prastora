# Kernel (Prastora)

Static HTML/CSS, no build; GitHub Pages serves main.
Navigation: system.yaml; elements.yaml lists elements with computable applicability. At the start of a task compile its context and read it instead of browsing:
`python .system/tools/pn_compile.py . domain=web.css task_kind=implementation [subject=<component|template|theme>]` → .context/task.md

Core invariants (any CSS work):
- Root font-size = 100vw / --scale-units, set per regime. No clamp, caps or max-width containers; --scale-min stays 0. Jumps between regimes are intended. A page may set a denser --scale-units per regime (see dashboard).
- CSS lengths in rem only.

Gate: `python3 check.py` exits 0 and `python .system/tools/pn_validate.py . --formats .system/formats` passes.
Temporary material goes to lab/ (lab.yaml), never to ad-hoc folders.
