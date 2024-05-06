# -*- coding: utf-8 -*-
#
# Licensed under the terms of the BSD 3-Clause
# (see guidata/LICENSE for details)

"""
Test JSON I/O
-------------

Testing various use cases of JSON I/O:

* Serialize and deserialize a data model, handling versioning and compatibility breaks.
"""

from __future__ import annotations

import atexit
import os
import os.path as osp

from guidata.env import execenv
from guidata.io import JSONReader, JSONWriter


# The following class represents a data model that we want to serialize and deserialize.
# This is the first version of the data model.
class MyDataObjectV10:
    """Data object version 1.0"""

    def __init__(self, title: str = "") -> None:
        self.title = title

    def __str__(self) -> str:
        """Return the string representation of the object"""
        return f"{self.__class__.__name__}({self.title})"

    def serialize(self, writer: JSONWriter) -> None:
        """Serialize the data model to an JSON file"""
        writer.write(self.title, "title")

    def deserialize(self, reader: JSONReader) -> None:
        """Deserialize the data model from an JSON file"""
        self.title = reader.read("title")


class MyDataModelV10:
    """Data model version 1.0"""

    VERSION = "1.0"
    MYDATAOBJCLASS = MyDataObjectV10

    def __init__(self) -> None:
        self.obj1 = MyDataObjectV10("first_obj_title")
        self.obj2 = MyDataObjectV10("second_obj_title")

    def __str__(self) -> str:
        """Return the string representation of the object"""
        return f"{self.__class__.__name__}({self.obj1}, {self.obj2})"

    def save(self, filename: str) -> None:
        """Save the data model from an JSON file"""
        objs = [self.obj1, self.obj2]
        writer = JSONWriter(filename)
        writer.write(self.VERSION, "created_version")
        writer.write_object_list(objs, "ObjList")
        writer.save()

    def load(self, filename: str) -> None:
        """Load the data model to an JSON file"""
        reader = JSONReader(filename)
        created_version = reader.read("created_version")
        self.obj1, self.obj2 = reader.read_object_list("ObjList", self.MYDATAOBJCLASS)
        execenv.print("Created version:", created_version)
        execenv.print("Current version:", self.VERSION)
        execenv.print("Model data:", self)
        reader.close()


# The following class represents a new version of the data model: let's assume that
# it replaces the previous version and we want to be able to deserialize the old
# version as well as the new version.
class MyDataObjectV11(MyDataObjectV10):
    """Data object version 1.1"""

    def __init__(self, title: str = "", subtitle: str = "") -> None:
        super().__init__(title)
        self.subtitle = subtitle  # New attribute

    def __str__(self) -> str:
        """Return the string representation of the object"""
        return f"{self.__class__.__name__}({self.title}, {self.subtitle})"

    def serialize(self, writer: JSONWriter):
        """Serialize the data model to an JSON file"""
        super().serialize(writer)
        writer.write(self.subtitle, "subtitle")

    def deserialize(self, reader: JSONReader):
        """Deserialize the data model from an JSON file"""
        super().deserialize(reader)
        # Handling compatibility with the previous version is done by providing a
        # default value for the new attribute:
        self.subtitle = reader.read("subtitle", default="<default (test)>")


class MyDataModelV11(MyDataModelV10):
    """Data model version 1.1"""

    VERSION = "1.1"
    MYDATAOBJCLASS = MyDataObjectV11

    def __init__(self) -> None:
        self.obj1 = MyDataObjectV11("first_obj_title")
        self.obj2 = MyDataObjectV11("second_obj_title")


def test_json_datamodel_compatiblity():
    """Test JSON I/O with data model compatibility"""
    path = osp.abspath("test.json")
    atexit.register(os.unlink, path)
    # atexit.register(lambda: os.unlink(path))
    # Serialize the first version of the data model
    model_v10 = MyDataModelV10()
    model_v10.save(path)
    # Deserialize the first version of the data model
    model_v10.load(path)
    # Deserialize using the new version of the data model
    model_v11 = MyDataModelV11()
    model_v11.load(path)


if __name__ == "__main__":
    test_json_datamodel_compatiblity()
