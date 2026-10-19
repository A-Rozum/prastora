"""House typography (norms/typography.md): the dash is U+2013 (–). Rewrites U+2014 and U+2015 in text files;
a long dash written between two words without spaces gets spaces (word – word); between digits it stays closed (2026–2027).

Quoted and source material keeps its own characters:
- quotations in typographic marks «…», “…”, „…“ (within one paragraph) and block quotations (lines starting with >);
- code: fenced blocks (``` or ~~~) and inline `code`;
- files matching a glob listed under `verbatim:` in typography.yaml at the repository root.
A project whose owner chose another dash has `dash: em` in typography.yaml; its files stay as they are.

    python plyn_typography.py <repo> [paths…]   default: files staged in <repo> (git diff --cached)
Exit code 0; prints the files it changed. Applied at every commit by the hook that A-Rozum/plyn tools/setup.sh
installs, and on every landing by plyn_land.py and workflows/land.yml."""
import fnmatch, pathlib, re, subprocess, sys

LONG = "\u2014\u2015"
BETWEEN = re.compile(r"(?<=[^\W\d])[" + LONG + r"](?=[^\W\d])")  # between letters; digits keep a closed range (2026–2027)
ANY = re.compile("[" + LONG + "]")
PARA = r"(?:(?!\n[ \t]*\n)[^{close}])*"  # within one paragraph
KEEP = re.compile("|".join([
    r"^[ \t]*(```|~~~)[^\n]*\n.*?^[ \t]*\1[^\n]*$",   # fenced code block
    r"`[^`\n]+`",                                      # inline code
    r"^[ \t]*>[^\n]*$",                                # block quotation line
    "«" + PARA.format(close="»") + "»",
    "„" + PARA.format(close="“”") + "[“”]",
    "“" + PARA.format(close="”") + "”",
]), re.M | re.S)

def house(text):
    """Set the house dash outside quoted and code spans."""
    out, last = [], 0
    for m in KEEP.finditer(text):
        out.append(_dash(text[last:m.start()])); out.append(m.group(0)); last = m.end()
    out.append(_dash(text[last:]))
    return "".join(out)

def _dash(s):
    return ANY.sub("\u2013", BETWEEN.sub(" \u2013 ", s))

def settings(repo):
    f = pathlib.Path(repo) / "typography.yaml"
    text = f.read_text(encoding="utf-8") if f.exists() else ""
    em = re.search(r"^\s*dash:\s*em\b", text, re.M) is not None
    verbatim, inside = [], False
    for line in text.splitlines():
        if re.match(r"^verbatim:\s*$", line): inside = True; continue
        m = re.match(r"^verbatim:\s*\[(.*)\]\s*$", line)
        if m: verbatim += [g.strip().strip("'\"") for g in m.group(1).split(",") if g.strip()]; continue
        if inside:
            m = re.match(r"^\s*-\s*(.+?)\s*$", line)
            if m: verbatim.append(m.group(1).strip("'\"")); continue
            if line.strip() and not line.startswith((" ", "\t")): inside = False
    return em, verbatim

def opted_out(repo):
    return settings(repo)[0]

def staged(repo):
    out = subprocess.run(["git", "diff", "--cached", "--name-only", "--diff-filter=AM"], cwd=repo, capture_output=True, text=True).stdout
    return [p for p in out.splitlines() if p]

def apply(repo, paths=None):
    repo = pathlib.Path(repo)
    em, verbatim = settings(repo)
    if em: return []
    if paths is None: paths = staged(repo)
    changed = []
    for rel in paths:
        if any(fnmatch.fnmatch(rel, g) or fnmatch.fnmatch(rel, g.rstrip("/") + "/*") for g in verbatim): continue
        p = repo / rel
        try: text = p.read_bytes().decode("utf-8")
        except (OSError, UnicodeDecodeError): continue
        new = house(text)
        if new != text:
            p.write_bytes(new.encode("utf-8")); changed.append(rel)
    return changed

if __name__ == "__main__":
    repo = sys.argv[1] if len(sys.argv) > 1 else "."
    changed = apply(repo, sys.argv[2:] or None)
    if changed: print("House dash set in: " + ", ".join(changed))
