"""Python versions shown on plugin pages (hub-lite#143)."""

import pytest

from create_static_html_files import (
    NEWEST_PYTHON_MINOR,
    OLDEST_PYTHON_MINOR,
    supported_python_versions,
)

NEWEST = f"3.{NEWEST_PYTHON_MINOR}"


@pytest.mark.parametrize(
    ("requires_python", "first", "last"),
    [
        # No upper bound: up to the newest Python, not a stale 3.11 cap.
        (">=3.10", "3.10", NEWEST),
        # An exclusive bound stops one minor below it (it used to compute
        # float("3.13") - 0.1 = 3.03).
        (">=3.9,<3.13", "3.9", "3.12"),
        ("<=3.12,>=3.10", "3.10", "3.12"),
        # A patch in the lower bound still allows that minor.
        (">=3.10.2", "3.10", NEWEST),
        ("~=3.11", "3.11", NEWEST),
        (">=3.9, <4", "3.9", NEWEST),
    ],
)
def test_range(requires_python, first, last):
    versions = supported_python_versions(requires_python)
    assert versions[0] == first
    assert versions[-1] == last


def test_exclusion():
    assert "3.11" not in supported_python_versions(">=3.10,!=3.11.*")


@pytest.mark.parametrize("requires_python", [None, "", "not a specifier"])
def test_missing_or_invalid_lists_everything(requires_python):
    versions = supported_python_versions(requires_python)
    assert versions[0] == f"3.{OLDEST_PYTHON_MINOR}"
    assert versions[-1] == NEWEST
