"""Identify contrastive negative definitions for human or agent review."""
import argparse
from pathlib import Path
import re

PATTERNS = (
    ("negative-definition", re.compile(r"\b(?:is|are|was|were)\s+not\b.{0,90}\b(?:but|rather)\b", re.I)),
    ("negative-enumeration", re.compile(r"\b(?:not|neither)\b.{0,80}\b(?:nor|not)\b", re.I)),
    ("russian-contrast", re.compile(r"\b(?:это|является)\s+не\b.{0,90}\bа\b", re.I)),
    ("russian-enumeration", re.compile(r"\bне\b.{0,80}\b(?:и не|ни)\b", re.I)),
)

def inspect(text):
    for number, line in enumerate(text.splitlines(), 1):
        if line.lstrip().startswith("    "):
            continue
        for name, pattern in PATTERNS:
            if pattern.search(line):
                yield number, name, line.strip()[:200]

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", type=Path)
    args = parser.parse_args()
    count = 0
    for path in args.paths:
        files = sorted(p for p in path.rglob("*") if p.suffix in (".md", ".txt")) if path.is_dir() else [path]
        for file in files:
            for line_no, kind, sample in inspect(file.read_text(encoding="utf-8")):
                print(f"{file}:{line_no}: {kind}: {sample}")
                count += 1
    print(f"{count} candidates; keep meaningful contrasts and operative exclusions.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
