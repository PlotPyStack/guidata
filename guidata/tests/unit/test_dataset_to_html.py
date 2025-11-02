# -*- coding: utf-8 -*-
#
# Licensed under the terms of the BSD 3-Clause
# (see guidata/LICENSE for details)

"""
Unit tests for DataSet.to_html() method

Tests various scenarios for HTML generation including:
- Basic dataset with title and comment
- BoolItem with different text/label combinations
- Various data types (string, int, float, etc.)
- Edge cases (empty datasets, None values, etc.)
"""

import datetime

import pytest

import guidata.dataset as gds


class SimpleDataset(gds.DataSet):
    """Simple dataset for testing HTML output"""

    name = gds.StringItem("Name", default="Test Name")
    value = gds.IntItem("Value", default=42)
    enabled = gds.BoolItem("Enabled option")


class ComplexDataset(gds.DataSet):
    """Dataset with various item types and BoolItem configurations"""

    # Basic items
    text = gds.StringItem("Text field", default="Hello World")
    number = gds.FloatItem("Number", default=3.14159)
    date = gds.DateItem("Date", default=datetime.date(2023, 1, 1))

    # BoolItem variations
    bool_simple = gds.BoolItem("Simple boolean")
    bool_with_label = gds.BoolItem("Boolean text", "Label name")
    bool_enabled = gds.BoolItem("Feature enabled", default=True)
    bool_disabled = gds.BoolItem("Feature disabled", default=False)

    # None value test
    optional_text = gds.StringItem("Optional", default=None, allow_none=True)


class DatasetWithComment(
    gds.DataSet,
    comment=(
        "This is the comment that should appear in lighter blue\nin the HTML output."
    ),
):
    """A dataset with title and comment"""

    param = gds.StringItem("Parameter", default="value")


class EmptyDataset(gds.DataSet):
    """Empty dataset for edge case testing"""

    pass


def test_simple_dataset_to_html():
    """Test basic HTML generation for simple dataset"""
    dataset = SimpleDataset()
    html = dataset.to_html()

    # Check title is present and styled (uses first line of docstring)
    expected_title = (
        '<u><b style="color: #5294e2">Simple dataset for testing HTML output</b></u>'
    )
    assert expected_title in html

    # Check table structure
    assert '<table border="0">' in html
    assert "</table>" in html

    # Check item names and values are present
    assert "Name:" in html
    assert "Test Name" in html
    assert "Value:" in html
    assert "42" in html

    # Check checkbox for boolean
    assert "Enabled option:" in html
    assert "☐" in html  # Unchecked by default


def test_complex_dataset_to_html():
    """Test HTML generation for dataset with various item types"""
    dataset = ComplexDataset()
    html = dataset.to_html()

    # Check title (uses first line of docstring)
    expected_title = (
        '<u><b style="color: #5294e2">'
        "Dataset with various item types and BoolItem configurations"
        "</b></u>"
    )
    assert expected_title in html  # Check basic items
    assert "Text field:" in html
    assert "Hello World" in html
    assert "Number:" in html
    assert "3.14159" in html

    # Check BoolItem variations
    assert "Simple boolean:" in html
    assert "☐" in html  # Default false

    # Check BoolItem with label - should show "Label name: ☐ Boolean text"
    assert "Label name:" in html and "☐ Boolean text" in html

    # Check enabled/disabled states
    assert "Feature enabled:" in html
    assert "☑" in html  # Should be checked
    assert "Feature disabled:" in html
    # Should have both checked and unchecked boxes

    # Check None value handling
    assert "Optional:" in html
    assert "-" in html  # None should be displayed as '-'


def test_dataset_with_comment():
    """Test HTML generation for dataset with title and comment"""
    dataset = DatasetWithComment()
    html = dataset.to_html()

    # Check title (uses first line of docstring)
    expected_title = (
        '<u><b style="color: #5294e2">A dataset with title and comment</b></u>'
    )
    assert expected_title in html

    # Check comment is present and styled with the lighter blue
    assert '<span style="color: #5294e2">' in html
    assert "This is the comment that should appear in lighter blue" in html


def test_bool_item_combinations():
    """Test various BoolItem text/label combinations"""

    class BoolTestDataset(gds.DataSet):
        # Only text, no label
        bool1 = gds.BoolItem("Just text")
        # Both text and label
        bool2 = gds.BoolItem("Text part", "Label part")
        # Empty text, only label (edge case)
        bool3 = gds.BoolItem("", "Only label")

    dataset = BoolTestDataset()
    dataset.bool1 = True
    dataset.bool2 = False
    dataset.bool3 = True

    html = dataset.to_html()

    # Check first boolean (text only)
    assert "Just text:" in html
    assert "☑" in html

    # Check second boolean (text and label)
    assert "Label part" in html and "☐ Text part" in html

    # Check third boolean (label only)
    assert "Only label:" in html


def test_empty_dataset():
    """Test HTML generation for empty dataset"""
    dataset = EmptyDataset()
    html = dataset.to_html()

    # Should have title (uses first line of docstring)
    expected_title = (
        '<u><b style="color: #5294e2">Empty dataset for edge case testing</b></u>'
    )
    assert expected_title in html  # Should indicate no items
    assert "No items to display" in html


def test_dataset_with_none_values():
    """Test handling of None values in various item types"""

    class NoneTestDataset(gds.DataSet):
        text_none = gds.StringItem("Text", default=None, allow_none=True)
        int_none = gds.IntItem("Integer", default=None, allow_none=True)
        bool_none = gds.BoolItem("Boolean", default=None, allow_none=True)

    dataset = NoneTestDataset()
    html = dataset.to_html()

    # All None values should display as '-'
    # Count occurrences of '-' in table cells
    html_lines = html.split("\n")
    dash_count = sum(line.count('">-</td>') for line in html_lines)
    assert dash_count >= 2  # At least text and int should show '-'


def test_html_structure_and_styling():
    """Test the HTML structure and CSS styling"""
    dataset = SimpleDataset()
    html = dataset.to_html()

    # Check CSS styles
    assert "text-align: right" in html
    assert "text-align: left" in html
    assert "vertical-align: top" in html
    assert "padding-left: 10px" in html

    # Check table structure
    assert html.count("<tr>") == html.count("</tr>")
    assert html.count("<td") == html.count("</td>")

    # Should be well-formed HTML table
    assert "<table" in html
    assert "</table>" in html


def test_checkbox_characters():
    """Test that proper checkbox characters are used"""

    class CheckboxDataset(gds.DataSet):
        checked = gds.BoolItem("Checked", default=True)
        unchecked = gds.BoolItem("Unchecked", default=False)

    dataset = CheckboxDataset()
    html = dataset.to_html()

    # Should contain both checked and unchecked boxes
    assert "☑" in html  # Checked box
    assert "☐" in html  # Unchecked box


def visualize_html_in_browser():
    """Generate and open HTML visualization in web browser for manual testing"""
    import datetime
    import os
    import tempfile
    import webbrowser

    # Create a comprehensive dataset for visualization
    class VisualizationDataset(gds.DataSet):
        """HTML Visualization Test Dataset

        This dataset contains various item types to demonstrate
        the HTML output formatting capabilities.
        """

        # Basic data types
        name = gds.StringItem("Full Name", default="John Smith")
        age = gds.IntItem("Age", default=35)
        salary = gds.FloatItem("Annual Salary", default=75000.50)
        start_date = gds.DateItem("Start Date", default=datetime.date(2020, 3, 15))
        birth_datetime = gds.DateTimeItem(
            "Birth Date/Time", default=datetime.datetime(1988, 7, 22, 14, 30)
        )

        # BoolItem variations to test checkbox rendering
        newsletter = gds.BoolItem("Subscribe to newsletter")
        notifications = gds.BoolItem("Email notifications", "Enable emails")
        premium = gds.BoolItem("Premium membership", default=True)
        marketing = gds.BoolItem("Marketing consent", default=False)

        # Optional fields
        middle_name = gds.StringItem("Middle Name", default=None, allow_none=True)
        phone = gds.StringItem("Phone Number", default="", allow_none=True)

        # Choice items
        department = gds.ChoiceItem(
            "Department",
            [
                ("IT", "Information Technology"),
                ("HR", "Human Resources"),
                ("FIN", "Finance"),
            ],
        )

    # Create and populate dataset
    dataset = VisualizationDataset()
    dataset.newsletter = True
    dataset.notifications = False
    dataset.phone = None

    # Generate complete HTML page
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DataSet to_html() Visualization</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            background-color: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }}
        .demo-section {{
            margin-bottom: 30px;
            padding: 15px;
            border: 1px solid #ddd;
            border-radius: 5px;
        }}
        h1 {{
            color: #333;
            text-align: center;
        }}
        h2 {{
            color: #666;
            border-bottom: 2px solid #eee;
            padding-bottom: 5px;
        }}
        .code {{
            background-color: #f8f8f8;
            padding: 10px;
            border-radius: 4px;
            font-family: 'Courier New', monospace;
            border: 1px solid #ddd;
            overflow-x: auto;
        }}
        .html-output {{
            border: 2px solid #007acc;
            padding: 15px;
            border-radius: 5px;
            background-color: #fafafa;
        }}
    </style>
</head>
<body>
    <h1>DataSet to_html() Method Visualization</h1>

    <div class="container">
        <h2>Dataset Definition</h2>
        <div class="code">
class VisualizationDataset(gds.DataSet):
    \"\"\"HTML Visualization Test Dataset

    This dataset contains various item types to demonstrate
    the HTML output formatting capabilities.
    \"\"\"

    # Basic data types
    name = gds.StringItem("Full Name", default="John Smith")
    age = gds.IntItem("Age", default=35)
    salary = gds.FloatItem("Annual Salary", default=75000.50)

    # BoolItem variations
    newsletter = gds.BoolItem("Subscribe to newsletter")
    notifications = gds.BoolItem("Email notifications", "Enable emails")
    premium = gds.BoolItem("Premium membership", default=True)

    # Optional fields (None values)
    middle_name = gds.StringItem("Middle Name", default=None, allow_none=True)
        </div>
    </div>

    <div class="container">
        <h2>Generated HTML Output</h2>
        <p>The following is the direct output from <code>dataset.to_html()</code>:</p>
        <div class="html-output">
            {dataset.to_html()}
        </div>
    </div>

    <div class="container">
        <h2>Key Features Demonstrated</h2>
        <ul>
            <li><strong>Title and Comment:</strong> Displayed in lighter blue
            (#5294e2) using the first line of the docstring as title</li>
            <li><strong>Two-column Layout:</strong> Item names right-aligned,
            values left-aligned</li>
            <li><strong>BoolItem Checkboxes:</strong> ☑ for True, ☐ for False</li>
            <li><strong>BoolItem Labels:</strong> Shows "Label: Text" format when
            both are provided</li>
            <li><strong>None Values:</strong> Displayed as "-" for better
            readability</li>
            <li><strong>Monospace Font:</strong> Table uses monospace font for
            consistent alignment</li>
        </ul>
    </div>

    <div class="container">
        <h2>Raw HTML Code</h2>
        <p>Raw HTML source code generated by the method:</p>
        <div class="code">
{dataset.to_html().replace("<", "&lt;").replace(">", "&gt;")}
        </div>
    </div>
</body>
</html>"""

    # Write to temporary file
    temp_file_args = {
        "mode": "w",
        "suffix": ".html",
        "delete": False,
        "encoding": "utf-8",
    }
    with tempfile.NamedTemporaryFile(**temp_file_args) as f:
        f.write(html_content)
        temp_file = f.name

    print(f"HTML file created: {temp_file}")
    print("Opening in default web browser...")

    # Open in web browser
    webbrowser.open(f"file://{os.path.abspath(temp_file)}")

    return temp_file


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
    visualize_html_in_browser()
