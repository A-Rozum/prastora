"""Static checks for Prastora. No dependencies: python3 check.py"""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit, unquote
import xml.etree.ElementTree as ET
import re

ROOT = Path(__file__).resolve().parent
LAYERS = {"core.css": "core", "themes": "theme", "components": "components", "pages": "page", "dev": "dev"}
ORDER = ["core", "theme", "components", "page", "dev"]


class Page(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.ids, self.duplicates, self.refs, self.styles, self.scripts = set(), [], [], [], []
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if attrs.get("id"):
            (self.duplicates if attrs["id"] in self.ids else []).append(attrs["id"])
            self.ids.add(attrs["id"])
        for key in ("href", "src", "action"):
            if attrs.get(key):
                self.refs.append(attrs[key])
        if tag == "link" and attrs.get("rel") == "stylesheet":
            self.styles.append(attrs.get("href", ""))
        if tag == "script" and attrs.get("src"):
            self.scripts.append(attrs["src"])


def layer_of(path):
    rel = path.relative_to(ROOT / "css").parts
    return LAYERS.get(rel[0])


def check_css(errors):
    for path in sorted((ROOT / "css").rglob("*.css")):
        name = path.relative_to(ROOT).as_posix()
        css = re.sub(r"/\*.*?\*/", "", path.read_text(encoding="utf-8"), flags=re.S)
        layer = layer_of(path)
        if layer is None:
            errors.append(f"{name}: not in a known layer folder")
            continue
        body = re.sub(r"^\s*@layer [\w\s,]+;", "", css) if layer == "core" else css
        if not re.match(rf"\s*@layer {layer}\s*\{{", body) or body.count("@layer") != 1:
            errors.append(f"{name}: must be wrapped in a single @layer {layer} block")
        if "@import" in css:
            errors.append(f"{name}: @import is not used; link files from the page")
        if re.search(r"\d(?:\.\d+)?px\b", css, flags=re.I):
            errors.append(f"{name}: px dimension (use rem; em in media queries)")
        if layer in ("components", "page", "dev") and re.search(r"#[0-9a-f]{3,8}\b|\brgba?\(|\bhsla?\(", css, flags=re.I):
            errors.append(f"{name}: literal colour; use theme custom properties")
        if layer == "theme":
            for decl in re.findall(r"[{;]\s*([\w-]+)\s*:", css):
                if not decl.startswith("--") and decl != "color-scheme":
                    errors.append(f"{name}: themes set custom properties only (found {decl})")


def check_pages(errors):
    pages = {p: Page(p.read_text(encoding="utf-8")) for p in sorted(ROOT.glob("*.html"))}
    for path, page in pages.items():
        name = path.name
        errors += [f"{name}: duplicate id {i}" for i in page.duplicates]
        for src in page.scripts + page.styles:
            if urlsplit(src).scheme or urlsplit(src).netloc:
                errors.append(f"{name}: external script or stylesheet {src}")
        layers = [layer_of(ROOT / urlsplit(s).path) for s in page.styles if urlsplit(s).path.startswith("css/")]
        if not layers or layers[0] != "core" or "theme" not in layers:
            errors.append(f"{name}: link css/core.css first, then a theme")
        if [ORDER.index(l) for l in layers if l] != sorted(ORDER.index(l) for l in layers if l):
            errors.append(f"{name}: stylesheets out of layer order")
        for ref in page.refs:
            url = urlsplit(ref)
            if url.scheme or url.netloc:
                continue
            target = path.parent / unquote(url.path) if url.path else path
            if not target.is_file():
                errors.append(f"{name}: missing target {ref}")
            elif url.fragment and target.suffix == ".html":
                ids = pages[target].ids if target in pages else Page(target.read_text(encoding="utf-8")).ids
                if unquote(url.fragment) not in ids:
                    errors.append(f"{name}: missing fragment {ref}")
            elif url.fragment and target.suffix == ".svg":
                if unquote(url.fragment) not in {e.get("id") for e in ET.parse(target).iter()}:
                    errors.append(f"{name}: missing fragment {ref}")
    return pages


def main():
    errors = []
    check_css(errors)
    pages = check_pages(errors)
    print(*errors, sep="\n") if errors else None
    print(f"Pages: {len(pages)}; errors: {len(errors)}")
    raise SystemExit(bool(errors))


if __name__ == "__main__":
    main()
