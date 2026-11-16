"""Render every plugin page with Jinja into _build_proto/ and measure it.

A prototype for the stack decision (napari-plans: "Which stack builds the
hub's plugin pages"). It reads the data today's build fetched
(_build/data/plugin_page_data.json), so run `pixi run fetch-data` first.

    pixi run python prototype/build.py
"""

import json
import re
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


def write_icon_sprite(path: Path):
    """Combine icons/*.svg into one sprite of <symbol>s, one per file name.

    Pages draw an icon with <use href=".../icons.svg#github">, so the icons
    download once and are cached, instead of adding ~11 KB to every page.
    Each icon is filled with currentColor, so it takes the text colour.
    """
    symbols = []
    for icon in sorted((HERE / "icons").glob("*.svg")):
        svg = icon.read_text("utf-8")
        match = re.search(r'viewBox="([^"]+)"', svg)
        if not match:
            raise ValueError(f"{icon} has no viewBox")
        view_box = match[1]
        inner = svg[svg.index(">") + 1 : svg.rindex("</svg>")]
        symbols.append(
            f'<symbol id="{icon.stem}" viewBox="{view_box}">{inner}</symbol>'
        )
    path.write_text(
        '<svg xmlns="http://www.w3.org/2000/svg">' + "".join(symbols) + "</svg>\n",
        encoding="utf-8",
    )


def main():
    start = time.perf_counter()
    env = Environment(
        loader=FileSystemLoader(HERE / "templates"),
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
    shutil.copy(HERE / "static" / "pygments.css", OUT / "static" / "css")
    write_icon_sprite(OUT / "static" / "images" / "icons.svg")

    sizes = []
    for plugin in plugins:
        page = page_from_data(plugin)
        html = template.render(page=page, root="../")
        path = OUT / "plugins" / f"{page.name}.html"
        path.write_text(html, encoding="utf-8")
        sizes.append(len(html.encode()))

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


if __name__ == "__main__":
    main()
