"""Copy napari-sphinx-theme's brand files (colours, code colours, icons) into static/brand/.

They come from the theme's brand folder, the one copy napari.org and the
other napari sites share. The copy is committed, so the build doesn't need
the theme (or Sphinx, which it depends on) and a visitor's first load
doesn't need a CDN. Run this to move to a new theme release, giving the
release's full commit SHA, or a checkout's path:

    git ls-remote https://github.com/napari/napari-sphinx-theme refs/tags/<tag>
    pixi run python prototype/update_brand.py <40-character commit SHA>
    pixi run python prototype/update_brand.py ../napari-sphinx-theme

A commit is fetched from jsDelivr's GitHub endpoint by its SHA, not by tag: a
tag can be moved to other content later, a commit can't. The files are
pasted into pages (the SVGs inline), so review their diff like code.
static/brand/SOURCE records where they came from.

napari's logos are not here: they come from the napari-resources package,
a dependency of the build (build.py).
"""

import re
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

OUT = Path(__file__).parent / "static" / "brand"
REPO = "napari-sphinx-theme"
BRAND = "napari_sphinx_theme/static/brand"
FILES = [
    "napari-tokens.css",
    "pygments.css",
    "icons/github.svg",
    "icons/image-sc.svg",
    "icons/mastodon.svg",
    "icons/napari-hub.svg",
    "icons/pypi.svg",
    "icons/zulip.svg",
]


def head_commit(checkout: Path) -> str:
    """The commit a checkout (or worktree) has checked out."""
    git = shutil.which("git")
    if git is None:
        return "unknown (git not found)"
    result = subprocess.run(  # noqa: S603 (git, on a path the maintainer gave)
        [git, "-C", str(checkout), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout.strip() or "unknown"


def from_checkout(checkout: Path) -> str:
    for name in FILES:
        (OUT / name).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(checkout / BRAND / name, OUT / name)
    return (
        f"a {REPO} checkout ({checkout.name}) at commit {head_commit(checkout)}; "
        "pin a release commit before merging"
    )


def from_commit(commit: str) -> str:
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        sys.exit(
            f"{commit!r} is not a full commit SHA. Give a checkout's path, or the "
            "40-character commit of a release (git ls-remote ... refs/tags/<tag>)."
        )
    base = f"https://cdn.jsdelivr.net/gh/napari/{REPO}@{commit}/{BRAND}"
    for name in FILES:
        (OUT / name).parent.mkdir(parents=True, exist_ok=True)
        with urllib.request.urlopen(f"{base}/{name}") as response:  # noqa: S310 (fixed https URL)
            (OUT / name).write_bytes(response.read())
    return f"{REPO} commit {commit}"


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
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
