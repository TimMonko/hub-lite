"""Copy napari's brand files (colours, code colours, icons) into static/brand/.

They come from napari-sphinx-theme's brand folder, the one copy napari.org
and the other napari sites share. The copy is committed, so the build and a
visitor's first load need neither the theme nor a CDN. Run this to move to a
new theme release, giving the release's full commit SHA:

    git ls-remote https://github.com/napari/napari-sphinx-theme refs/tags/v1.2.0
    pixi run python prototype/update_brand.py <40-character commit SHA>
    pixi run python prototype/update_brand.py ../napari-sphinx-theme   # a checkout

The files are fetched from jsDelivr's GitHub endpoint by commit, not by tag:
a tag can be moved to other content later, a commit can't. The fetched files
are pasted into pages (the SVGs inline), so review their diff like code.
static/brand/SOURCE records where they came from.
"""

import re
import shutil
import sys
import urllib.request
from pathlib import Path

OUT = Path(__file__).parent / "static" / "brand"
BRAND_PATH = "napari_sphinx_theme/static/brand"
CDN = "https://cdn.jsdelivr.net/gh/napari/napari-sphinx-theme@{commit}/" + BRAND_PATH
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
    return f"a napari-sphinx-theme checkout ({checkout.name}); pin a release commit before merging"


def from_commit(commit: str) -> str:
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        sys.exit(
            f"{commit!r} is not a full commit SHA. Give a checkout's path, or the "
            "40-character commit of a release (git ls-remote ... refs/tags/<tag>)."
        )
    base = CDN.format(commit=commit)
    for name in FILES:
        (OUT / name).parent.mkdir(parents=True, exist_ok=True)
        with urllib.request.urlopen(f"{base}/{name}") as response:  # noqa: S310 (fixed https URL)
            (OUT / name).write_bytes(response.read())
    return f"napari-sphinx-theme commit {commit} ({base})"


def main():
    source = sys.argv[1]
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    path = Path(source)
    described = from_checkout(path) if path.is_dir() else from_commit(source)
    (OUT / "SOURCE").write_text(
        f"Copied by prototype/update_brand.py from {described}.\n"
        "Don't edit these files here; change them in napari-sphinx-theme.\n",
        encoding="utf-8",
    )
    print(f"copied {len(FILES)} files from {described}")


if __name__ == "__main__":
    main()
