# guidata AI Coding Agent Instructions

## Project Overview

**guidata** is the foundational library of the PlotPyStack, providing automatic GUI generation from Python data structures. It enables declarative definition of parameter sets that automatically generate Qt editing widgets.

### Technology Stack

- **Python**: 3.9+ (`from __future__ import annotations`)
- **Core**: NumPy (≥1.22), h5py (≥3.6), QtPy (≥1.9)
- **GUI**: Qt via QtPy (PyQt5/PyQt6/PySide6)
- **Testing**: pytest
- **Linting**: Ruff (preferred), Pylint

### Architecture

```
guidata/
├── dataset/        # Core DataSet system (items, types, serialization)
├── widgets/        # Ready-to-use Qt widgets (console, editors, browsers)
├── io/             # HDF5, JSON, INI serialization
├── utils/          # CLI tools (translations, build, cleanup)
├── config.py       # Configuration and translation setup
├── configtools.py  # Image/icon path management
├── qthelpers.py    # Qt utility functions
└── tests/          # pytest suite
```

## Development Workflows

### Running Commands

```powershell
python -m pytest --ff                    # Run tests
python -m ruff format                    # Format code
python -m ruff check --fix               # Lint with auto-fix
python -m guidata.utils.translations scan --name guidata --directory .  # Update .po files
```

### CLI Tools

guidata provides command-line utilities:

```powershell
gtrans scan --name myapp --directory .   # Scan for translatable strings
gtrans compile --name myapp --directory . # Compile .mo files
greqs all                                 # Generate requirements docs
gbuild                                    # Secure package build
gclean                                    # Cleanup build artifacts
```

## Core Patterns

### DataSet System

The heart of guidata - declarative parameter definitions:

```python
import guidata.dataset as gds

class ProcessingParams(gds.DataSet):
    """Parameters for my processing."""

    threshold = gds.FloatItem("Threshold", default=0.5, min=0, max=1)
    method = gds.ChoiceItem("Method", ["fast", "accurate"], default="fast")
    enabled = gds.BoolItem("Enable feature", default=True)

    # Factory method for script-friendly instantiation
    @staticmethod
    def create(threshold: float = 0.5, method: str = "fast") -> ProcessingParams:
        return ProcessingParams(threshold=threshold, method=method)
```

### Available Data Items

| Item Type | Purpose |
|-----------|---------|
| `IntItem`, `FloatItem` | Numeric input with optional bounds |
| `StringItem`, `TextItem` | Single/multi-line text |
| `BoolItem` | Checkbox |
| `ChoiceItem`, `MultipleChoiceItem` | Single/multiple selection |
| `ColorItem`, `FontFamilyItem` | Color/font pickers |
| `FileOpenItem`, `FileSaveItem`, `DirectoryItem` | Path selection |
| `DateItem`, `DateTimeItem` | Date/time pickers |
| `FloatArrayItem` | NumPy array editor |
| `DictItem` | Dictionary editor |

### DataSet Groups and Tabs

Organize items visually:

```python
class MyParams(gds.DataSet):
    # Tab groups
    _bg = gds.BeginTabGroup("Settings")

    _t1 = gds.BeginGroup("General")
    name = gds.StringItem("Name")
    _t1e = gds.EndGroup("General")

    _t2 = gds.BeginGroup("Advanced")
    iterations = gds.IntItem("Iterations", default=100)
    _t2e = gds.EndGroup("Advanced")

    _bge = gds.EndTabGroup("Settings")
```

### Serialization

DataSets support multiple formats:

```python
# HDF5
from guidata.io import HDF5Reader, HDF5Writer
with HDF5Writer("params.h5") as writer:
    params.serialize(writer)

# JSON
from guidata.dataset import dataset_to_json, json_to_dataset
json_str = dataset_to_json(params)
restored = json_to_dataset(json_str)
```

### GUI Integration

Display/edit DataSets in dialogs:

```python
# Edit in modal dialog
params = ProcessingParams()
if params.edit():  # Returns True if OK clicked
    print(f"Threshold: {params.threshold}")

# Embed in custom widget
from guidata.dataset.qtwidgets import DataSetEditGroupBox
groupbox = DataSetEditGroupBox("Parameters", ProcessingParams)
```

## Coding Conventions

### Type Annotations

```python
from __future__ import annotations
```

### Translations

```python
from guidata.config import _

label = _("Processing parameters")  # ✅ Translatable
```

### Docstrings

Google-style:

```python
def create_widget(parent: QWidget | None = None) -> DataSetEditGroupBox:
    """Create parameter editing widget.

    Args:
        parent: Parent widget

    Returns:
        Configured edit group box
    """
```

## Key Files Reference

| File | Purpose |
|------|---------|
| `guidata/dataset/__init__.py` | All DataSet exports |
| `guidata/dataset/dataitems.py` | Item definitions (IntItem, etc.) |
| `guidata/dataset/datatypes.py` | DataSet base class |
| `guidata/dataset/qtwidgets.py` | Qt widget generation |
| `guidata/dataset/io.py` | Serialization support |
| `guidata/config.py` | Configuration, `_()` function |
| `guidata/qthelpers.py` | Qt utilities |
| `guidata/utils/translations.py` | Translation CLI |

## Related Projects

- **PythonQwt**: Low-level Qt plotting (sibling)
- **PlotPy**: Interactive plotting using guidata (downstream)
- **Sigima/DataLab**: Scientific applications (downstream)
