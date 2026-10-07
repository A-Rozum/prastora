# Kernel (Prastora)

Static HTML/CSS, no build; GitHub Pages serves main.
Navigation: system.yaml; elements.yaml lists elements with computable applicability. Select what a task needs:
`python .system/tools/select.py . domain=web.css task_kind=implementation [subject=<component|template|theme>]`

Core invariants (any CSS work):
- Root font-size = 100vw / --scale-units, set per regime. No clamp, caps or max-width containers; --scale-min stays 0. Jumps between regimes are intended. A page may set a denser --scale-units per regime (see dashboard).
- CSS lengths in rem only.

Gate: `python3 check.py` exits 0 and `python .system/tools/validate.py . --formats .system/formats` passes.
Temporary material goes to lab/ (lab.yaml), never to ad-hoc folders.
