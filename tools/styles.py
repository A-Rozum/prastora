#!/usr/bin/env python3
"""Optional, deterministic CSS bundles from a trusted site's delivery plan (no server work)."""
import argparse
import hashlib
import json
from pathlib import Path
import re


def generate(root, plan):
    root = Path(root).resolve()
    if plan.get('format') != 1 or not isinstance(plan.get('bundles'), dict):
        raise ValueError('Expected format 1 with named bundles.')
    result = {}
    for target, sources in plan['bundles'].items():
        if not isinstance(sources, list) or not sources or len(sources) != len(set(sources)):
            raise ValueError('Every bundle requires an ordered, nonempty, unique source list.')
        def local(url):
            if not isinstance(url, str) or not re.fullmatch(r'/[A-Za-z0-9_./-]+\.css', url) or '..' in url.split('/'):
                raise ValueError('Use canonical local CSS paths: '+str(url))
            path = (root / url.lstrip('/')).resolve()
            if not path.is_relative_to(root):
                raise ValueError('CSS paths must stay inside the declared asset root.')
            return path
        local(target)
        if target in sources:
            raise ValueError('A bundle cannot contain itself.')
        pieces, provenance = [], []
        for source in sources:
            raw = local(source).read_bytes()
            css = raw.decode('utf-8')
            # Bundles move files. Refuse dependencies that need a CSS parser to relocate.
            if re.search(r'@import\b', css, re.I) or re.search(r'url\((?![\s\"\']*(?:data:|https?:|/))', css, re.I):
                raise ValueError('Use root-relative CSS URLs and explicit source lists before bundling '+source)
            digest = hashlib.sha256(raw).hexdigest()
            provenance.append({'path': source, 'sha256': digest})
            pieces.append('/* '+source+' */\n'+css.rstrip()+'\n')
        output = '\n'.join(pieces).encode()
        result[target] = {'body': output, 'sources': provenance, 'sha256': hashlib.sha256(output).hexdigest()}
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('plan', type=Path)
    parser.add_argument('--root', required=True, type=Path)
    parser.add_argument('--check', action='store_true', help='Reject missing/stale generated bundles without writing.')
    args = parser.parse_args()
    bundles = generate(args.root, json.loads(args.plan.read_text()))
    # Validate every input before writing any output.
    for target, bundle in bundles.items():
        path = args.root / target.lstrip('/')
        if args.check:
            if not path.is_file() or path.read_bytes() != bundle['body']:
                raise SystemExit('Stale or missing CSS bundle: '+target)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(bundle['body'])
    print(json.dumps({path: {k: v for k, v in info.items() if k != 'body'} for path, info in bundles.items()}, indent=2))


if __name__ == '__main__':
    main()
