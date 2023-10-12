# -*- coding: utf-8 -*-
#
# Licensed under the terms of the BSD 3-Clause
# (see guidata/LICENSE for details)

"""
Generate a dataset from a function signature

This function is used to generate a dataset from a function signature which has
type annotations. See the example below.
"""

# guitest: show

import numpy as np

from guidata.env import execenv
from guidata.utils.conv import create_dataset_from_func, get_arg_info


def func_ok(
    a: int, b: float, c: str = "test", d: dict[str, int] = {"x": 1, "y": 3}
) -> None:
    """A function with type annotations"""
    pass


def func_no_type(a, b, c="test"):
    """A function without type annotations"""
    pass


def func_no_default(a: int, b: float, c: str, data: np.ndarray) -> None:
    """A function without default values"""
    pass


def test_dataset_from_func():
    """Test generate dataset from function"""
    for func in (func_ok, func_no_default):
        execenv.print(func.__name__)
        execenv.print(get_arg_info(func))
        dataset = create_dataset_from_func(func)
        execenv.print(dataset)
        execenv.print(dataset.create(a=1, b=2.0))
        execenv.print("")
    func = func_no_type
    try:
        create_dataset_from_func(func)
        assert False, "Should have raised a ValueError"
    except ValueError:
        # This is expected
        pass


if __name__ == "__main__":
    test_dataset_from_func()
