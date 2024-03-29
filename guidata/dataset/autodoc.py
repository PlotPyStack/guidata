"""
sphinx.ext.autodoc extension for :class:`guidata.dataset.DataSet` and related classes.
"""

import logging
from inspect import Parameter, Signature
from typing import Any, Type

from docutils import nodes
from sphinx.application import Sphinx
from sphinx.ext.autodoc import (
    ClassDocumenter,
    MethodDocumenter,
    bool_option,
    stringify_signature,
    object_description,
)
from sphinx.util.docstrings import prepare_docstring
from sphinx.util.docutils import SphinxDirective
from sphinx.util.inspect import getdoc

import guidata.dataset as gds

logger = logging.getLogger(__name__)

# These item types must not have a default value other than None whild documenting
DATAITEMS_NONE_DEFAULT = (gds.DictItem, gds.FloatArrayItem, gds.DateItem)


def datasetnote_option(arg: str) -> tuple[bool, int | None]:
    if arg is None:
        return True, None
    try:
        return True, int(arg)
    except ValueError:
        return True, None


def check_item_can_be_documented(instance: gds.DataSet, item: gds.DataItem) -> None:
    value = item.get_value(instance)
    if isinstance(item, DATAITEMS_NONE_DEFAULT) and value is not None:
        raise ValueError(
            f"Item {item.get_name()} has a default value of {value} which is not None."
        )


def document_items(cls: Type[gds.DataSet]) -> str:
    docstring_lines = []
    instance = cls()
    for item in instance.get_items():
        # check_item_can_be_documented(instance, item)

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
            f"\t{item.get_name()} ({type_.__name__}): {label} {help_} "
            f"Default: {object_description(item.get_value(instance))}."
        )
    return "\n".join(docstring_lines)


class CreateMethodDocumenter(MethodDocumenter):
    objtype = "_create_method"
    directivetype = MethodDocumenter.objtype
    priority = 10 + MethodDocumenter.priority
    option_spec = dict(MethodDocumenter.option_spec)
    parent: type[gds.DataSet]

    @classmethod
    def can_document_member(cls, member, membername, isattr, parent):
        try:
            return issubclass(parent, gds.DataSet) and membername == "create"
        except TypeError:
            return False

    def format_signature(self, **kwargs: Any) -> str:
        instance = self.parent()
        params = [
            Parameter(
                item.get_name(),
                Parameter.POSITIONAL_OR_KEYWORD,
                annotation=item.type,
                # default=item.get_string_value(instance),
            )
            for item in instance.get_items()
        ]
        sig = Signature(parameters=params, return_annotation=self.parent)
        return stringify_signature(sig, **kwargs)

    def get_doc(self):
        self.object.__annotations__["return"] = self.parent
        docstring_lines = [
            f"Returns a new instance of {self.parent.__name__} with the fields set to "
            "the given values.",
            "",
            "Args:",
        ]

        docstring_lines.append(document_items(self.parent))

        docstring_lines.extend(
            ("Returns:", "", f"\tNew instance of {self.parent.__name__}")
        )
        return [
            prepare_docstring(
                "\n".join(docstring_lines),
                tabsize=self.directive.state.document.settings.tab_width,
            )
        ]


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
                ".. datasetnote:: "
                f"{self.object.__module__ + '.' + self.object.__qualname__} "
                f"{example_lines or ''}",
                self.get_sourcename(),
            )


class DatasetNoteDirective(SphinxDirective):
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
            f"{item.get_name()}={item.get_string_value(instance)}"
            for item in instance.get_items()
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

        example_lines = min(len(items), example_lines) if example_lines else len(items)
        code_lines = [
            f"dataset = {cls.__name__}()",
            *(
                f"dataset.{items[i].get_name()} = {items[i].get_string_value(instance)}"
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


def setup(app: Sphinx) -> None:
    """Setup extension"""
    app.setup_extension("sphinx.ext.autodoc")
    app.add_autodocumenter(CreateMethodDocumenter)
    app.add_autodocumenter(DataSetDocumenter)
    app.add_directive("datasetnote", DatasetNoteDirective)
