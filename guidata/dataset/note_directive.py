#
# Licensed under the terms of the BSD 3-Clause
# (see guidata/LICENSE for details)

"""Sphinx directive to display a note about how to instanciate a dataset class"""

from __future__ import annotations

from typing import TYPE_CHECKING, Type

from docutils import nodes
from sphinx.util import logging
from sphinx.util.docutils import SphinxDirective

import guidata.dataset as gds
from guidata import __version__

if TYPE_CHECKING:
    import sphinx.application

logger = logging.getLogger(__name__)


class DatasetNoteDirective(SphinxDirective):
    """Directive to display a note about how to instanciate a dataset class"""

    required_arguments = 1  # the class name is a required argument
    optional_arguments = 1  # the number of example lines to display is optional
    final_argument_whitespace = True
    has_content = True

    def run(self):
        class_name = self.arguments[0]

        example_lines: int | None
        if len(self.arguments) > self.required_arguments:
            example_lines = int(self.arguments[self.required_arguments])
        else:
            example_lines = None

        cls: Type[gds.DataSet]
        try:
            # Try to import the class
            module_name, class_name = class_name.rsplit(".", 1)
            module = __import__(module_name, fromlist=[class_name])
            cls = getattr(module, class_name)

        except Exception as e:
            logger.warning(f"Failed to import class {class_name}: {e}")
            instance_str = f"Failed to import class {class_name}"
            note_node = nodes.error(instance_str)
            return [note_node]

        # Create an instance of the class and get its string representation
        instance = cls()
        instance_str = str(instance)
        items = instance.get_items()

        formated_args = ", ".join(
            f"{item.get_name()}={item._default}" for item in instance.get_items()
        )
        note_node = nodes.note()
        paragraph1 = nodes.paragraph()
        paragraph1 += nodes.Text("To instanciate a new ")
        paragraph1 += nodes.literal(text=f"{cls.__name__}")
        paragraph1 += nodes.Text(" , you can use the create() classmethod like this:")
        paragraph1 += nodes.literal_block(
            text=f"{cls.__name__}.create({formated_args})", language="python"
        )
        note_node += paragraph1

        paragraph2 = nodes.paragraph()
        paragraph2 += nodes.Text("You can also first instanciate a default ")
        paragraph2 += nodes.literal(text=f" {cls.__name__}")
        paragraph2 += nodes.Text(" and then set the fields like this:")

        example_lines = min(len(items), example_lines) if example_lines else len(items)
        code_lines = [
            f"dataset = {cls.__name__}()",
            *(
                f"dataset.{items[i].get_name()} = {repr(items[i]._default)}"
                for i in range(example_lines)
            ),
        ]
        if len(items) > example_lines:
            code_lines.append("...")

        paragraph2 += nodes.literal_block(
            text="\n".join(code_lines),
            language="python",
        )
        note_node += paragraph2

        # Create a note node

        return [note_node]


def setup(app: sphinx.application.Sphinx) -> dict[str, object]:
    """Initialize the Sphinx extension"""
    app.add_directive("datasetnote", DatasetNoteDirective)

    return {
        "version": __version__,
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
