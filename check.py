"""Optional local checks; no dependencies and no browser JavaScript."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit, unquote
import xml.etree.ElementTree as ET


class Page(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.ids = set()
        self.refs = []
        self.duplicates = []
        self.scripts = 0
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        identifier = attrs.get("id")
        if identifier:
            if identifier in self.ids:
                self.duplicates.append(identifier)
            self.ids.add(identifier)
        for key in ("href", "src", "action"):
            if attrs.get(key):
                self.refs.append(attrs[key])
        self.scripts += tag == "script"


def main():
    root = Path(__file__).resolve().parent
    pages = {path: Page(path.read_text(encoding="utf-8")) for path in root.glob("*.html")}
    errors = []
    for path, page in pages.items():
        errors.extend(f"{path.name}: duplicate id {item}" for item in page.duplicates)
        if page.scripts:
            errors.append(f"{path.name}: unexpected browser script")
        for ref in page.refs:
            url = urlsplit(ref)
            if url.scheme or url.netloc:
                continue
            target = path.parent / unquote(url.path) if url.path else path
            if not target.is_file():
                errors.append(f"{path.name}: missing target {ref}")
                continue
            if url.fragment and target.suffix in (".html", ".svg"):
                if target.suffix == ".html":
                    ids = pages[target].ids if target in pages else Page(target.read_text(encoding="utf-8")).ids
                else:
                    ids = {element.get("id") for element in ET.parse(target).iter()}
                if unquote(url.fragment) not in ids:
                    errors.append(f"{path.name}: missing fragment {ref}")
    for error in errors:
        print(error)
    assets = list((root / "assets").glob("*"))
    print(f"Pages: {len(pages)}; errors: {len(errors)}; HTML/CSS/SVG total: {sum(p.stat().st_size for p in [*pages, *assets])} bytes")
    raise SystemExit(bool(errors))


if __name__ == "__main__":
    main()
