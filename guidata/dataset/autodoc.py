"""
sphinx.ext.autodoc extension for :class:`guidata.dataset.DataSet` and related classes.
"""

import logging
from inspect import Parameter, Signature
from typing import Any, Hashable, Type, Union

from docutils import nodes
from docutils.core import publish_parts
from sphinx.application import Sphinx
from sphinx.ext.autodoc import ClassDocumenter, MethodDocumenter, bool_option
from sphinx.util.docstrings import prepare_docstring
from sphinx.util.docutils import SphinxDirective
from sphinx.util.inspect import getdoc, object_description, stringify_signature
from sphinx.util.typing import stringify_annotation

import guidata.dataset as gds
from guidata.config import _

# _ = lambda x: x

DATAITEMS_NONE_DEFAULT: tuple[type[gds.DataItem], ...] = (
    gds.DictItem,
    gds.FloatArrayItem,
    gds.DateItem,
    gds.FileSaveItem,
    gds.FilesOpenItem,
)


def datasetnote_option(arg: str) -> tuple[bool, int | None]:
    if arg is None:
        return True, None
    try:
        return True, int(arg)
    except ValueError:
        return True, None


def check_item_can_be_documented(dataset: gds.DataSet, item: gds.DataItem) -> None:
    """Checks if an item can be documented depending on its value.

    Args:
        dataset: DataSet instance.
        item: DataItem instance.

    Raises:
        ValueError: If the item has a default value that is not allowed (not hashable).
    """
    value = item.get_value(dataset)

    if isinstance(item, DATAITEMS_NONE_DEFAULT) and not isinstance(value, Hashable):
        raise ValueError(
            f"Item '{item.get_name()}' from {dataset.__class__.__name__} has a "
            f"default value of type {type(value)} = {value} which is not allowed. "
            "Default value should be an immutable type."
        )


def document_choice_item(item: gds.ChoiceItem) -> str:
    """Additional documentation for ChoiceItem containing the available choices.

    Args:
        item: ChoiceItem to document.

    Returns:
        Additional choice documentation.
    """
    available_choices = item.get_prop("data", "choices")
    str_choices = ", ".join(object_description(key) for key, *_ in available_choices)
    doc = _("Single choice from: %s.") % str_choices
    return doc


def document_multiple_choice_item(item: gds.MultipleChoiceItem) -> str:
    """Additional documentation for MultipleChoiceItem containing the available choices.

    Args:
        item: ChoiceItem to document.

    Returns:
        Additional choice documentation.
    """
    available_choices = item.get_prop("data", "choices")
    str_choices = ", ".join(object_description(key) for key, *_ in available_choices)
    doc = _("Multiple choice from: %s.") % str_choices
    return doc


def escape_docline(line: str) -> str:
    """Escape a line of documentation.

    Args:
        line: Line of documentation.

    Returns:
        Escaped line of documentation.
    """
    return line.replace("*", "\\*").replace("\n", "").replace("\r", "")


def is_label_redundant(label: str, item_name: str) -> bool:
    """Check if the label is redundant with the item name.

    Args:
        label: Label to check.
        item_name: Item name to check against.

    Returns:
        True if the label is redundant with the item name, False otherwise.
    """
    item_name = item_name.lower()
    return any(word not in item_name for word in label.split())


class ItemDoc:
    """Wrapper class around a DataItem used to document it."""

    def __init__(self, dataset: gds.DataSet, item: gds.DataItem) -> None:
        self.item = item

        check_item_can_be_documented(dataset, item)

        type_ = item.type
        if not type_:
            type_ = Any
        if isinstance(item, gds.ChoiceItem):
            types = set(type(key) for key, *_ in item.get_prop("data", "choices"))
            if types:
                if len(types) == 1:
                    type_ = types.pop()
                else:
                    type_ = f"Union[{', '.join(t.__name__ for t in types)}]"
            else:
                type_ = Any

        self.type_ = stringify_annotation(type_)

        label = item.get_prop("display", "label")
        if is_label_redundant(label, item.get_name()):
            label = ""
        if len(label) > 0 and not label.endswith("."):
            label += "\\."
        self.label = label

        help_ = item.get_help(dataset).capitalize()

        if isinstance(item, gds.MultipleChoiceItem):
            help_ += document_multiple_choice_item(item)
        elif isinstance(item, gds.ChoiceItem):
            help_ += document_choice_item(item)

        elif len(help_) > 0 and not help_.endswith("."):
            help_ += "\\."
        self.help_ = help_

        self.name = item.get_name()

        self.default = object_description(item.get_value(dataset))

    def to_function_parameter(self) -> str:
        """Convert the item to a parameter docstring (e.g. used for Dataset.create()).

        Returns:
            Formated docstring of the item.
        """
        return escape_docline(
            f"\t{self.name} ({self.type_}): {self.label} "
            f"{self.help_} " + _("Default: %s.") % self.default
        )

    def to_attribute(self) -> str:
        """Convert the item to an attribute used in the DataSet docstring.

        Returns:
            Formated docstring of the item.
        """
        return escape_docline(
            f"\t{self.name} ({type(self.item)}): {self.label} {self.help_} "
            + _("Default: %s.") % self.default
        )


class CreateMethodDocumenter(MethodDocumenter):
    """Custom MethodDocumented specific to DataSet.create() method."""

    objtype = "_dataset_create"
    directivetype = MethodDocumenter.objtype
    priority = 10 + MethodDocumenter.priority
    option_spec = dict(MethodDocumenter.option_spec)
    parent: type[gds.DataSet]

    @classmethod
    def can_document_member(cls, member, membername, isattr, parent):
        """Override the parent method to only document the DataSet.create() method."""
        try:
            return issubclass(parent, gds.DataSet) and membername == "create"
        except TypeError:
            return False

    def format_signature(self, **kwargs: Any) -> str:
        """Override the parent method to dynamically generate a signature for the parent
        DataSet.create() method depending on the DataItem of the DatSet."""
        instance = self.parent()
        params = [
            Parameter(
                item.get_name(),
                Parameter.POSITIONAL_OR_KEYWORD,
                annotation=ItemDoc(instance, item).type_,
            )
            for item in instance.get_items()
        ]
        sig = Signature(parameters=params, return_annotation=self.parent)
        return stringify_signature(sig, **kwargs)

    def get_doc(self) -> list[list[str]]:
        """Override the parent method to dynamically generate a docstring for the create
        method depending on the DataItem of the DatSet.

        Returns:
            list of docstring lines.
        """
        self.object.__annotations__["return"] = self.parent
        docstring_lines = [
            _(
                "Returns a new instance of %s with the fields set to "
                "the given values."
            )
            % self.parent.__name__,
            "",
            "Args:",
        ]

        dataset = self.parent()
        for item in dataset.get_items():
            docstring_lines.append(ItemDoc(dataset, item).to_function_parameter())

        docstring_lines.extend(
            ("", "Returns:", _("\tNew instance of %s.") % self.parent.__name__)
        )
        docstring = prepare_docstring(
            "\n".join(docstring_lines),
            tabsize=self.directive.state.document.settings.tab_width,
        )
        return [docstring]


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
            "shownote": datasetnote_option,
        }
    )
    object: Type[gds.DataSet]

    @classmethod
    def can_document_member(cls, member, membername, isattr, parent) -> bool:
        """Override the parent method to only document DataSet classes."""
        try:
            return issubclass(member, gds.DataSet)
        except TypeError:
            return False

    def format_signature(self, **kwargs) -> str:
        """Override the parent method to dynamically generate a signature for the
        DataSet class depending on the DataItem of the DatSet and if the 'showsig'
        option is set.

        Returns:
            Formated signature of the DataSet class.
        """
        if self.options.get("showsig", False):
            return super().format_signature(**kwargs)
        return ""

    def get_doc(self) -> list[list[str]]:
        """Override the parent method to dynamically generate a docstring for the
        DataSet class depending on the DataItem of the DatSet. DataSet attributes
        (DataItems) are documented in the docstring if the 'showattr' option is used.

        Returns:
            Docstring lines.
        """
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
            dataset = self.object()
            for item in dataset.get_items():
                docstring_lines.append(ItemDoc(dataset, item).to_attribute())

        return [
            prepare_docstring(
                "\n".join(docstring_lines),
                tabsize=self.directive.state.document.settings.tab_width,
            )
        ]

    def add_content(self, more_content: Any | None) -> None:
        """Override the parent method to hide the create method documentation if the
        'hidecreate' option is used. Also add a datasetnote directive if the
        'shownote' option is used.

        Args:
            more_content: Additional content to show/hide.
        """
        super().add_content(more_content)

        if not self.options.get("hidecreate", False):
            fullname = (
                self.object.__module__ + "." + self.object.__qualname__ + ".create"
            )
            method_documenter = CreateMethodDocumenter(
                self.directive, fullname, indent=self.content_indent
            )
            method_documenter.generate(more_content=more_content)

        show_note, example_lines = self.options.get("shownote", (False, None))
        if show_note:
            self.add_line(
                ".. datasetnote:: "
                f"{self.object.__module__ + '.' + self.object.__qualname__} "
                f"{example_lines or ''}",
                self.get_sourcename(),
            )


class DatasetNoteDirective(SphinxDirective):
    """Custom directive to add a note about how to instanciate and modify a DataSet
    class."""

    required_arguments = 1  # the class name is a required argument
    optional_arguments = 1  # the number of example lines to display is optional
    final_argument_whitespace = True
    has_content = True

    def run(self):
        """Run the directive.

        Returns:
            list of returned nodes.
        """
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
            logging.error(f"Failed to import class {class_name}: {e}")
            instance_str = _("Failed to import class %s") % class_name
            note_node = nodes.error(instance_str)
            return [note_node]

        # Create an instance of the class and get its string representation
        instance = cls()
        instance_str = str(instance)
        items = instance.get_items()

        formated_args = ", ".join(
            f"{item.get_name()}={object_description(item.get_value(instance))}"
            for item in instance.get_items()
        )
        note_node = nodes.note()
        paragraph1 = nodes.paragraph()
        paragraph1 += nodes.Text(_("To instanciate a new "))
        paragraph1 += nodes.literal(text=cls.__name__)
        paragraph1 += nodes.Text(
            _(" , you can use the create() classmethod like this:")
        )
        paragraph1 += nodes.literal_block(
            text=f"{cls.__name__}.create({formated_args})", language="python"
        )

        note_node += paragraph1

        paragraph2 = nodes.paragraph()
        paragraph2 += nodes.Text(_("You can also first instanciate a default "))
        paragraph2 += nodes.literal(text=cls.__name__)
        paragraph2 += nodes.Text(_(" and then set the fields like this:"))

        example_lines = min(len(items), example_lines) if example_lines else len(items)
        code_lines = [
            f"dataset = {cls.__name__}()",
            *(
                f"dataset.{items[i].get_name()} = "
                f"{object_description(items[i].get_value(instance))}"
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
