# -*- coding: utf-8 -*-
#
# Licensed under the terms of the BSD 3-Clause
# (see guidata/LICENSE for details)

"""Translation tests

Check that guidata translations are available, and that a missing, corrupted or
unreadable gettext catalog never prevents the application from starting: the
translation callback falls back to English (and warns if the catalog is corrupted).
"""

# guitest: show

from __future__ import annotations

import struct
import warnings

import pytest

from guidata import configtools
from guidata.config import _
from guidata.env import execenv

translations = (_("Some required entries are incorrect"),)

MODNAME = "guidata_test_catalog"
UTF8_HEADER = b"Content-Type: text/plain; charset=UTF-8\n"


def _build_mo(messages: dict[bytes, bytes]) -> bytes:
    """Build a little-endian GNU gettext binary catalog

    Args:
        messages: mapping of original strings to translated strings (the empty
         original string holds the catalog header)

    Returns:
        Binary content of the catalog
    """
    keys = sorted(messages)
    ids = strs = b""
    entries = []
    for key in keys:
        entries.append((len(ids), len(key), len(strs), len(messages[key])))
        ids += key + b"\0"
        strs += messages[key] + b"\0"
    keystart = 7 * 4 + 16 * len(keys)
    valuestart = keystart + len(ids)
    koffsets, voffsets = [], []
    for id_off, id_len, str_off, str_len in entries:
        koffsets += [id_len, id_off + keystart]
        voffsets += [str_len, str_off + valuestart]
    offsets = koffsets + voffsets
    header = struct.pack(
        "<7I", 0x950412DE, 0, len(keys), 7 * 4, 7 * 4 + 8 * len(keys), 0, 0
    )
    return header + struct.pack(f"<{len(offsets)}I", *offsets) + ids + strs


VALID_MO = _build_mo({b"": UTF8_HEADER, b"Hello": b"Bonjour"})

CORRUPTED_CATALOGS = {
    "bad_magic_number": b"\0" * 28,
    "empty_file": b"",
    "truncated_header": VALID_MO[:10],
    "offsets_past_end_of_file": VALID_MO[:-12],
    "unknown_charset": _build_mo(
        {b"": b"Content-Type: text/plain; charset=unknown-charset\n", b"Hello": b"X"}
    ),
    "invalid_utf8_translation": _build_mo({b"": UTF8_HEADER, b"Hello": b"\xff\xfe"}),
    "invalid_plural_forms": _build_mo(
        {b"": UTF8_HEADER + b"Plural-Forms: nplurals=2; plural=import os;\n"}
    ),
}


@pytest.fixture(name="locale_dir")
def fixture_locale_dir(tmp_path, monkeypatch):
    """Isolated French locale directory used by `get_translation`"""
    monkeypatch.setattr(configtools, "get_module_locale_path", lambda _: str(tmp_path))
    monkeypatch.setenv("LANGUAGE", "fr")
    msgdir = tmp_path / "fr" / "LC_MESSAGES"
    msgdir.mkdir(parents=True)
    return msgdir


def test_translations():
    """Test translations"""
    for text in translations:
        execenv.print(text)
    execenv.print("OK")


def test_valid_catalog(locale_dir):
    """A valid catalog is used without warning"""
    (locale_dir / f"{MODNAME}.mo").write_bytes(VALID_MO)
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        translate = configtools.get_translation(MODNAME)
    assert translate("Hello") == "Bonjour"


def test_missing_catalog(locale_dir):
    """A missing catalog silently falls back to English"""
    assert not any(locale_dir.iterdir())
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        translate = configtools.get_translation(MODNAME)
    assert translate("Hello") == "Hello"


@pytest.mark.parametrize("content", CORRUPTED_CATALOGS.values(), ids=CORRUPTED_CATALOGS)
def test_corrupted_catalog(locale_dir, content):
    """A corrupted catalog falls back to English with a warning"""
    (locale_dir / f"{MODNAME}.mo").write_bytes(content)
    with pytest.warns(RuntimeWarning, match="falling back to English") as record:
        translate = configtools.get_translation(MODNAME)
    assert MODNAME in str(record[0].message)
    assert translate("Hello") == "Hello"


if __name__ == "__main__":
    test_translations()
