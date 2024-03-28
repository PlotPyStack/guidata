from docutils import nodes
from docutils.parsers.rst import Directive
from sphinx.util import logging
from sphinx.util.docutils import SphinxDirective

logger = logging.getLogger(__name__)

from typing import Type

import guidata.dataset as gds
from guidata import __version__


class datasetnoteDirective(SphinxDirective):
    required_arguments = 1  # the class name is a required argument
    optional_arguments = 0
    final_argument_whitespace = True
    has_content = True

    def run(self):
        class_name = self.arguments[0]
        try:
            # Try to import the class
            module_name, class_name = class_name.rsplit(".", 1)
            module = __import__(module_name, fromlist=[class_name])
            cls: Type[gds.DataSet] = getattr(module, class_name)

            # Create an instance of the class and get its string representation
            instance = cls()
            instance_str = str(instance)
            formated_args = ", ".join(
                f"{item.get_name()}={item._default}" for item in instance.get_items()
            )

            note_node = nodes.note()
            paragraph1 = nodes.paragraph()
            paragraph1 += nodes.Text("To instanciate a new ")
            paragraph1 += nodes.literal(text=f"{cls.__name__}")
            paragraph1 += nodes.Text(" , you can use the create classmethod like this:")
            paragraph1 += nodes.literal_block(
                text=f"{cls.__name__}.create({formated_args})", language="python"
            )
            note_node += paragraph1

            paragraph2 = nodes.paragraph()
            paragraph2 += nodes.Text("You can also first instanciate a default ")
            paragraph2 += nodes.literal(text=f" {cls.__name__}")
            paragraph2 += nodes.Text(" and then set the fields like this:")
            paragraph2 += nodes.literal_block(
                text=f"dataset = {cls.__name__}()\n"
                f"dataset.{instance.get_items()[0].get_name()} = new_value\n"
                f"instance.{instance.get_items()[1].get_name()} = new_value\n"
                f"...",
                language="python",
            )
            note_node += paragraph2

        except Exception as e:
            logger.warning(f"Failed to import class {class_name}: {e}")
            instance_str = f"Failed to import class {class_name}"
            note_node = nodes.error(instance_str)
        # Create a note node

        return [note_node]


def setup(app):
    app.add_directive("datasetnote", datasetnoteDirective)

    return {
        "version": __version__,
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
