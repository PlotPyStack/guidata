"""
sphinx.ext.autodoc extension for :class:`guidata.dataset.DataSet` and related classes.
"""

from sphinx.application import Sphinx
from sphinx.ext.autodoc import ClassDocumenter, ObjectMember

import guidata.dataset as gds
from guidata import __version__ as guidata_version

__version__ = guidata_version


class DataSetDocumenter(ClassDocumenter):
    """
    Specialized Documenter subclass for DataSet classes.
    """

    objtype = "dataset"
    directivetype = ClassDocumenter.objtype
    priority = 10 + ClassDocumenter.priority
    option_spec = dict(ClassDocumenter.option_spec)

    @classmethod
    def can_document_member(cls, member, membername, isattr, parent):
        try:
            return issubclass(member, gds.DataSet)
        except TypeError:
            return False

    def get_object_members(self, want_all):
        check, members = super().get_object_members(want_all)
        existing_member_names = {m.__name__ for m in members}
        instance: gds.DataSet = self.object()
        print(f"Inspecting {self.object_name} members")
        for item in instance.get_items():
            if item.get_name() not in existing_member_names:
                existing_member_names.add(item.get_name())
                print(f"Adding {item.get_name()} to {self.object_name}")
                members.append(ObjectMember(item.get_name(), item))
        return check, members

    def add_content(
        self,
        more_content,
    ) -> None:
        super().add_content(more_content)
        source_name = self.get_sourcename()
        instance: gds.DataSet = self.object()
        self.add_line("", source_name)
        for item in instance.get_items():
            name = item.get_name()
            helptxt = item.get_help(instance)
            default = item.get_string_value(instance)
            typetxt = "Any"
            if hasattr(item, "type"):
                typetxt = item.type.__name__
            self.add_line(f"**{name}**: {typetxt}={default} ({helptxt})", source_name)
            self.add_line("", source_name)


def setup(app: Sphinx) -> None:
    """Setup extension"""
    app.setup_extension("sphinx.ext.autodoc")
    app.add_autodocumenter(DataSetDocumenter)
