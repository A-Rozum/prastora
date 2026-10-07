"""Validate a repository against the system formats: system.yaml, elements.yaml, state.yaml (if present).
Usage: python tools/pn_validate.py [repo_dir] [--formats DIR]. Exit 0 = valid. First executable part of the kernel."""
import sys, json, pathlib, re, yaml
from jsonschema import Draft202012Validator

def _plain(x):
    """YAML turns 2026-10-07 into a date object; schemas expect ISO strings."""
    import datetime
    if isinstance(x, (datetime.date, datetime.datetime)):
        return x.isoformat()
    if isinstance(x, dict):
        return {k: _plain(v) for k, v in x.items()}
    if isinstance(x, list):
        return [_plain(v) for v in x]
    return x

def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    repo = pathlib.Path(args[0] if args else ".").resolve()
    fdir = pathlib.Path(sys.argv[sys.argv.index("--formats") + 1]) if "--formats" in sys.argv else pathlib.Path(__file__).resolve().parent.parent / "formats"
    errors, warnings = [], []
    def check(file, schema):
        p = repo / file
        if not p.exists():
            return None
        data = _plain(yaml.safe_load(p.read_text())) or ([] if file in ("elements.yaml", "lab.yaml") else {})
        v = Draft202012Validator(json.loads((fdir / schema).read_text()))
        for e in v.iter_errors(data):
            errors.append(f"{file}: {'/'.join(map(str, e.path)) or '(root)'}: {e.message}")
        return data
    manifest = check("system.yaml", "manifest.schema.json")
    if manifest is None:
        errors.append("system.yaml: missing")
    elements = check("elements.yaml", "elements.schema.json") or []
    check("state.yaml", "state.schema.json")
    from pn_inputs import inventory
    try:
        matters, materials = inventory(repo, elements, fdir, require_files=True)
        st = _plain(yaml.safe_load((repo / 'state.yaml').read_text())) if (repo / 'state.yaml').exists() else {}
        for t in st.get('tasks', []):
            if t.get('matter') is not None and t['matter'] not in {m['id'] for m in matters}:
                errors.append(f"state.yaml: {t['id']}: unknown matter")
    except (ValueError, TypeError, KeyError) as ex:
        errors.append(str(ex))
    lab = check("lab.yaml", "lab.schema.json") or []
    import datetime
    today = datetime.date.today().isoformat()
    for e in lab if isinstance(lab, list) else []:
        if isinstance(e, dict):
            if e.get("path") and not (repo / e["path"]).exists():
                errors.append(f"lab.yaml: {e.get('id')}: path not found: {e['path']}")
            if str(e.get("review_by", "9999")) < today:
                (errors if "--strict" in sys.argv else warnings).append(f"lab.yaml: {e.get('id')}: review_by {e.get('review_by')} has passed — promote, decide or delete")
    ids = [e.get("id", "") for e in elements if isinstance(e, dict)]
    bare = [re.sub(r"@.*$", "", i) for i in ids]
    for i in {x for x in bare if bare.count(x) > 1}:
        errors.append(f"elements.yaml: duplicate id {i}")
    for e in elements:
        if isinstance(e, dict) and e.get("path") and not (repo / e["path"]).exists():
            errors.append(f"elements.yaml: {e.get('id')}: path not found: {e['path']}")
    known = set(bare)
    vocab_file = fdir.parent / "vocabulary" / "facets.yaml"
    if vocab_file.exists():
        sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
        from pn_facets import conds
        vocab = yaml.safe_load(vocab_file.read_text())
        for e in elements:
            if not isinstance(e, dict) or not isinstance(e.get("applies"), dict):
                continue
            try:
                for f, v in conds(e["applies"]):
                    if f not in vocab:
                        errors.append(f"elements.yaml: {e.get('id')}: unknown facet '{f}'")
                    elif vocab[f].get("closed") and v not in vocab[f].get("values", []):
                        errors.append(f"elements.yaml: {e.get('id')}: '{v}' is not a value of facet '{f}'")
            except Exception as ex:
                errors.append(f"elements.yaml: {e.get('id')}: malformed applies ({ex})")
    for e in elements:
        for r in (e.get("relations") or []) if isinstance(e, dict) else []:
            if r.get("to") and re.sub(r"@.*$", "", r["to"]) not in known and ":" in r["to"] and r["to"].split(":")[0] in ("tool", "norm", "method", "check", "template"):
                errors.append(f"elements.yaml: {e.get('id')}: relation to unknown element {r['to']}")
    if manifest and isinstance(manifest, dict):
        for pid in manifest.get("provides", []):
            if pid not in known:
                errors.append(f"system.yaml: provides {pid}, not in elements.yaml")
    for w in warnings:
        print("WARN ", w)
    for e in errors:
        print("ERROR", e)
    print(f"{repo.name}: {len(elements)} elements, {len(errors)} errors")
    sys.exit(1 if errors else 0)

if __name__ == "__main__":
    main()
