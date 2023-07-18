# -*- coding: utf-8 -*-
#
# Copyright © Spyder Project Contributors
# Licensed under the terms of the MIT License


"""
Tests for dataframeeditor.py
"""

# guitest: show

import numpy as np
import pytest

try:
    import pandas as pd
    import pandas.testing as pdt

    from guidata.widgets.dataframeeditor import DataFrameEditor
except ImportError:
    # pandas is not installed
    pd = pdt = DataFrameEditor = None

from guidata.env import execenv
from guidata.qthelpers import exec_dialog, qt_app_context


@pytest.mark.skipif(pd is None, reason="pandas is not installed")
def test_dataframeeditor():
    """DataFrame editor test"""

    def test_edit(data, title="", parent=None):
        """Test subroutine"""
        dlg = DataFrameEditor(parent=parent)

        if dlg.setup_and_check(data, title=title):
            exec_dialog(dlg)
            return dlg.get_value()
        else:
            import sys

            sys.exit(1)

    with qt_app_context():
        df1 = pd.DataFrame(
            [
                [True, "bool"],
                [1 + 1j, "complex"],
                ["test", "string"],
                [1.11, "float"],
                [1, "int"],
                [np.random.rand(3, 3), "Unkown type"],
                ["Large value", 100],
                ["áéí", "unicode"],
            ],
            index=["a", "b", np.nan, np.nan, np.nan, "c", "Test global max", "d"],
            columns=[np.nan, "Type"],
        )
        out = test_edit(df1)
        pdt.assert_frame_equal(df1, out)

        result = pd.Series([True, "bool"], index=[np.nan, "Type"], name="a")
        out = test_edit(df1.iloc[0])
        pdt.assert_series_equal(result, out)

        df1 = pd.DataFrame(np.random.rand(100100, 10))
        out = test_edit(df1)
        pdt.assert_frame_equal(out, df1)

        series = pd.Series(np.arange(10), name=0)
        out = test_edit(series)
        pdt.assert_series_equal(series, out)

        execenv.print("OK")


if __name__ == "__main__":
    test_dataframeeditor()
