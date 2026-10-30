# -*- coding: utf-8 -*-
#
# Licensed under the terms of the BSD 3-Clause
# (see guidata/LICENSE for details)

"""
Test the text about a package

``AboutInfo.about`` (and ``about`` for guidata) returns the text about a package,
either as HTML (e.g. for the about dialog box) or as plain text.
"""

from __future__ import annotations

import pytest

from guidata.widgets.about import AboutInfo, about


def _get_info() -> AboutInfo:
    """Return information about a test package"""
    return AboutInfo(
        "mypackage", "1.2.3", "My description", "John Doe", 2020, "MyOrganization"
    )


def test_about_plain_text() -> None:
    """Plain-text output contains the package information without HTML"""
    text = _get_info().about(html=False)
    assert text.startswith("mypackage 1.2.3\nMy description\n")
    for info in ("John Doe", "2020", "MyOrganization", "Copyright"):
        assert info in text
    assert "<" not in text


def test_about_html() -> None:
    """HTML output contains links to the author and the organization"""
    text = _get_info().about(html=True)
    assert "<a href='https://github.com/JohnDoe'>John Doe</a>" in text
    assert "<a href='https://github.com/MyOrganization'>MyOrganization</a>" in text
    assert "\n" not in text


@pytest.mark.parametrize("html", [True, False])
def test_guidata_about(html: bool) -> None:
    """Text about guidata, complete or limited to the copyright"""
    assert "Pierre Raybaut" in about(html=html)
    text = about(html=html, copyright_only=True)
    assert "Copyright" in text
    assert "Pierre Raybaut" not in text
