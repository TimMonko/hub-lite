"""Copy napari's brand files (colours, code colours, icons) into static/brand/.

They come from napari-sphinx-theme's brand folder, the one copy napari.org
and the other napari sites share. The copy is committed, so the build and a
visitor's first load need neither the theme nor a CDN. Run this to move to a
new theme release:

    pixi run python prototype/update_brand.py v1.2.0
    pixi run python prototype/update_brand.py ../napari-sphinx-theme   # a checkout

A tag is fetched from jsDelivr's GitHub endpoint. static/brand/SOURCE records
where the files came from.
"""

import shutil
import sys
import urllib.request
from pathlib import Path

OUT = Path(__file__).parent / "static" / "brand"
BRAND_PATH = "napari_sphinx_theme/static/brand"
CDN = "https://cdn.jsdelivr.net/gh/napari/napari-sphinx-theme@{tag}/" + BRAND_PATH
FILES = [
    "napari-tokens.css",
    "pygments.css",
    "icons/github.svg",
    "icons/image-sc.svg",
    "icons/mastodon.svg",
    "icons/napari.svg",
    "icons/napari-hub.svg",
    "icons/pypi.svg",
    "icons/zulip.svg",
]


def from_checkout(checkout: Path) -> str:
    for name in FILES:
        (OUT / name).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(checkout / BRAND_PATH / name, OUT / name)
    return f"a napari-sphinx-theme checkout ({checkout.name}); pin a tag before merging"


def from_tag(tag: str) -> str:
    base = CDN.format(tag=tag)
    for name in FILES:
        (OUT / name).parent.mkdir(parents=True, exist_ok=True)
        with urllib.request.urlopen(f"{base}/{name}") as response:  # noqa: S310 (fixed https URL)
            (OUT / name).write_bytes(response.read())
    return f"napari-sphinx-theme {tag} ({base})"


def main():
    source = sys.argv[1]
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    path = Path(source)
    described = from_checkout(path) if path.is_dir() else from_tag(source)
    (OUT / "SOURCE").write_text(
        f"Copied by prototype/update_brand.py from {described}.\n"
        "Don't edit these files here; change them in napari-sphinx-theme.\n",
        encoding="utf-8",
    )
    print(f"copied {len(FILES)} files from {described}")


if __name__ == "__main__":
    main()
