# -*- coding: utf-8 -*-
#
# Licensed under the terms of the BSD 3-Clause
# (see guidata/LICENSE for details)

"""
Update/Restore dataset from/to another dataset or dictionary
"""

# guitest: show

import numpy as np

from guidata.dataset.conv import restore_dataset, update_dataset
from guidata.tests.dataset.test_all_items import Parameters


def test_update_restore_dataset():
    """Test update/restore dataset from/to another dataset or dictionary"""
    dataset = Parameters()
    dsdict = {
        "integer": 1,
        "float_slider": 1.0,
        "bool1": True,
        "string": "test",
        "floatarray": np.array([1, 2, 3]),
        "dictionary": {"a": 1, "b": 2},
    }
    # Update dataset from dictionary
    update_dataset(dataset, dsdict)
    # Check dataset values
    assert dataset.integer == dsdict["integer"]
    assert dataset.float_slider == dsdict["float_slider"]
    assert dataset.bool1 == dsdict["bool1"]
    assert dataset.string == dsdict["string"]
    assert np.all(dataset.floatarray == dsdict["floatarray"])
    assert dataset.dictionary == dsdict["dictionary"]
    # Update dataset from another dataset
    dataset2 = Parameters()
    update_dataset(dataset2, dataset)
    # Check dataset values
    assert dataset2.integer == dataset.integer
    assert dataset2.float_slider == dataset.float_slider
    assert dataset2.bool1 == dataset.bool1
    assert dataset2.string == dataset.string
    assert np.all(dataset2.floatarray == dataset.floatarray)
    assert dataset2.dictionary == dataset.dictionary
    # Restore dataset from dictionary
    restore_dataset(dataset, dsdict)
    # Check dataset values
    assert dataset.integer == dsdict["integer"]
    assert dataset.float_slider == dsdict["float_slider"]
    assert dataset.bool1 == dsdict["bool1"]
    assert dataset.string == dsdict["string"]
    assert np.all(dataset.floatarray == dsdict["floatarray"])
    assert dataset.dictionary == dsdict["dictionary"]


if __name__ == "__main__":
    test_update_restore_dataset()
