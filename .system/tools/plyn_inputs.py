"""Matter boundaries and required inputs. Shared by selection, compilation and validation.
Matter ids and material kinds are opaque: exact match, no hierarchy or transitive links."""
import json, pathlib, datetime, yaml
from jsonschema import Draft202012Validator

def _default_formats():
    """formats next to tools (vendored .system in a project), else the vendored standard of the tools repository."""
    base = pathlib.Path(__file__).resolve().parent.parent
    return base / "formats" if (base / "formats").is_dir() else base / ".system" / "formats"


def plain(value):
    if isinstance(value, (datetime.date, datetime.datetime)): return value.isoformat()
    if isinstance(value, dict): return {k: plain(v) for k, v in value.items()}
    if isinstance(value, list): return [plain(v) for v in value]
    return value

def read(repo, name):
    path = repo / name
    return plain(yaml.safe_load(path.read_text())) if path.exists() else []

def checked_path(repo, name):
    path = pathlib.Path(name)
    if path.is_absolute() or '..' in path.parts or not name:
        raise ValueError(f'unsafe material path: {name}')
    resolved = (repo / path).resolve()
    if not resolved.is_relative_to(repo.resolve()):
        raise ValueError(f'material path leaves repository: {name}')
    return resolved

def inventory(repo, elements, formats=None, require_files=False):
    """Validate boundaries before any element/material content is read; missing files may be inputs to request."""
    formats = formats or _default_formats()
    matters, materials = read(repo, 'matters.yaml'), read(repo, 'materials.yaml')
    for name, data, schema in [('matters.yaml', matters, 'matters.schema.json'),
                               ('materials.yaml', materials, 'materials.schema.json'),
                               ('elements.yaml', elements, 'elements.schema.json')]:
        errors = list(Draft202012Validator(json.loads((formats / schema).read_text())).iter_errors(plain(data)))
        if errors: raise ValueError(f'{name}: {errors[0].message}')
    ids = [m['id'] for m in matters]
    if len(set(ids)) != len(ids): raise ValueError('matters.yaml: duplicate matter id')
    known = set(ids)
    manifest = plain(yaml.safe_load((repo / 'system.yaml').read_text())) if (repo / 'system.yaml').exists() else {}
    ranks = {'public':0, 'internal':1, 'confidential':2, 'client':3}
    for m in materials:
        if ranks[m['access']] > ranks.get(manifest.get('access'), -1):
            raise ValueError(f"materials.yaml: {m['id']}: access exceeds repository class")
        if manifest.get('kind') == 'lab' and m['access'] == 'client':
            raise ValueError('materials.yaml: client material is not permitted in the lab')
    for m in matters:
        if any(link not in known or link == m['id'] for link in m.get('related', [])):
            raise ValueError(f"matters.yaml: {m['id']}: unknown or self-related matter")
    mids = [m['id'] for m in materials]
    if len(set(mids)) != len(mids): raise ValueError('materials.yaml: duplicate material id')
    owners = {}
    for item in [*elements, *materials]:
        matter = item.get('matter')
        if matter is not None and matter not in known:
            raise ValueError(f"{item['id']}: unknown matter {matter}")
        path = checked_path(repo, item['path'])
        if path in owners and owners[path] != matter:
            raise ValueError(f"{item['id']}: same file assigned to different scopes")
        owners[path] = matter
    if require_files:
        for m in materials:
            if not checked_path(repo, m['path']).is_file():
                raise ValueError(f"materials.yaml: {m['id']}: file not found: {m['path']}")
    return matters, materials

def allowed_matters(matters, task):
    matter = task.get('matter')
    if matter is None: return set()
    if not isinstance(matter, str) or matter not in {m['id'] for m in matters}:
        raise ValueError('task matter must name exactly one registered matter')
    current = next(m for m in matters if m['id'] == matter)
    return {matter, *current.get('related', [])}

def in_scope(item, allowed):
    return item.get('matter') is None or item['matter'] in allowed

def available_materials(repo, materials, allowed):
    return [m for m in materials if m['matter'] in allowed and checked_path(repo, m['path']).is_file()]

def missing_inputs(elements, materials):
    kinds = {m['kind'] for m in materials}
    return [(e['id'], kind) for e in elements for kind in e.get('requires_inputs', []) if kind not in kinds]
