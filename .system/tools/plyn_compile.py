"""Compile the context for one task into .context/task.md — a vendor-neutral bundle any agent environment can read
(Claude Code via CLAUDE.md → AGENTS.md, Codex and OpenCode via AGENTS.md, a chat by uploading the file).
Usage: python tools/plyn_compile.py [repo_dir] domain=… task_kind=… [subject=…] [budget=…]
The bundle holds: task facets, open tasks from state.yaml, selected elements most specific first (content or head),
tools by reference, elements dropped by budget, and the fallback note if nothing normative matched."""
import sys, pathlib, datetime, yaml
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import plyn_select as _sel
parse, select = _sel.parse, _sel.select
from plyn_inputs import read, inventory, allowed_matters, in_scope, available_materials, missing_inputs

def main():
    # A failed compile must not leave a stale bundle from another task.
    root = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 and '=' not in sys.argv[1] else pathlib.Path('.')
    (root / '.context' / 'task.md').unlink(missing_ok=True)
    repo, task, budget, _ = parse(sys.argv[1:])
    elements = read(repo, 'elements.yaml')
    matters, materials = inventory(repo, elements)
    allowed = allowed_matters(matters, task)
    available = available_materials(repo, materials, allowed)
    missing = missing_inputs(_sel.eligible(repo, task), available)
    chosen, skipped, normative = select(repo, task, budget)
    out = [f"# Context for the current task", "",
           f"Compiled {datetime.datetime.now(datetime.timezone.utc):%Y-%m-%d %H:%M} UTC by tools/plyn_compile.py. Facets: " +
           ", ".join(f"{k}={v}" for k, v in task.items()) + ".",
           "Read this file instead of browsing the repository. More specific elements come first and override general ones; the jadro's invariants are never overridden.", ""]
    if missing:
        out += ['## Missing inputs', '',
                'Report these to the user before relying on them. How to proceed without them (wait, search, work on the client\'s account with marked uncertainty, draft but not file) is the user\'s decision, given in the task.', '']
        out += [f'- {element}: missing {kind}' for element, kind in missing] + ['']
    st = repo / "state.yaml"
    if st.exists():
        s = yaml.safe_load(st.read_text()) or {}
        out += ["## Open tasks (state.yaml)", ""]
        for t in s.get("tasks", []):
            if not in_scope(t, allowed): continue
            out.append(f"- [{t['status']}] {t['id']}: {t['title']} — done when: {t['done_when']} (executor: {t['executor']})")
        out.append("")
    if not normative:
        out += ["## Not anticipated", "", "No element applies beyond the kernel. Work from general knowledge and search with lowered trust; say in the result that the task was not anticipated, so the gap can be filled.", ""]
    refs = [p for p in chosen if p["mode"] == "reference"]
    demand = [p for p in chosen if p["mode"] == "demand"]
    for p in [p for p in chosen if p["mode"] not in ("reference", "demand")]:
        out += [f'<element id="{p["id"]}" path="{p["path"]}"' + (' load="head"' if p["mode"] == "head" else "") + ">", p["text"].strip(), "</element>", ""]
    exp_by_id = {e.get("id"): e.get("expects") for e in (elements or []) if isinstance(e, dict) and e.get("expects")}
    exp = [(p["id"], exp_by_id[p["id"]]) for p in chosen if p["id"] in exp_by_id]
    if exp:
        out += ["## Expected result (check before handing over; a departure in either direction goes to the project's feedback log)", "",
                "basic: without it the result fails; ordinary: a competent result has it; refinement: tolerable if missing. Meeting them does not make the result ideal.", ""]
        for eid, levels in exp:
            out.append(f"- {eid}")
            for lvl in ("basic", "ordinary", "refinement"):
                for c in levels.get(lvl, []):
                    out.append(f"  - {lvl}: {c}")
        out.append("")
    if demand:
        out += ["## Open when needed (sources: cite exactly from the file, never from memory)", ""] + [f"- {p['id']} — {p['path']} — {p['text']}" for p in demand] + [""]
    if refs:
        out += ["## Tools and checks (run, do not read)", ""] + [f"- {p['path']} — {p['text']}" for p in refs] + [""]
    if skipped:
        out += ["## Dropped by budget (open only if the task requires)", ""] + [f"- {p['id']} — {p['path']}" for p in skipped] + [""]
    if available:
        out += ['## Matter materials (only the permitted scope)', '']
        remaining = max(0, budget - sum(p['tokens'] for p in chosen))
        for m in available:
            mode = m.get('load', 'demand')
            if mode == 'demand':
                out += [f"- {m['id']} — {m['path']} — kind: {m['kind']}"]
                continue
            text = _sel.excerpt(repo / m['path'], mode)
            tokens = max(1, len(text) // 4)
            if tokens > remaining:
                out += [f"- {m['id']} — {m['path']} — kind: {m['kind']} (open when needed; budget)"]
            else:
                remaining -= tokens
                out += [f'<material id="{m["id"]}" matter="{m["matter"]}">', text.strip(), '</material>', '']
        out.append('')
    dst = repo / ".context" / "task.md"; dst.parent.mkdir(exist_ok=True); dst.write_text("\n".join(out))
    print(f"{dst}: {len(chosen)} elements, ~{sum(p['tokens'] for p in chosen)} tokens" + (f", {len(skipped)} dropped by budget" if skipped else ""))

if __name__ == "__main__":
    try:
        main()
    except ValueError as ex:
        sys.exit(f'Cannot compile context: {ex}')
