# Version 3.15 #

## guidata Version 3.15.0 ##

✨ New features:

* **JSON Schema export for `DataSet` classes** — added a new `guidata.dataset.jsonschema` module that converts any `DataSet` subclass into a UI-framework-agnostic `JSON Schema 2020-12` document, augmented with `x-guidata-*` extension keywords for guidata-specific concerns (groups, tabs, units, choice labels, dynamic choices, image icons, layout tree). Public API: `dataset_to_schema()` (class → schema), `dataset_to_schema_with_values()` (instance → schema + current values), `resolve_dynamic_choices()` (resolve a `ChoiceItem` whose choices are computed by a callable). All three helpers are re-exported from `guidata.dataset`. Items requiring callables that cannot cross JSON (`ButtonItem`, conditional visibility through callable `active` props) raise `NotImplementedError`. This enables non-Qt frontends — typically a browser/React UI driven by Pyodide — to render guidata `DataSet` declarations natively while keeping a single source of truth.

* **Pluggable UI backend for `DataSet` dialogs** — added a new `guidata.dataset.backends` module that exposes a small handler registry consulted by `DataSet.edit()`, `DataSet.view()` and `DataSetGroup.edit()` before falling back to the existing Qt dialogs. Applications can register handlers for the `"edit_dataset"`, `"view_dataset"` and `"edit_dataset_group"` slots to plug an alternate UI (web, CLI, notebook, …) without modifying the Qt path used by existing applications. When no handler is registered, behaviour is byte-for-byte identical to previous releases. Public API: `set_handler()`, `get_handler()`, `has_handler()`, `clear_handler()`, `clear_all_handlers()`.

* **Asynchronous `DataSet.edit_async()`** — added a coroutine variant of `DataSet.edit()` for environments whose event loop cannot block the calling thread (typically browser/JavaScript frontends). When an `"edit_dataset_async"` handler is registered in `guidata.dataset.backends`, it is awaited and its result returned; otherwise `edit_async()` falls back to the synchronous `edit()`, so it is always safe to call.
