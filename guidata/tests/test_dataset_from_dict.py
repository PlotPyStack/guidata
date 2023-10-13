# -*- coding: utf-8 -*-
#
# Licensed under the terms of the BSD 3-Clause
# (see guidata/LICENSE for details)

"""
Generate a dataset class from a dictionary
"""

# guitest: show

import numpy as np

from guidata.dataset import create_dataset_from_dict
from guidata.env import execenv

TEST_DICT1 = {
    "a": 1,
    "b": 2.0,
    "c": "test",
    "d": {"x": 1, "y": 3},
    "data": np.array([1, 2, 3]),
}
TEST_DICT2 = {
    "a": 1,
    "unsupported": [2.0, 3.0],
}


def test_dataset_from_dict():
    """Test generate dataset class from a dictionary"""
    for dictionary in (TEST_DICT1,):
        execenv.print(dictionary)
        dataset = create_dataset_from_dict(dictionary)
        execenv.print(dataset)
        execenv.print(dataset.create())
        execenv.print("")
    try:
        create_dataset_from_dict(TEST_DICT2)
        assert False, "Should have raised a ValueError"
    except ValueError:
        # This is expected
        pass


if __name__ == "__main__":
    test_dataset_from_dict()
