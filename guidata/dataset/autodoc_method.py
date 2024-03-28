import importlib
from typing import Any

from docutils import nodes
from docutils.parsers.rst import Directive
from docutils.statemachine import ViewList
from sphinx.application import Sphinx
from sphinx.ext.autodoc import MethodDocumenter
from sphinx.util.docstrings import prepare_docstring
from sphinx.util.inspect import getdoc
from sphinx.util.nodes import nested_parse_with_titles

import guidata.dataset as gds


class CreateMethodDocumenter(MethodDocumenter):
    objtype = "_create_method"
    directivetype = MethodDocumenter.objtype
    priority = 10 + MethodDocumenter.priority
    option_spec = dict(MethodDocumenter.option_spec)

    @classmethod
    def can_document_member(cls, member, membername, isattr, parent):
        try:
            return issubclass(member, gds.DataSet)
        except TypeError:
            return False

    def get_doc(self):
        self.object.__annotations__["return"] = self.parent
        docstring_lines = [
            f"Returns a new instance of {self.parent.__name__} with the fields set to "
            "the given values.",
            "",
            "Args:",
        ]

        instance = self.parent()
        for item in instance.get_items():
            type_ = item.type
            if not type_:
                type_ = Any

            label = item.get_prop("display", "label")
            if not label.endswith("."):
                label += "."
            help_ = item._help

            if not help_.endswith("."):
                help_ += "."

            docstring_lines.append(
                f"\t{item.get_name()} ({type_.__name__}): {label} {help_} "
                f"Default: {item._default}"
            )

        docstring_lines.extend(
            ("Returns:", "", f"\tNew instance of {self.parent.__name__}")
        )
        return [
            prepare_docstring(
                "\n".join(docstring_lines),
                tabsize=self.directive.state.document.settings.tab_width,
            )
        ]


def setup(app: Sphinx):
    app.setup_extension("sphinx.ext.autodoc")
    app.add_autodocumenter(CreateMethodDocumenter)
