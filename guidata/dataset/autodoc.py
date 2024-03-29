"""
sphinx.ext.autodoc extension for :class:`guidata.dataset.DataSet` and related classes.
"""

import logging
from typing import Any, Type

from docutils import nodes
from docutils.nodes import note, paragraph
from docutils.parsers.rst.roles import set_classes
from docutils.statemachine import StringList, ViewList
from sphinx.application import Sphinx
from sphinx.ext.autodoc import (
    ClassDocumenter,
    MethodDocumenter,
    ObjectMember,
    bool_option,
)
from sphinx.util.docstrings import prepare_docstring
from sphinx.util.inspect import getdoc
from sphinx.util.nodes import nested_parse_with_titles

import guidata.dataset as gds
from guidata import __version__ as guidata_version
from guidata.dataset.autodoc_method import CreateMethodDocumenter
from guidata.dataset.note_directive import DatasetNoteDirective


def datasetnote_option(arg: str) -> tuple[bool, int | None]:
    if arg is None:
        return True, None
    try:
        return True, int(arg)
    except ValueError:
        return True, None


class DataSetDocumenter(ClassDocumenter):
    """
    Specialized Documenter subclass for DataSet classes.
    """

    objtype = "dataset"
    directivetype = ClassDocumenter.objtype
    priority = 10 + ClassDocumenter.priority
    option_spec = dict(ClassDocumenter.option_spec)
    option_spec.update(
        {
            "showattr": bool_option,
            "hidecreate": bool_option,
            "showsig": bool_option,
            "datasetnote": datasetnote_option,
        }
    )
    object: Type[gds.DataSet]

    @classmethod
    def can_document_member(cls, member, membername, isattr, parent):
        try:
            return issubclass(member, gds.DataSet)
        except TypeError:
            return False

    def format_signature(self, **kwargs) -> str:
        if self.options.get("showsig", False):
            return super().format_signature(**kwargs)
        return ""

    def get_doc(self):
        first_line = getdoc(
            self.object,
            self.get_attr,
            self.config.autodoc_inherit_docstrings,
            self.object,
        )

        docstring_lines = [
            first_line or "",
        ]
        if self.options.get("showattr", False):
            docstring_lines.extend(("", "Attributes:"))
            instance = self.object()
            for item in instance.get_items():
                type_ = item.type
                if not type_:
                    type_ = Any

                label = item.get_prop("display", "label")
                if len(label) > 0 and not label.endswith("."):
                    label += "."

                help_ = item.get_help(instance)
                if len(help_) > 0 and not help_.endswith("."):
                    help_ += "."

                docstring_lines.append(
                    f"\t{item.get_name()} ({type(item)}): {label} {help_} "
                    f"Default: {item._default}"
                )

        return [
            prepare_docstring(
                "\n".join(docstring_lines),
                tabsize=self.directive.state.document.settings.tab_width,
            )
        ]

    def add_content(self, more_content: Any | None) -> None:
        super().add_content(more_content)

        if not self.options.get("hidecreate", False):
            fullname = (
                self.object.__module__ + "." + self.object.__qualname__ + ".create"
            )
            method_documenter = CreateMethodDocumenter(
                self.directive, fullname, indent=self.content_indent
            )
            method_documenter.generate(more_content=more_content)

        show_note, example_lines = self.options.get("datasetnote", (False, None))
        if show_note:
            # logging.warning("Note option is deprecated. Use datasetnote instead.")
            self.add_line(
                f".. datasetnote:: {self.object.__module__ + '.' + self.object.__qualname__} {example_lines or ''}",
                self.get_sourcename(),
            )


def setup(app: Sphinx) -> None:
    """Setup extension"""
    app.setup_extension("sphinx.ext.autodoc")
    app.add_autodocumenter(DataSetDocumenter)
