from inspect import Parameter, Signature
from typing import Any

from sphinx.application import Sphinx
from sphinx.ext.autodoc import MethodDocumenter, stringify_signature
from sphinx.util.docstrings import prepare_docstring

import guidata.dataset as gds


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
                default=item._default,
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

        instance = self.parent()
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
