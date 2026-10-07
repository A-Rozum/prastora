"""Select elements applicable to a task (first part of the context assembler).
Usage: python tools/select.py [repo_dir] domain=legal.interpol task_kind=drafting [budget=8000]
Output: applicable elements, most specific first, with token estimates; if nothing matches beyond always-elements,
says so — the fallback is search with lowered trust, marked "not anticipated"."""
import sys, pathlib, yaml
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from facets import evaluate

def main():
    args = sys.argv[1:]
    repo = pathlib.Path(args[0]) if args and "=" not in args[0] else pathlib.Path(".")
    task = {}
    for a in args:
        if "=" in a:
            k, v = a.split("=", 1); task[k] = v.split(",") if "," in v else v
    budget = int(task.pop("budget", 10**9))
    elements = yaml.safe_load((repo / "elements.yaml").read_text()) or []
    picked = []
    for e in elements:
        if e.get("status") in ("deprecated", "removed"): continue
        m, spec = evaluate(e["applies"], task)
        if m:
            p = repo / e["path"]
            load = e.get("load") or ("reference" if e["id"].split(":")[0] in ("tool", "check", "trigger") else "content")
            text = p.read_text(errors="ignore") if p.is_file() else ""
            if load == "head":
                text = text[: text.find("*/") + 2] if "*/" in text[:4000] else "\n".join(text.splitlines()[:40])
            tokens = 20 if load == "reference" else (e.get("tokens") or len(text) // 4)
            picked.append((spec, e["id"], e["path"] + ("" if load == "content" else f" [{load}]"), tokens, "always" in e["applies"]))
    picked.sort(key=lambda x: (-x[0], x[1]))
    total, out = 0, []
    for spec, i, path, tok, always in picked:
        if total + tok > budget and not always:
            print(f"skip (budget) {i}"); continue
        total += tok; out.append((spec, i, path, tok))
    for spec, i, path, tok in out:
        print(f"{spec:>2}  {i:<40} {path}  ~{tok} tok")
    print(f"total ~{total} tokens, {len(out)} elements")
    if all(any(p[1] == i and p[4] for p in picked) for _, i, _, _ in out):
        print("no normative match beyond always-elements: fallback = search with lowered trust, mark as 'not anticipated'")

if __name__ == "__main__":
    main()
