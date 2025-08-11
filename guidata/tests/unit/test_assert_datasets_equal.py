# -*- coding: utf-8 -*-
#
# Licensed under the terms of the BSD 3-Clause
# (see guidata/LICENSE for details)

"""
Regression test for DataSet equality/identity semantics.

This test ensures DataSet does NOT implement value-based __eq__ (identity only)
and remains hashable, so instances can be used as dict/set keys. It guards
against reintroducing __eq__, which would implicitly disable __hash__ and
break collections. For value comparisons in tests, use
guidata.testing.assert_datasets_equal.
"""

import guidata.dataset as gds


def test_dataset_identity_semantics():
    """Test identity semantics for datasets"""

    class _DS(gds.DataSet):
        a = gds.IntItem("a", default=1)

    d1, d2 = _DS.create(a=1), _DS.create(a=1)
    # identity equality
    assert d1 != d2
    assert d1 == d1
    # hashable (usable as dict/set keys)
    s = {d1, d2}
    assert d1 in s and d2 in s
    assert type(_DS.__eq__) is type(object.__eq__)
    assert _DS.__hash__ is object.__hash__
