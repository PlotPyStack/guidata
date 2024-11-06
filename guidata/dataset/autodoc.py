"""
sphinx.ext.autodoc extension for :py:class:`guidata.dataset.DataSet` and related
classes.
"""

from __future__ import annotations

import logging
import re
from inspect import Parameter, Signature
from typing import TYPE_CHECKING, Any, Type

from docutils import nodes
from docutils.statemachine import StringList
from sphinx.ext.autodoc import ClassDocumenter, MethodDocumenter, bool_option
from sphinx.util.docstrings import prepare_docstring
from sphinx.util.docutils import SphinxDirective
from sphinx.util.inspect import getdoc, object_description, stringify_signature
from sphinx.util.nodes import nested_parse_with_titles
from sphinx.util.typing import stringify_annotation

import guidata.dataset as gds
from guidata.config import _

if TYPE_CHECKING:
    from docutils.parsers.rst.states import RSTState, RSTStateMachine
    from sphinx.application import Sphinx

IGNORED_AUTO_HELP: tuple[str, ...] = (_("integer"), _("float"), _("string"))


# Create a combined regex pattern of all keys in the dictionary
REPLACABLE_HTML_TAGS = {
    "strong": "\\ :strong:`{}`",
    "b": "\\ :strong:`{}`",
    "u": "\\ :underline:`{}`",
    "i": "\\ :emphasis:`{}`",
    "em": "\\ :emphasis:`{}`",
    "sub": "\\ :subscript:`{}`",
    "sup": "\\ :superscript:`{}`",
    "span": "{}",
    "code": "\\ :code:`{}`",
}

# Case of self-closing tags can be handled by adding a group "(<.+/>)" to the regex
# and handling the cases in the replace_html_tags function or by adding a new dictionary
# entry for specific tags if needed. This could be useful for tags like "<br/>" or
# "<hr/>" or "<a .../>". The current does not handle tag attributes.
# The regex pattern can only match specified tag but could be made generic using the
# following pattern: "<(.+?)>(.*?)</\\1>" and then using rhe dict.get() method in
# replace_html_tags function with an empty pattern.
_tags = "|".join(REPLACABLE_HTML_TAGS.keys())
HTML_TAG_PATTERN = re.compile(f"<({_tags})>(.*?)</\\1>")


def replace_html_tags(match: re.Match):
    """Replace HTML tags with reST directives.

    Args:
        match: Match object.

    Returns:
        New string with reST directives.
    """
    tag = match.group(1)
    value = match.group(2)
    new_string = REPLACABLE_HTML_TAGS[tag].format(value)

    return new_string


def datasetnote_option(arg: str) -> tuple[bool, int | None]:
    """Handles the datasetnote option for the datasetnote directive.

    Args:
        arg: Argument to parse (set after the directive).

    Returns:
        Returns True to signal the option exists and the number of example note_lines to
         display if set else None.
    """
    if arg is None:
        return True, None
    try:
        return True, int(arg)
    except ValueError:
        return True, None


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


def get_auto_help(item: gds.DataItem, dataset: gds.DataSet) -> str:
    """Get the auto-generated help for a DataItem.

    Args:
        item: DataItem to get the help from.

    Returns:
        Auto-generated help for the DataItem.
    """
    auto_help = item.get_auto_help(dataset).rstrip(" .")
    if not auto_help or auto_help in IGNORED_AUTO_HELP:
        return ""
    return capitalize_sentences(auto_help) + "\\."


def get_choice_help(item: gds.DataItem) -> str:
    """Get the choice help for a DataItem if it is a ChoiceItem or MultipleChoiceItem.

    Args:
        item: DataItem to get the choice help from.

    Returns:
        Choice help for the DataItem. If the DataItem is not a ChoiceItem or
        MultipleChoiceItem, an empty string is returned.
    """
    choice_help = ""
    if isinstance(item, gds.MultipleChoiceItem):
        choice_help = document_multiple_choice_item(item)
    elif isinstance(item, gds.ChoiceItem):
        choice_help = document_choice_item(item)
    return choice_help


def escape_docline(line: str) -> str:
    """Escape a line of documentation.

    Args:
        line: Line of documentation.

    Returns:
        Escaped line of documentation.
    """
    return line.replace("*", "\\*").replace("\n", " ")


def is_label_redundant(label: str, item_name: str) -> bool:
    """Check if the label is redundant with the item name.

    Args:
        label: Label to check.
        item_name: Item name to check against.

    Returns:
        True if the label is redundant with the item name, False otherwise.
    """
    item_name = item_name.lower()
    return not any(word.strip() not in item_name for word in label.lower().split())


def capitalize_sentences(text: str) -> str:
    """Capitalize each sentence in a text.

    Args:
        text: Text to capitalize.

    Returns:
        Capitalized text.
    """
    sentences = re.split("(?<=[.!?]) +", text)
    capitalized_sentences = [sentence.capitalize() for sentence in sentences]

    return " ".join(capitalized_sentences)


class ItemDoc:
    """Wrapper class around a DataItem used to document it."""

    def __init__(self, dataset: gds.DataSet, item: gds.DataItem) -> None:
        self.item = item
        self.item_type = stringify_annotation(type(item))

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

        label = re.sub(HTML_TAG_PATTERN, replace_html_tags, label)
        self.label = label

        help_ = item._help or ""
        help_ = capitalize_sentences(help_)
        if len(help_) > 0 and not help_.endswith("."):
            help_ += "\\."

        auto_help = get_auto_help(item, dataset)
        if auto_help:
            help_ += " " + auto_help

        choice_help = get_choice_help(item)
        if choice_help:
            help_ += " " + choice_help

        self.help_ = help_

        self.name = item.get_name()

        self.default = object_description(item.get_default())

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
            f"\t{self.name} ({self.item_type}): {self.label} {self.help_} "
            + _("Default: %s.") % self.default
        )


class CreateMethodDocumenter(MethodDocumenter):
    """Custom MethodDocumented specific to DataSet.create() method."""

    objtype = "dataset_create"
    directivetype = MethodDocumenter.objtype
    priority = 10 + MethodDocumenter.priority
    option_spec = dict(MethodDocumenter.option_spec)
    parent: type[gds.DataSet]

    @classmethod
    def can_document_member(cls, member, membername, isattr, parent):
        """Override the parent method to only document the DataSet.create() method."""
        is_create_method = (
            membername == "create"
            and isinstance(member, classmethod)
            and issubclass(member.__class__, gds.DataSet)
        )

        return is_create_method

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
            list of docstring note_lines.
        """
        self.object.__annotations__["return"] = self.parent
        docstring_lines = [
            _(
                "Returns a new instance of :py:class:`%s` with the fields set to "
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
            (
                "",
                "Returns:",
                _("\tNew instance of :py:class:`%s`.") % self.parent.__name__,
            )
        )
        docstring = prepare_docstring(
            "\n".join(docstring_lines),
            tabsize=self.directive.state.document.settings.tab_width,
        )

        # return [[html.unescape(s) for s in docstring]]
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
            "hideattr": bool_option,
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
        DataSet class depending on the DataItem of the DatSet. By default the dataset
        attributes are documented but can be hidden using the 'hideattr' option.

        Returns:
            Docstring note_lines.
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
        if not self.options.get("hideattr", False):
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
        source = self.get_sourcename()
        hide_create: bool = self.options.get("hidecreate", False)
        create_method_overwritten = "create" in self.object.__dict__

        if hide_create or self.options.inherited_members and not hide_create:
            if self.options.exclude_members is None:
                self.options["exclude-members"] = set(("create",))
            else:
                self.options["exclude-members"].add("create")

        super().add_content(more_content=more_content)

        if not hide_create and not create_method_overwritten:
            fullname = self.fullname + ".create"
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
                source,
            )


class DatasetNoteDirective(SphinxDirective):
    """Custom directive to add a note about how to instanciate and modify a DataSet
    class."""

    required_arguments = 1  # the class name is a required argument
    optional_arguments = 1  # the number of example note_lines to display is optional
    final_argument_whitespace = True
    has_content = True

    def __init__(
        self,
        name: str,
        arguments: list[str],
        options: dict[str, Any],
        content: StringList,
        lineno: int,
        content_offset: int,
        block_text: str,
        state: RSTState,
        state_machine: RSTStateMachine,
    ) -> None:
        super().__init__(
            name,
            arguments,
            options,
            content,
            lineno,
            content_offset,
            block_text,
            state,
            state_machine,
        )
        self.current_line_offset = self.content_offset

    def add_lines(self, stringlist: StringList, *lines: str) -> None:
        source = self.get_source_info()[0]
        new_offset = self.current_line_offset + 1
        i = new_offset
        for i, line in enumerate(lines, start=new_offset):
            stringlist.append(line, source=source, offset=i)
        new_offset = i
        self.current_line_offset += new_offset

    def add_code_lines(self, stringlist: StringList, *lines: str) -> None:
        source = self.get_source_info()[0]
        new_offset = self.current_line_offset + 1
        tab = " " * self.state.document.settings.tab_width

        stringlist.append("", source=source, offset=new_offset)
        stringlist.append(
            ".. code-block:: python", source=source, offset=new_offset + 2
        )
        stringlist.append("", source=source, offset=new_offset + 3)
        new_offset += 4
        i = new_offset
        for i, line in enumerate(lines, start=new_offset):
            stringlist.append(tab + line, source=source, offset=i)
        new_offset = i + 1
        stringlist.append("", source=source, offset=new_offset)
        self.current_line_offset += new_offset

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

        node = nodes.note()

        # Create a new ViewList instance and add your rst text to it
        source, lineno = self.get_source_info()
        self.current_line_offset = self.content_offset

        note_lines = StringList()
        self.add_lines(
            note_lines,
            _(
                "To instanciate a new :py:class:`%s` dataset, you can use the "
                "classmethod :py:meth:`%s.create()` like this:"
            )
            % (cls.__name__, cls.__name__),
            "",
        )

        self.add_code_lines(
            note_lines,
            f"{cls.__name__}.create({formated_args})",
        )

        self.add_lines(
            note_lines,
            _(
                "You can also first instanciate a default :py:class:`%s` "
                "and then set the fields like this:"
            )
            % cls.__name__,
        )

        example_lines = min(len(items), example_lines) if example_lines else len(items)
        code_lines = [
            f"param = {cls.__name__}()",
            *(
                f"param.{items[i].get_name()} = "
                f"{object_description(items[i].get_value(instance))}"
                for i in range(example_lines)
            ),
        ]

        if len(items) > example_lines:
            code_lines.append("...")
        self.add_code_lines(note_lines, *code_lines)

        nested_parse_with_titles(self.state, note_lines, node)

        return [node]


def setup(app: Sphinx) -> None:
    """Setup extension"""
    app.setup_extension("sphinx.ext.autodoc")
    app.add_autodocumenter(CreateMethodDocumenter)
    app.add_autodocumenter(DataSetDocumenter)
    app.add_directive("datasetnote", DatasetNoteDirective)
