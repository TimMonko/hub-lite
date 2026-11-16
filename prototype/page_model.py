"""The page model: what a plugin page shows, as plain values.

This is the only place that decides facts about a plugin (which Python
versions, which plugin types, which links). The template only lays them out.
Every field says where its value comes from.
"""

from __future__ import annotations

import dataclasses
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from create_static_html_files import (  # noqa: E402
    PluginPageData,
    extract_github_info,
    get_plugin_types,
    render_readme,
    supported_python_versions,
)

MISSING = {"", "n/a", "none", "nan"}


@dataclasses.dataclass
class Link:
    label: str
    url: str
    kind: str  # "pypi", "github", "source" or "website": picks the icon


@dataclasses.dataclass
class PluginPage:
    name: str  # normalized PyPI name; also the page's file name
    display_name: str  # from the npe2 manifest
    summary: str  # PyPI summary
    version: str  # latest release
    release_date: str | None  # date of the latest release (YYYY-MM-DD)
    first_released: str | None  # date of the first release (YYYY-MM-DD)
    authors: list[str]  # PEP 621 author names
    license: str  # as declared; SPDX cleanup is hub-lite#76
    links: list[Link]  # PyPI always, then source and website if declared
    plugin_types: list[str]  # from the npe2 manifest's contributions
    python_versions: list[str]  # from requires-python (hub-lite#143)
    operating_systems: list[str]  # from "Operating System ::" classifiers
    requirements: list[str]  # requires-dist, as declared
    reads: list[str]  # reader filename patterns
    writes: list[str]  # writer filename extensions
    readme_html: str  # the PyPI description, rendered


def page_from_data(plugin: PluginPageData) -> PluginPage:
    links = [Link("PyPI", plugin.home_pypi, "pypi")]
    if plugin.home_github and plugin.home_github.lower() not in MISSING:
        user, repo = extract_github_info(plugin.home_github)
        if user and repo:
            links.append(Link(f"{user}/{repo}", plugin.home_github, "github"))
        else:
            links.append(Link("Source code", plugin.home_github, "source"))
    if plugin.home_other and plugin.home_other.lower() not in MISSING:
        links.append(Link("Website", plugin.home_other, "website"))

    operating_systems = [
        item.split("Operating System :: ", 1)[1].strip("' \"")
        for item in plugin.package_metadata_classifiers
        if "Operating System ::" in item
    ]

    return PluginPage(
        name=plugin.normalized_name,
        display_name=plugin.display_name or plugin.name,
        summary=plugin.summary,
        version=plugin.version,
        release_date=(plugin.modified_at or "")[:10] or None,
        first_released=(plugin.created_at or "")[:10] or None,
        authors=plugin.authors,
        license=plugin.license,
        links=links,
        plugin_types=get_plugin_types(plugin),
        python_versions=supported_python_versions(
            plugin.package_metadata_requires_python
        ),
        operating_systems=operating_systems,
        requirements=plugin.package_metadata_requires_dist,
        reads=plugin.contributions_readers_filename_patterns,
        writes=plugin.contributions_writers_filename_extensions,
        readme_html=render_readme(
            plugin.package_metadata_description or "", plugin.home_github
        ),
    )
