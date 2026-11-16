"""Relative links and images in a README point at the plugin's repository."""

import pytest

from create_static_html_files import github_repo_url, render_readme, resolve_readme_url

REPO = "https://github.com/ndev-kit/ndevio"


@pytest.mark.parametrize(
    ("home_github", "expected"),
    [
        ("https://github.com/ndev-kit/ndevio", REPO),
        ("https://github.com/ndev-kit/ndevio/", REPO),
        ("https://github.com/ndev-kit/ndevio.git", REPO),
        ("https://github.com/ndev-kit/ndevio#readme", REPO),
        ("https://github.com/ndev-kit/ndevio/tree/main/src", REPO),
        ("https://gitlab.com/someone/plugin", None),
        (None, None),
    ],
)
def test_github_repo_url(home_github, expected):
    assert github_repo_url(home_github) == expected


@pytest.mark.parametrize(
    ("url", "kind", "expected"),
    [
        ("CONTRIBUTING.md", "blob", f"{REPO}/blob/HEAD/CONTRIBUTING.md"),
        ("./docs/usage.md", "blob", f"{REPO}/blob/HEAD/docs/usage.md"),
        ("/docs/usage.md", "blob", f"{REPO}/blob/HEAD/docs/usage.md"),
        ("resources/shot.png", "raw", f"{REPO}/raw/HEAD/resources/shot.png"),
        ("https://example.org/x.png", "raw", "https://example.org/x.png"),
        ("//example.org/x.png", "raw", "//example.org/x.png"),
        ("#usage", "blob", "#usage"),
        ("mailto:someone@example.org", "blob", "mailto:someone@example.org"),
        ("data:image/png;base64,AAAA", "raw", "data:image/png;base64,AAAA"),
        ("", "blob", ""),
    ],
)
def test_resolve_readme_url(url, kind, expected):
    assert resolve_readme_url(url, REPO, kind) == expected


def test_markdown_links_and_images_point_at_the_repo():
    html = render_readme(
        "See [Contributing](CONTRIBUTING.md).\n\n![A screenshot](docs/shot.png)\n",
        REPO,
    )
    assert f'href="{REPO}/blob/HEAD/CONTRIBUTING.md"' in html
    assert f'src="{REPO}/raw/HEAD/docs/shot.png"' in html


def test_html_in_a_readme_points_at_the_repo():
    html = render_readme(
        '<p align="center"><img src="docs/logo.png" width="200"></p>\n\n'
        'Text with <a href="LICENSE">a license</a> inline.\n',
        REPO,
    )
    assert f'src="{REPO}/raw/HEAD/docs/logo.png"' in html
    assert f'href="{REPO}/blob/HEAD/LICENSE"' in html


def test_without_a_repo_links_are_left_alone():
    html = render_readme("[Contributing](CONTRIBUTING.md)\n", None)
    assert 'href="CONTRIBUTING.md"' in html


def test_headings_have_ids_for_in_page_links():
    html = render_readme(
        "# ndevio\n\n## How ndevio handles images\n\n[jump](#how-ndevio-handles-images)\n",
        REPO,
    )
    assert '<h2 id="how-ndevio-handles-images">' in html
    assert 'href="#how-ndevio-handles-images"' in html
    # The first heading is dropped: the page already shows the name.
    assert "<h1" not in html
