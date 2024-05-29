# -*- coding: utf-8 -*-
#
# Licensed under the terms of the BSD 3-Clause
# (see guidata/LICENSE for details)

"""
Test if some guidata features work without Qt
(and they should!)
"""

import os


def test_imports_without_qt():
    """Test if some guidata features work without Qt"""
    os.environ["QT_API"] = "invalid_value"  # Invalid Qt API
    try:
        # pylint: disable=unused-import
        # pylint: disable=import-outside-toplevel
        import guidata.dataset.dataitems  # noqa: F401
        import guidata.dataset.datatypes  # noqa: F401
    except ValueError as exc:
        raise AssertionError("guidata imports failed without Qt") from exc


if __name__ == "__main__":
    test_imports_without_qt()
