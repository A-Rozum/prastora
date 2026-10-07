"""Compile the context for one task into .context/task.md — a vendor-neutral bundle any agent environment can read
(Claude Code via CLAUDE.md → AGENTS.md, Codex and OpenCode via AGENTS.md, a chat by uploading the file).
Usage: python tools/compile.py [repo_dir] domain=… task_kind=… [subject=…] [budget=…]
The bundle holds: task facets, open tasks from state.yaml, selected elements most specific first (content or head),
tools by reference, elements dropped by budget, and the fallback note if nothing normative matched."""
import sys, pathlib, datetime, yaml
import importlib.util
_spec = importlib.util.spec_from_file_location("ctx_select", pathlib.Path(__file__).resolve().parent / "select.py")
_sel = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(_sel)   # local select.py, not the stdlib module
parse, select = _sel.parse, _sel.select

def main():
    repo, task, budget, _ = parse(sys.argv[1:])
    chosen, skipped, normative = select(repo, task, budget)
    out = [f"# Context for the current task", "",
           f"Compiled {datetime.datetime.now(datetime.timezone.utc):%Y-%m-%d %H:%M} UTC by tools/compile.py. Facets: " +
           ", ".join(f"{k}={v}" for k, v in task.items()) + ".",
           "Read this file instead of browsing the repository. More specific elements come first and override general ones; the kernel's invariants are never overridden.", ""]
    st = repo / "state.yaml"
    if st.exists():
        s = yaml.safe_load(st.read_text()) or {}
        out += ["## Open tasks (state.yaml)", ""]
        for t in s.get("tasks", []):
            out.append(f"- [{t['status']}] {t['id']}: {t['title']} — done when: {t['done_when']} (executor: {t['executor']})")
        out.append("")
    if not normative:
        out += ["## Not anticipated", "", "No element applies beyond the kernel. Work from general knowledge and search with lowered trust; say in the result that the task was not anticipated, so the gap can be filled.", ""]
    refs = [p for p in chosen if p["mode"] == "reference"]
    for p in [p for p in chosen if p["mode"] != "reference"]:
        out += [f'<element id="{p["id"]}" path="{p["path"]}"' + (' load="head"' if p["mode"] == "head" else "") + ">", p["text"].strip(), "</element>", ""]
    if refs:
        out += ["## Tools and checks (run, do not read)", ""] + [f"- {p['path']} — {p['text']}" for p in refs] + [""]
    if skipped:
        out += ["## Dropped by budget (open only if the task requires)", ""] + [f"- {p['id']} — {p['path']}" for p in skipped] + [""]
    dst = repo / ".context" / "task.md"; dst.parent.mkdir(exist_ok=True); dst.write_text("\n".join(out))
    print(f"{dst}: {len(chosen)} elements, ~{sum(p['tokens'] for p in chosen)} tokens" + (f", {len(skipped)} dropped by budget" if skipped else ""))

if __name__ == "__main__":
    main()
