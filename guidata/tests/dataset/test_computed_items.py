# -*- coding: utf-8 -*-
#
# Licensed under the terms of the BSD 3-Clause
# (see guidata/LICENSE for details)

"""
Demonstrates how items may be computed based on other items' values.

The computed items feature allows you to create read-only items whose values are
automatically calculated using a method of the dataset. This is similar to computed
properties in other frameworks.
"""

# guitest: show

import guidata.dataset as gds
from guidata.env import execenv
from guidata.qthelpers import qt_app_context


class Parameters(gds.DataSet):
    """Example dataset with computed items"""

    def compute_sum(self) -> float:
        """Compute the sum of x1 and x2"""
        return self.x1 + self.x2

    def compute_results(self) -> str:
        """Compute a results string based on current values"""
        sum_value = self.x1 + self.x2
        return f"""Results:

    String: {self.string}
    Sum: {sum_value:.2f}
    Boolean: {self.boolean}
    Color: {self.color}
    Choice: {self.choice}"""

    string = gds.StringItem("String", default="foobar")
    x1 = gds.FloatItem("x1", default=2.0)
    x2 = gds.FloatItem("x2", default=3.0)
    # This item will be computed by calling the compute_sum method
    x1plusx2 = gds.FloatItem("x1+x2 (computed)").set_computed(compute_sum)
    boolean = gds.BoolItem("Boolean", default=True)
    color = gds.ColorItem("Color", default="red")
    choice = gds.ChoiceItem(
        "Single choice",
        (("First", "first"), ("Second", "second"), ("Third", "third")),
        default="first",
    ).set_pos(col=1, colspan=2)
    # This item will be computed by calling the compute_results method
    results = gds.TextItem("Results (computed)").set_computed(compute_results)


def test_computed_items():
    """Test computed items"""
    with qt_app_context():
        prm = Parameters()

        # Test that computed items work
        execenv.print(f"x1: {prm.x1}")
        execenv.print(f"x2: {prm.x2}")
        execenv.print(f"x1+x2 (computed): {prm.x1plusx2}")
        execenv.print(f"Results (computed):\n{prm.results}")

        # Test that computed items are read-only
        try:
            prm.x1plusx2 = 10.0
            raise Exception("Should not be able to set computed item!")
        except ValueError as e:
            execenv.print(f"✓ Correctly prevented setting computed item: {e}")

        # Test that computed items update when dependencies change
        prm.x1 = 5.0
        prm.x2 = 7.0
        execenv.print("\nAfter changing x1=5.0, x2=7.0:")
        execenv.print(f"x1+x2 (computed): {prm.x1plusx2}")
        execenv.print(f"Results (computed):\n{prm.results}")

        execenv.print("\n" + "=" * 60)
        execenv.print("REAL-TIME GUI UPDATE TEST:")
        execenv.print("When you edit values in the GUI, computed items should")
        execenv.print("update automatically in real-time as you type!")
        execenv.print("Try changing x1 and x2 values and watch the computed")
        execenv.print("fields update automatically.")
        execenv.print("=" * 60)

        execenv.print(prm)
        if prm.edit():
            execenv.print(prm)
        prm.view()
        execenv.print("OK")


if __name__ == "__main__":
    test_computed_items()
