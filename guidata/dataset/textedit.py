# -*- coding: utf-8 -*-
#
# Licensed under the terms of the BSD 3-Clause
# (see guidata/LICENSE for details)

"""
Text visitor for DataItem objects
(for test purpose only)
"""


def prompt(item):
    """Get item value"""
    return input(item.get_prop("display", "label") + " ? ")


class TextEditVisitor:
    """Text visitor"""

    def __init__(self, instance):
        self.instance = instance

    def visit_generic(self, item):
        """Generic visitor"""
        while True:
            value = prompt(item)
            item.set_from_string(self.instance, value)
            if item.check_item(self.instance):
                break
            print("Incorrect value!")

    visit_FloatItem = visit_generic
    visit_IntItem = visit_generic
    visit_StringItem = visit_generic
