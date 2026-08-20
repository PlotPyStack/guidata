"""Tests for the vendored darkdetect package."""

import runpy
from types import SimpleNamespace

import pytest

from guidata.external import darkdetect
from guidata.external.darkdetect import _dummy, _linux_detect


def test_darkdetect_api() -> None:
    """Check the vendored version and public API."""
    assert darkdetect.__version__ == "0.8.0"
    for name in ("theme", "isDark", "isLight", "listener"):
        assert callable(getattr(darkdetect, name))


@pytest.mark.parametrize(
    ("version", "expected"),
    [("10.13.6", False), ("10.14.0", True), ("11.0", True)],
)
def test_macos_supported_version(monkeypatch, version: str, expected: bool) -> None:
    """Check the macOS 10.14 minimum without importing AppKit."""
    platform = SimpleNamespace(mac_ver=lambda: (version, ("", "", ""), ""))
    monkeypatch.setattr(darkdetect, "platform", platform, raising=False)
    assert darkdetect.macos_supported_version() is expected


def test_linux_theme_falls_back_to_gtk(monkeypatch) -> None:
    """Use the GTK theme when the freedesktop color scheme is unavailable."""
    outputs = iter((b"", b"'Adwaita-dark'\n"))
    calls = []

    def run(command, *, capture_output):
        calls.append(command)
        return SimpleNamespace(stdout=next(outputs))

    monkeypatch.setattr(_linux_detect.subprocess, "run", run)

    assert _linux_detect.theme() == "Dark"
    assert calls[0][-1] == "color-scheme"
    assert calls[1][-1] == "gtk-theme"


def test_linux_theme_uses_color_scheme(monkeypatch) -> None:
    """Prefer the freedesktop color scheme when it is available."""
    calls = []

    def run(command, *, capture_output):
        calls.append(command)
        return SimpleNamespace(stdout=b"'prefer-dark'\n")

    monkeypatch.setattr(_linux_detect.subprocess, "run", run)

    assert _linux_detect.theme() == "Dark"
    assert len(calls) == 1
    assert calls[0][-1] == "color-scheme"


def test_dummy_listener_is_unsupported() -> None:
    """Keep listener behavior explicit on unsupported platforms."""
    assert _dummy.theme() is None
    assert _dummy.isDark() is None
    assert _dummy.isLight() is None
    with pytest.raises(NotImplementedError):
        _dummy.listener(lambda theme: None)


def test_native_theme_smoke() -> None:
    """Exercise the detector selected for the host platform."""
    assert darkdetect.theme() in ("Dark", "Light", None)
    assert darkdetect.isDark() in (True, False, None)
    assert darkdetect.isLight() in (True, False, None)


def test_module_cli(capsys) -> None:
    """Run the vendored module entry point."""
    runpy.run_module("guidata.external.darkdetect", run_name="__main__")
    assert capsys.readouterr().out in (
        "Current theme: Dark\n",
        "Current theme: Light\n",
        "Current theme: None\n",
    )
