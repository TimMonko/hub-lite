"""Render every plugin page with Jinja into _build_proto/ and measure it.

A prototype for the stack decision (napari-plans: "Which stack builds the
hub's plugin pages"). It reads the data today's build fetched
(_build/data/plugin_page_data.json), so run `pixi run fetch-data` first.

    pixi run python prototype/build.py
    pixi run python -m pagefind --site _build_proto   # the search index
"""

import json
import shutil
import statistics
import time
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined
from page_model import PluginPageData, page_from_data

HERE = Path(__file__).parent
ROOT = HERE.parent
DATA = ROOT / "_build" / "data" / "plugin_page_data.json"
OUT = ROOT / "_build_proto"


def main():
    start = time.perf_counter()
    env = Environment(
        # static/brand/ too, so templates can include "icons/github.svg".
        loader=FileSystemLoader([HERE / "templates", HERE / "static" / "brand"]),
        autoescape=True,
        undefined=StrictUndefined,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    template = env.get_template("plugin.html")
    plugins = [PluginPageData(**p) for p in json.loads(DATA.read_text("utf-8"))]

    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / "plugins").mkdir(parents=True)
    shutil.copytree(ROOT / "static" / "images", OUT / "static" / "images")
    (OUT / "static" / "css").mkdir(parents=True)
    shutil.copy(HERE / "static" / "hub.css", OUT / "static" / "css" / "hub.css")
    # napari's shared colours and code colours (update_brand.py).
    for name in ("napari-tokens.css", "pygments.css"):
        shutil.copy(HERE / "static" / "brand" / name, OUT / "static" / "css")

    (OUT / "static" / "js").mkdir(parents=True)
    shutil.copy(HERE / "static" / "home.js", OUT / "static" / "js" / "home.js")

    sizes = []
    pages = []
    for plugin in plugins:
        page = page_from_data(plugin)
        html = template.render(page=page, root="../")
        path = OUT / "plugins" / f"{page.name}.html"
        path.write_text(html, encoding="utf-8")
        sizes.append(len(html.encode()))
        pages.append(page)

    # The home page lists every plugin, most recently updated first (home.js's
    # default sort, so the order is the same with or without JavaScript).
    pages.sort(key=lambda page: page.release_date or "", reverse=True)
    home = env.get_template("index.html").render(pages=pages, root="")
    (OUT / "index.html").write_text(home, encoding="utf-8")

    elapsed = time.perf_counter() - start
    sizes.sort()
    css = sum(p.stat().st_size for p in (OUT / "static" / "css").iterdir())
    print(f"{len(sizes)} plugin pages in {elapsed:.1f} s")
    print(
        f"page HTML: median {statistics.median(sizes) / 1024:.1f} KB, "
        f"p90 {sizes[int(len(sizes) * 0.9)] / 1024:.1f} KB, "
        f"max {sizes[-1] / 1024:.1f} KB"
    )
    print(f"CSS per page (cached after the first): {css / 1024:.1f} KB")
    print(f"home page: {len(home.encode()) / 1024:.1f} KB HTML for {len(pages)} plugins")


if __name__ == "__main__":
    main()
