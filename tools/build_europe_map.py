"""Optional asset generation: simplified public-domain Natural Earth geography.

Run from the project root with Python. No runtime dependencies or network map tiles.
Source: https://www.naturalearthdata.com/about/terms-of-use/
"""
import json
from pathlib import Path
from urllib.request import urlopen
from xml.sax.saxutils import escape

SOURCE = "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_110m_admin_0_countries.geojson"
COUNTRIES = {
    "Portugal", "Spain", "France", "Belgium", "Netherlands", "Luxembourg",
    "Germany", "Switzerland", "Austria", "Italy", "United Kingdom", "Ireland",
    "Denmark", "Norway", "Sweden", "Finland", "Poland", "Czechia", "Slovakia",
    "Hungary", "Slovenia", "Croatia", "Bosnia and Herzegovina", "Serbia",
    "Montenegro", "Kosovo", "Albania", "Macedonia", "North Macedonia", "Greece",
    "Bulgaria", "Romania", "Moldova", "Ukraine", "Belarus", "Lithuania",
    "Latvia", "Estonia", "Russia", "Turkey", "Cyprus", "Tunisia", "Algeria",
}


def project(point):
    lon, lat = point[:2]
    return (lon + 12) * 18, (62 - lat) * 24


def main():
    with urlopen(SOURCE, timeout=60) as response:
        features = json.load(response)["features"]
    paths = []
    for feature in features:
        name = feature["properties"]["ADMIN"]
        if name not in COUNTRIES:
            continue
        geometry = feature["geometry"]
        polygons = geometry["coordinates"] if geometry["type"] == "MultiPolygon" else [geometry["coordinates"]]
        for polygon in polygons:
            rings = []
            for ring in polygon:
                points = [project(point) for point in ring]
                if min(x for x, _ in points) > 900 or max(x for x, _ in points) < 0:
                    continue
                if min(y for _, y in points) > 700 or max(y for _, y in points) < 0:
                    continue
                rings.append("M" + "L".join(f"{x:.1f},{y:.1f}" for x, y in points) + "Z")
            if rings:
                paths.append(f'<path d="{"".join(rings)}"><title>{escape(name)}</title></path>')
    svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 700"><title>Europe – simplified geography</title><desc>Natural Earth 1:110m public-domain country outlines. Approximate projection; not a navigation map.</desc><g id="land" fill-rule="evenodd">' + "".join(paths) + '</g></svg>\n'
    destination = Path(__file__).resolve().parents[1] / "assets" / "europe-map.svg"
    destination.write_text(svg, encoding="utf-8")
    print(f"Generated {destination.name}: {len(paths)} paths, {destination.stat().st_size} bytes")


if __name__ == "__main__":
    main()
