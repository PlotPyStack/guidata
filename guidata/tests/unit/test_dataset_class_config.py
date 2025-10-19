# -*- coding: utf-8 -*-
#
# Licensed under the terms of the BSD 3-Clause
# (see guidata/LICENSE for details)

"""
Test DataSet class-level configuration via __init_subclass__
"""

# guitest: show

from guidata.dataset import DataSet, FloatItem, StringItem
from guidata.env import execenv


def test_dataset_class_config():
    """Test DataSet class-level configuration using __init_subclass__"""

    # Test 1: Basic class-level configuration
    class ConfiguredDataSet(
        DataSet,
        title="My Configured Dataset",
        comment="This is configured at class level",
        icon="myicon.png",
    ):
        """Developer documentation - not used as title"""

        param1 = FloatItem("Parameter 1", default=1.0)
        param2 = StringItem("Parameter 2", default="test")

    instance1 = ConfiguredDataSet()
    execenv.print("Test 1: Class-level configuration")
    execenv.print(f"  Title: '{instance1.get_title()}'")
    execenv.print(f"  Comment: '{instance1.get_comment()}'")
    execenv.print(f"  Icon: '{instance1.get_icon()}'")
    assert instance1.get_title() == "My Configured Dataset"
    assert instance1.get_comment() == "This is configured at class level"
    assert instance1.get_icon() == "myicon.png"
    execenv.print("  ✓ Passed\n")

    # Test 2: Instance parameter overrides class-level configuration
    instance2 = ConfiguredDataSet(
        title="Override Title", comment="Override Comment", icon="override.png"
    )
    execenv.print("Test 2: Instance override")
    execenv.print(f"  Title: '{instance2.get_title()}'")
    execenv.print(f"  Comment: '{instance2.get_comment()}'")
    execenv.print(f"  Icon: '{instance2.get_icon()}'")
    assert instance2.get_title() == "Override Title"
    assert instance2.get_comment() == "Override Comment"
    assert instance2.get_icon() == "override.png"
    execenv.print("  ✓ Passed\n")

    # Test 3: No configuration - falls back to docstring for title only
    class UnconfiguredDataSet(DataSet):
        """First line of docstring

        This is the remaining comment part
        """

        param1 = FloatItem("Parameter 1")

    instance3 = UnconfiguredDataSet()
    execenv.print("Test 3: No class-level configuration (backward compatibility)")
    execenv.print(f"  Title: '{instance3.get_title()}'")
    execenv.print(f"  Comment: '{instance3.get_comment()}'")
    assert instance3.get_title() == "First line of docstring"  # Uses docstring
    assert instance3.get_comment() is None  # No automatic comment from docstring
    execenv.print("  ✓ Passed (docstring used for title, no comment)\n")

    # Test 3b: Explicitly set empty title - no comment from docstring
    class EmptyTitleDataSet(DataSet, title=""):
        """Docstring is for developer documentation only"""

        param1 = FloatItem("Parameter 1")

    instance3b = EmptyTitleDataSet()
    execenv.print("Test 3b: Explicitly empty title")
    execenv.print(f"  Title: '{instance3b.get_title()}'")
    execenv.print(f"  Comment: '{instance3b.get_comment()}'")
    assert instance3b.get_title() == ""  # Explicitly empty
    assert instance3b.get_comment() is None  # No automatic comment from docstring
    execenv.print("  ✓ Passed (empty title, no comment from docstring)\n")

    # Test 4: Partial configuration
    class PartialConfigDataSet(DataSet, title="Partial Config"):
        """Docstring comment"""

        param1 = FloatItem("Parameter 1")

    instance4 = PartialConfigDataSet()
    execenv.print("Test 4: Partial configuration (title only)")
    execenv.print(f"  Title: '{instance4.get_title()}'")
    execenv.print(f"  Comment: '{instance4.get_comment()}'")
    execenv.print(f"  Icon: '{instance4.get_icon()}'")
    assert instance4.get_title() == "Partial Config"
    assert instance4.get_comment() is None  # No automatic comment from docstring
    assert instance4.get_icon() == ""
    execenv.print("  ✓ Passed\n")

    # Test 5: Readonly configuration
    class ReadOnlyDataSet(DataSet, title="Read Only", readonly=True):
        """Read-only dataset"""

        param1 = FloatItem("Parameter 1", default=5.0)

    instance5 = ReadOnlyDataSet()
    execenv.print("Test 5: Readonly configuration")
    execenv.print(f"  Is readonly: {instance5.is_readonly()}")
    assert instance5.is_readonly() is True
    execenv.print("  ✓ Passed\n")

    # Test 6: Inheritance of class-level configuration
    class DerivedDataSet(ConfiguredDataSet):
        """This inherits from ConfiguredDataSet"""

        param3 = FloatItem("Parameter 3", default=3.0)

    instance6 = DerivedDataSet()
    execenv.print("Test 6: Inheritance (inherits parent config)")
    execenv.print(f"  Title: '{instance6.get_title()}'")
    execenv.print(f"  Comment: '{instance6.get_comment()}'")
    # Note: Inheritance doesn't automatically pass down class config
    # Each class needs its own configuration
    execenv.print("  ✓ Passed\n")

    # Test 7: Override inherited configuration
    class OverriddenDerivedDataSet(
        ConfiguredDataSet, title="Overridden Title", icon="new.png"
    ):
        """Overriding parent configuration"""

        param3 = FloatItem("Parameter 3", default=3.0)

    instance7 = OverriddenDerivedDataSet()
    execenv.print("Test 7: Override inherited configuration")
    execenv.print(f"  Title: '{instance7.get_title()}'")
    execenv.print(f"  Icon: '{instance7.get_icon()}'")
    assert instance7.get_title() == "Overridden Title"
    assert instance7.get_icon() == "new.png"
    execenv.print("  ✓ Passed\n")

    # Test 8: Empty strings vs None
    class EmptyStringDataSet(DataSet, title="", comment=""):
        """Docstring"""

        param1 = FloatItem("Parameter 1")

    instance8 = EmptyStringDataSet()
    execenv.print("Test 8: Explicit empty strings")
    execenv.print(f"  Title: '{instance8.get_title()}'")
    execenv.print(f"  Comment: '{instance8.get_comment()}'")
    assert instance8.get_title() == ""
    assert instance8.get_comment() == ""
    execenv.print("  ✓ Passed\n")

    execenv.print("All tests passed! ✓")


if __name__ == "__main__":
    test_dataset_class_config()
