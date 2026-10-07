"""Select elements applicable to a task (first part of the context assembler).
Usage: python tools/pn_select.py [repo_dir] domain=legal.interpol task_kind=drafting [subject=...] [budget=8000]"""
import sys, pathlib, yaml
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from pn_facets import evaluate, conds
from pn_inputs import read, inventory, allowed_matters, in_scope

def parse(args):
    repo = pathlib.Path(args[0]) if args and "=" not in args[0] else pathlib.Path(".")
    task = {}
    for a in args:
        if "=" in a:
            k, v = a.split("=", 1); task[k] = v.split(",") if "," in v else v
    budget = int(task.pop("budget", 10**9)); target = task.pop("target", "bundle")
    return repo, task, budget, target

def load_mode(e):
    kind = e["id"].split(":")[0]
    return e.get("load") or ("reference" if kind in ("tool", "check", "trigger") else "demand" if kind == "reference" else "content")

def excerpt(path, mode):
    text = path.read_text(errors="ignore") if path.is_file() else ""
    if mode == "head":
        return text[: text.find("*/") + 2] if "*/" in text[:4000] else "\n".join(text.splitlines()[:40])
    if mode in ("reference", "demand"):
        first = next((l.strip(' "#/*') for l in text.splitlines() if l.strip(' "#/*')), "")
        return first[:200]
    return text

# Instructions before material: a kernel is never dropped; norms, conventions, methods and roles come before
# templates, concepts and references. Within a tier, more specific first. (Found in ccf: by specificity alone,
# large references pushed out the legal kernel and the methods under a tight budget.)
TIER = {"core": 0, "norm": 1, "convention": 2, "method": 3, "role": 3, "task-type": 3, "quality-model": 4, "template": 4,
        "concept": 5, "component": 5, "metric": 5, "package": 5, "benchmark-task": 5, "reference": 6, "example": 7}

RANK = {'public': 0, 'internal': 1, 'confidential': 2, 'client': 3}

def package_elements(repo):
    """Elements of packages copied into this repository (manifest packages with a path holding elements.yaml).
    Paths are made relative to the repository; a project's own element with the same id overrides the package's;
    a package element whose access exceeds the repository's class is refused."""
    man = read(repo, 'system.yaml') or {}
    limit = RANK.get(man.get('access'), 3)
    out = []
    for p in man.get('packages', []):
        base = p.get('path')
        if not base or not (repo / base / 'elements.yaml').is_file():
            continue
        for e in read(repo / base, 'elements.yaml') or []:
            if RANK.get(e.get('access'), 3) > limit:
                raise ValueError(f"{p['id']}: {e['id']}: access exceeds repository class")
            if e['id'].split(':')[0] == 'core' and e['path'] == 'AGENTS.md':
                continue   # a package's repository kernel addresses work on that package, not work that uses it
            out.append({**e, 'path': f"{base}/{e['path']}", 'package': p['id']})
    return out

def all_elements(repo):
    own = read(repo, 'elements.yaml') or []
    ids = {e['id'].split('@')[0] for e in own}
    return own + [e for e in package_elements(repo) if e['id'].split('@')[0] not in ids]

def eligible(repo, task):
    elements = read(repo, 'elements.yaml')
    matters, _ = inventory(repo, elements)
    allowed = allowed_matters(matters, task)
    return [e for e in all_elements(repo) if e.get('status') not in ('deprecated', 'removed')
            and in_scope(e, allowed) and evaluate(e['applies'], task)[0]]

def select(repo, task, budget=10**9):
    """Return (chosen, skipped, normative_match). chosen: list of dicts with id, path, mode, spec, tokens, text."""
    picked = []
    for e in eligible(repo, task):
        m, spec = evaluate(e["applies"], task)
        if not m: continue
        mode = load_mode(e); text = excerpt(repo / e["path"], mode)
        tokens = 20 if mode in ("reference", "demand") else (e.get("tokens") or len(text) // 4)
        kind = e["id"].split(":")[0]
        asked = task.get("subject"); asked = asked if isinstance(asked, list) else ([asked] if asked else [])
        if any(f == "subject" and v in asked for f, v in conds(e["applies"])):
            spec += 10   # explicitly requested by the task's subject: first within its tier
        picked.append({"id": e["id"], "path": e["path"], "mode": mode, "spec": spec, "tokens": tokens, "text": text,
                       "always": "always" in e["applies"] or kind == "core", "tier": TIER.get(kind, 6)})
    picked.sort(key=lambda x: (x["tier"], -x["spec"], x["id"]))
    chosen, skipped, total = [], [], 0
    for p in picked:
        if total + p["tokens"] > budget and not p["always"]:
            skipped.append(p); continue
        total += p["tokens"]; chosen.append(p)
    return chosen, skipped, any(not p["always"] for p in chosen)

def main():
    repo, task, budget, _ = parse(sys.argv[1:])
    chosen, skipped, normative = select(repo, task, budget)
    for p in skipped: print(f"skip (budget) {p['id']}")
    for p in chosen: print(f"{p['spec']:>2}  {p['id']:<40} {p['path']}{'' if p['mode']=='content' else ' ['+p['mode']+']'}  ~{p['tokens']} tok")
    print(f"total ~{sum(p['tokens'] for p in chosen)} tokens, {len(chosen)} elements")
    if not normative:
        print("no normative match beyond always-elements: fallback = search with lowered trust, mark as 'not anticipated'")

if __name__ == "__main__":
    main()
