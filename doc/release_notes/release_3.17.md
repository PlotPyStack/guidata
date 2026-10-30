# Version 3.17 #

## guidata Version 3.17.0 ##

* Python 3.10 or later is now required. Python 3.9 users must keep an earlier compatible release.

✨ New features:

* **`get_pixmap` — sharp images with display scaling** — the new `guidata.configtools.get_pixmap` function loads an image as a pixmap at the resolution of the display: when the display scaling is greater than 100% (e.g. 125%, 150%), the high-resolution variants of the image following Qt's `@Nx` naming convention (e.g. `logo@2x.png` next to `logo.png`) are used, so that the image remains sharp instead of being upscaled. `get_image_label` (and thus `get_image_layout`) now relies on it.

🛠 Bug fixes:

* **Text not scaled with display scaling on Windows (Qt5)** — with a Windows display scaling greater than 100% (e.g. 125%), the text of most widgets (labels, buttons, data set editors, ...) kept the size it has at 100%, while menus and status bars were scaled, because Qt5 derives its default font from a legacy system font which ignores the display scaling. Applications created with `guidata.qapplication` (or `qt_app_context`) now use the message font of the system as default font (typically "Segoe UI", 9pt), like with Qt6: the text follows the display scaling and the Windows text size setting.
* **Application startup blocked by a corrupted translation file** — when a `.mo` translation catalog was corrupted or unreadable (e.g. truncated during installation), importing guidata failed with an error such as `OSError: Bad magic number`. The same applied to any application relying on `guidata.configtools.get_translation`, like PlotPy, Sigima or DataLab, so the application could not start at all. The interface now falls back to English, and a `RuntimeWarning` identifies the faulty catalog (fixes [Issue #119](https://github.com/PlotPyStack/guidata/issues/119)).
* **Error when editing a dictionary field in a JSON Schema based form** — in a form generated with `guidata.dataset.dataset_to_schema` (e.g. in a web frontend), editing a `DictItem` field failed with `TypeError: DictItem.__dictedit() missing 1 required positional argument: 'parent'`: the button opening the dictionary editor in the Qt interface was handled as a callback updating the other fields. `DictItem` fields are no longer flagged with `x-guidata-has-callback`, and `resolve_dataset_callbacks` returns an empty mapping for them (fixes [Issue #123](https://github.com/PlotPyStack/guidata/issues/123)).
* **Date/time callback never called** — the `display` callback of a `DateTimeItem` was never called when the date or time was changed in a dataset editor, so that the values computed from it were not updated. The callback is now called on each change, with the new value of the item (a `datetime.datetime` object), like for the other items (fixes [Issue #123](https://github.com/PlotPyStack/guidata/issues/123)).
* **Plain-text "about" information** — `guidata.widgets.about.about(html=False)` (and `AboutInfo.about(html=False)`) failed with `UnboundLocalError` instead of returning the information about the package as plain text (fixes [Issue #123](https://github.com/PlotPyStack/guidata/issues/123)).
* **French translations of the DataFrame editor** — when entering a number format not starting with `%`, the French error message stated the opposite of the actual rule ("must not start with '%'"), and the title of the export dialog box was shown in English. Both are now correctly translated (fixes [Issue #123](https://github.com/PlotPyStack/guidata/issues/123)).
