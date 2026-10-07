"""Facet predicates: evaluation and specificity. Shared by validate.py and select.py."""
import pathlib, yaml

def load_vocab(root):
    return yaml.safe_load((pathlib.Path(root) / "vocabulary" / "facets.yaml").read_text())

def conds(pred):
    """Yield (facet, value) leaf conditions of a predicate."""
    if "always" in pred: return
    for k in ("all", "any"):
        if k in pred:
            for p in pred[k]: yield from conds(p)
            return
    if "not" in pred:
        yield from conds(pred["not"]); return
    (f, v), = pred.items()
    for x in (v if isinstance(v, list) else [v]):
        yield f, x

def _hit(task_values, want):
    return any(tv == want or tv.startswith(want + ".") for tv in task_values)

def evaluate(pred, task):
    """Return (matched, specificity). Specificity = sum of depths of matched positive conditions."""
    if "always" in pred: return True, 0
    if "all" in pred:
        rs = [evaluate(p, task) for p in pred["all"]]
        return all(m for m, _ in rs), sum(s for m, s in rs if m)
    if "any" in pred:
        rs = [evaluate(p, task) for p in pred["any"]]
        hits = [s for m, s in rs if m]
        return bool(hits), max(hits) if hits else 0
    if "not" in pred:
        m, _ = evaluate(pred["not"], task)
        return (not m), 0
    (f, v), = pred.items()
    tv = task.get(f); tv = tv if isinstance(tv, list) else ([tv] if tv else [])
    wants = v if isinstance(v, list) else [v]
    hits = [w for w in wants if (w in tv if f == 'matter' else _hit(tv, w))]
    return bool(hits), max((w.count(".") + 1 for w in hits), default=0)
