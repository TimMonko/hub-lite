"""Render every plugin page and the home page into _build_proto/, index them, and measure.

A prototype for the stack decision (napari-plans: "Which stack builds the
hub's plugin pages"). It reads the data today's build fetched
(_build/data/plugin_page_data.json), so run `pixi run fetch-data` first.

    pixi run python prototype/build.py

Order matters: plugin pages, then the Pagefind index of them, then the home
page, whose cards carry each plugin's Pagefind result id.
"""

import asyncio
import gzip
import json
import shutil
import statistics
import time
from collections import Counter
from importlib.resources import files
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined
from napari_resources import logo_path, special_logo_path
from page_model import PluginPage, PluginPageData, page_from_data
from pagefind.index import IndexConfig, PagefindIndex

HERE = Path(__file__).parent
ROOT = HERE.parent
DATA = ROOT / "_build" / "data" / "plugin_page_data.json"
OUT = ROOT / "_build_proto"
# napari-sphinx-theme's brand files: colours, code colours, icons. The
# package is installed without Sphinx (pyproject's dependency-overrides).
BRAND = Path(str(files("napari_sphinx_theme") / "static" / "brand"))


# --- File formats ---------------------------------------------------------


def read_formats(patterns: list[str]) -> list[str]:
    """Reader filename patterns as file extensions: "*.TIF" -> ".tif".

    Patterns that name no extension are left out: "*" (the reader is offered
    every file and decides itself), "*omero*", "s3://*", directory names.
    """
    formats = set()
    for pattern in patterns:
        ext = pattern.strip().lower().lstrip("*").rstrip("*")
        if ext.startswith(".") and len(ext) > 1 and not set("*/:?[") & set(ext):
            formats.add(ext)
    return sorted(formats)


def written_formats(extensions: list[str]) -> list[str]:
    """Writer extensions, lower case, each with its dot: "TIF" -> ".tif"."""
    return sorted(
        {"." + ext.strip().lower().lstrip(".") for ext in extensions if ext.strip(". ")}
    )


# --- Search -----------------------------------------------------------------


async def index_site() -> None:
    """Index the plugin pages with Pagefind (its Python API; same as `pagefind --site`)."""
    config = IndexConfig(output_path=str(OUT / "pagefind"))
    async with PagefindIndex(config) as index:
        await index.add_directory(str(OUT))


def pagefind_ids() -> dict[str, str]:
    """Plugin name -> the id Pagefind's search gives that plugin's page.

    A search result's id names the page's fragment file
    (pagefind/fragment/<id>.pf_fragment), which holds the page's URL. With
    the id on each card, home.js maps results to cards without fetching
    each result's data. This reads Pagefind's output format, which Pagefind
    doesn't document, so main() fails the build if any plugin has no id.
    """
    ids = {}
    for path in (OUT / "pagefind" / "fragment").glob("*.pf_fragment"):
        data = gzip.decompress(path.read_bytes()).removeprefix(b"pagefind_dcd")
        url = json.loads(data)["url"]
        ids[url.rsplit("/", 1)[-1].removesuffix(".html")] = path.stem
    return ids


# --- Pages ------------------------------------------------------------------


def home_cards(pages: list[PluginPage], ids: dict[str, str]) -> list[dict]:
    """What the home page needs per plugin, most recently updated first.

    That is home.js's default sort, so the order is the same with or
    without JavaScript.
    """
    missing = sorted(page.name for page in pages if page.name not in ids)
    if missing:
        raise SystemExit(
            f"No Pagefind id for {len(missing)} plugins (format change?): {missing[:5]}"
        )
    cards = [
        {
            "page": page,
            "pagefind_id": ids[page.name],
            "reads": read_formats(page.reads),
            "writes": written_formats(page.writes),
        }
        for page in pages
    ]
    cards.sort(key=lambda card: card["page"].release_date or "", reverse=True)
    return cards


def main():
    start = time.perf_counter()
    env = Environment(
        # The theme's brand folder too, so templates can include
        # "icons/github.svg", and napari-resources' hand-made logos, for
        # "silhouette-current-color.svg".
        loader=FileSystemLoader(
            [
                HERE / "templates",
                BRAND,
                special_logo_path("silhouette-current-color").parent,
            ]
        ),
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
    # napari's shared colours and code colours, from napari-sphinx-theme.
    for name in ("napari-tokens.css", "pygments.css"):
        shutil.copy(BRAND / name, OUT / "static" / "css")
    (OUT / "static" / "js").mkdir(parents=True)
    for name in ("home.js", "theme.js"):
        shutil.copy(HERE / "static" / name, OUT / "static" / "js" / name)
    # napari's logos from napari-resources, as napari itself uses them: the
    # header's, light and dark (the dark one's gold border shows on the dark
    # navbar), and the favicon, which follows the system's colour scheme.
    images = OUT / "static" / "images"
    shutil.copy(logo_path("gradient", "plain", "light"), images / "napari-light.svg")
    shutil.copy(logo_path("gradient", "plain", "dark"), images / "napari-dark.svg")
    shutil.copy(
        special_logo_path("silhouette-theme-aware"), images / "napari-favicon.svg"
    )

    sizes = []
    pages = []
    for plugin in plugins:
        page = page_from_data(plugin)
        html = template.render(page=page, root="../")
        (OUT / "plugins" / f"{page.name}.html").write_text(html, encoding="utf-8")
        sizes.append(len(html.encode()))
        pages.append(page)

    asyncio.run(index_site())

    cards = home_cards(pages, pagefind_ids())
    formats = Counter(f for card in cards for f in {*card["reads"], *card["writes"]})
    pythons = sorted(
        {v for page in pages for v in page.python_versions},
        key=lambda v: tuple(int(part) for part in v.split(".")),
        reverse=True,
    )
    home = env.get_template("index.html").render(
        cards=cards,
        formats=[
            f for f, _ in formats.most_common()
        ],  # commonest first, for the suggestions
        python_versions=pythons,
        root="",
    )
    (OUT / "index.html").write_text(home, encoding="utf-8")

    elapsed = time.perf_counter() - start
    sizes.sort()
    css = sum(p.stat().st_size for p in (OUT / "static" / "css").iterdir())
    print(f"{len(sizes)} plugin pages, indexed, in {elapsed:.1f} s")
    print(
        f"page HTML: median {statistics.median(sizes) / 1024:.1f} KB, "
        f"p90 {sizes[int(len(sizes) * 0.9)] / 1024:.1f} KB, "
        f"max {sizes[-1] / 1024:.1f} KB"
    )
    print(f"CSS per page (cached after the first): {css / 1024:.1f} KB")
    print(
        f"home page: {len(home.encode()) / 1024:.1f} KB HTML "
        f"({len(gzip.compress(home.encode())) / 1024:.0f} KB gzipped) for {len(cards)} plugins, "
        f"{len(formats)} file formats"
    )


if __name__ == "__main__":
    main()
