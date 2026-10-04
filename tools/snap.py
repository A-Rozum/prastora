"""Visual regression check. Needs: pip install playwright pillow && playwright install chromium

  python3 tools/snap.py base [--css FILE ...] [--pages NAME ...] [--regimes mobile desktop wide] [--dark]
  (make changes)
  python3 tools/snap.py diff        # re-shoots the same set, prints only differences, exit 1 if any

--css picks the pages that link those files (paths from the repo root). --pages takes names like templates/pricing. Default: all pages, all regimes, light scheme.
One width per regime is enough: within a regime the layout only scales.
"""
import argparse, functools, shutil, http.server, json, re, sys, threading
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STORE = ROOT / ".snap"
REGIMES = {"mobile": 390, "desktop": 1440, "wide": 2560}
HIDE = ".load-reading,.viewport-reading output,iframe{visibility:hidden!important}"


def pages_for(css):
    names = []
    wanted = {(ROOT / c).resolve() for c in css}
    for page in sorted(ROOT.rglob("*.html")):
        rel = page.relative_to(ROOT)
        if {".git", ".snap", "tools"} & set(rel.parts):
            continue
        links = re.findall(r'<link rel="stylesheet" href="([^"]+)"', page.read_text(encoding="utf-8"))
        if not css or wanted & {(page.parent / l).resolve() for l in links}:
            names.append(rel.with_suffix("").as_posix())
    return names


def shoot(params, out):
    from playwright.sync_api import sync_playwright
    shutil.rmtree(out, ignore_errors=True)
    out.mkdir(parents=True, exist_ok=True)
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *args):
            pass
    handler = functools.partial(Quiet, directory=str(ROOT))
    server = http.server.ThreadingHTTPServer(("localhost", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base = f"http://localhost:{server.server_port}/"
    jobs = [(p, r, "light") for p in params["pages"] for r in params["regimes"]]
    if params["dark"] and params["pages"]:
        jobs += [(params["pages"][0], r, "dark") for r in params["regimes"]]
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        for page, regime, scheme in jobs:
            ctx = browser.new_context(viewport={"width": REGIMES[regime], "height": 900}, color_scheme=scheme)
            tab = ctx.new_page()
            tab.route("**/*", lambda r: r.continue_() if r.request.url.startswith(base) else r.abort())
            tab.goto(base + page + ".html")
            tab.add_style_tag(content=HIDE)
            tab.evaluate("document.querySelectorAll('img[loading=lazy]').forEach(i => i.loading = 'eager')")
            tab.wait_for_function("[...document.images].every(i => i.complete)")
            tab.wait_for_timeout(200)
            tab.screenshot(path=str(out / f"{page.replace('/', '~')}_{regime}_{scheme}.png"), full_page=True)
            ctx.close()
        browser.close()
    server.shutdown()
    return len(jobs)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("action", choices=["base", "diff"])
    ap.add_argument("--css", nargs="*", default=[])
    ap.add_argument("--pages", nargs="*")
    ap.add_argument("--regimes", nargs="*", default=list(REGIMES), choices=list(REGIMES))
    ap.add_argument("--dark", action="store_true")
    a = ap.parse_args()
    if a.action == "base":
        params = {"pages": a.pages or pages_for(a.css), "regimes": a.regimes, "dark": a.dark}
        STORE.mkdir(exist_ok=True)
        (STORE / "params.json").write_text(json.dumps(params))
        print(f"base: {shoot(params, STORE / 'base')} shots")
        return
    from PIL import Image, ImageChops
    params = json.loads((STORE / "params.json").read_text())
    shoot(params, STORE / "new")
    differ = []
    for old in sorted((STORE / "base").glob("*.png")):
        new = STORE / "new" / old.name
        a_img, b_img = Image.open(old).convert("RGB"), Image.open(new).convert("RGB")
        if a_img.size != b_img.size:
            differ.append(f"{old.name}: size {a_img.size} -> {b_img.size}")
        elif box := ImageChops.difference(a_img, b_img).getbbox():
            differ.append(f"{old.name}: changed in {box}; see .snap/new/{old.name}")
    print(*differ, sep="\n") if differ else print("no differences")
    sys.exit(bool(differ))


if __name__ == "__main__":
    main()
