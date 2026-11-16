"""Copy napari's brand files (colours, code colours, icons, logos) into static/brand/.

The colours, code colours and icons come from napari-sphinx-theme's brand
folder, and the napari logos from napari-resources: the copies napari.org and
napari itself use. The copy is committed, so the build and a visitor's first
load need neither package nor a CDN. Run this to move to new releases:

    git ls-remote https://github.com/napari/napari-sphinx-theme refs/tags/<tag>
    pixi run python prototype/update_brand.py <theme commit> ../napari-resources
    pixi run python prototype/update_brand.py ../napari-sphinx-theme ../napari-resources

The theme's files can come from a checkout, or from jsDelivr's GitHub
endpoint by the release's full commit SHA (not its tag: a tag can be moved to
other content later, a commit can't). napari-resources must be a checkout of
the release, installed (`uv sync`): its logos are generated at install and
aren't in git, so they can't be fetched by commit. SOURCE records the
checkout's commit. The files are pasted into pages (the SVGs inline), so
review their diff like code. static/brand/SOURCE records where they came from.
"""

import re
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

OUT = Path(__file__).parent / "static" / "brand"

# repository -> {path in the repository: path under static/brand/}
THEME_BRAND = "napari_sphinx_theme/static/brand"
SOURCES = {
    "napari-sphinx-theme": {
        f"{THEME_BRAND}/{name}": name
        for name in [
            "napari-tokens.css",
            "pygments.css",
            "icons/github.svg",
            "icons/image-sc.svg",
            "icons/mastodon.svg",
            "icons/napari-hub.svg",
            "icons/pypi.svg",
            "icons/zulip.svg",
        ]
    },
    "napari-resources": {
        "src/napari_resources/resources/logos/special/silhouette-current-color.svg": "icons/napari.svg",
        # The header logo: the dark one has a gold border that shows on the dark navbar.
        "src/napari_resources/resources/logos/generated/gradient-plain-light.svg": "logos/napari-light.svg",
        "src/napari_resources/resources/logos/generated/gradient-plain-dark.svg": "logos/napari-dark.svg",
    },
}
# Generated at install, not in git, so only a checkout has them.
CHECKOUT_ONLY = {"napari-resources"}


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


def copy(repo: str, source: str) -> str:
    """Copy one repository's files from a checkout or a commit; describe where from."""
    files = SOURCES[repo]
    checkout = Path(source)
    if checkout.is_dir():
        for src, dest in files.items():
            if not (checkout / src).is_file():
                sys.exit(
                    f"{checkout / src} is missing. Is the {repo} checkout installed (uv sync)?"
                )
            (OUT / dest).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(checkout / src, OUT / dest)
        return f"a {repo} checkout ({checkout.name}) at commit {head_commit(checkout)}"
    if repo in CHECKOUT_ONLY:
        sys.exit(
            f"Give a {repo} checkout's path: its logos are generated at install, not in git."
        )
    if not re.fullmatch(r"[0-9a-f]{40}", source):
        sys.exit(
            f"{source!r} is not a full commit SHA. Give a {repo} checkout's path, or "
            "the 40-character commit of a release (git ls-remote ... refs/tags/<tag>)."
        )
    base = f"https://cdn.jsdelivr.net/gh/napari/{repo}@{source}"
    for src, dest in files.items():
        (OUT / dest).parent.mkdir(parents=True, exist_ok=True)
        with urllib.request.urlopen(f"{base}/{src}") as response:  # noqa: S310 (fixed https URL)
            (OUT / dest).write_bytes(response.read())
    return f"{repo} commit {source}"


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    described = [
        copy(repo, source) for repo, source in zip(SOURCES, sys.argv[1:], strict=True)
    ]
    (OUT / "SOURCE").write_text(
        "Copied by prototype/update_brand.py from:\n"
        + "".join(f"- {line}\n" for line in described)
        + "Don't edit these files here; change them in napari-sphinx-theme or napari-resources.\n",
        encoding="utf-8",
    )
    count = sum(len(files) for files in SOURCES.values())
    print(f"copied {count} files from", "; ".join(described))


if __name__ == "__main__":
    main()
