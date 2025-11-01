"""Test ChoiceItem serialization with tuple values.

This is a regression test for the tuple/list issue in JSON serialization.
"""

import guidata.dataset as gds


class TupleChoiceParam(gds.DataSet):
    """Test parameter with tuple choices."""

    reference_levels = gds.ChoiceItem(
        "Reference levels",
        [
            ((5, 95), "5% - 95%"),
            ((10, 90), "10% - 90%"),
            ((20, 80), "20% - 80%"),
        ],
        default=(10, 90),
    )


def test_choice_item_tuple_serialization():
    """Test that ChoiceItem with tuple values survives JSON serialization.

    This is a regression test for the issue where JSON serialization converts
    tuples to lists, which then fail validation when deserializing.
    """
    # Create a parameter with a tuple choice
    param = TupleChoiceParam()
    assert param.reference_levels == (10, 90)

    # Serialize to JSON
    json_str = gds.dataset_to_json(param)

    # Deserialize from JSON
    # This should work even though JSON converts tuples to lists
    param2 = gds.json_to_dataset(json_str)

    # Verify the value is restored correctly
    # Note: After deserialization, it might be a list, but validation should accept it
    assert param2.reference_levels == [10, 90] or param2.reference_levels == (10, 90)


def test_choice_item_tuple_vs_list_validation():
    """Test that ChoiceItem validation accepts tuples and lists with same content."""
    param = TupleChoiceParam()

    # Setting with a tuple should work
    param.reference_levels = (20, 80)
    assert param.reference_levels == (20, 80)

    # Setting with a list with same content should also work (after our fix)
    param.reference_levels = [10, 90]
    assert param.reference_levels == [10, 90] or param.reference_levels == (10, 90)


if __name__ == "__main__":
    test_choice_item_tuple_serialization()
    test_choice_item_tuple_vs_list_validation()
    print("All tests passed!")
