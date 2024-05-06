# -*- coding: utf-8 -*-
#
# Licensed under the terms of the BSD 3-Clause
# (see guidata/LICENSE for details)

"""
Test HDF5 I/O
-------------

Testing various use cases of HDF5 I/O:

* Serialize and deserialize a data model, handling versioning and compatibility breaks.
"""

from __future__ import annotations

import atexit
import os
import os.path as osp

import guidata.dataset as gds
from guidata.env import execenv
from guidata.io import HDF5Reader, HDF5Writer


# The following class represents a data model that we want to serialize and deserialize.
# This is the first version of the data model.
class MyFirstDataSetV10(gds.DataSet):
    """First data set version 1.0"""

    alpha = gds.FloatItem("Alpha", default=0.0)
    number = gds.IntItem("Number", default=0)
    text = gds.StringItem("Text", default="")


class MySecondDataSetV10(gds.DataSet):
    """Second data set version 1.0"""

    length = gds.FloatItem("Length", default=0.0)
    duration = gds.IntItem("Duration", default=0)


class MyDataObjectV10:
    """Data object version 1.0"""

    def __init__(self, title: str = "") -> None:
        self.title = title
        self.metadata = {"author": "John Doe", "age": 24, "skills": ["Python", "C++"]}

    def __str__(self) -> str:
        """Return the string representation of the object"""
        return f"{self.__class__.__name__}({self.title})"

    def serialize(self, writer: HDF5Writer) -> None:
        """Serialize the data model to an HDF5 file"""
        writer.write(self.title, "title")
        with writer.group("metadata"):
            writer.write_dict(self.metadata)

    def deserialize(self, reader: HDF5Reader) -> None:
        """Deserialize the data model from an HDF5 file"""
        self.title = reader.read("title")
        with reader.group("metadata"):
            self.metadata = reader.read_dict()


class MyDataModelV10:
    """Data model version 1.0"""

    VERSION = "1.0"
    MYDATAOBJCLASS = MyDataObjectV10
    MYDATASETCLASS1 = MyFirstDataSetV10
    MYDATASETCLASS2 = MySecondDataSetV10

    def __init__(self) -> None:
        self.obj1 = MyDataObjectV10("first_obj_title")
        self.obj2 = MyDataObjectV10("second_obj_title")
        self.obj3 = MyDataObjectV10("third_obj_title")
        self.param1 = MyFirstDataSetV10()
        self.param2 = MySecondDataSetV10()

    def __str__(self) -> str:
        """Return the string representation of the object"""
        text = f"{self.__class__.__name__}:"
        text += f"\n  {self.obj1}"
        text += f"\n  {self.obj2}"
        text += f"\n  {self.obj3}"
        text += f"\n  {self.param1}"
        text += f"\n  {self.param2}"
        return text

    def save(self, filename: str) -> None:
        """Save the data model from an HDF5 file"""
        objs = [self.obj1, self.obj2]
        writer = HDF5Writer(filename)
        writer.write(self.VERSION, "created_version")
        writer.write_object_list(objs, "ObjList")
        writer.write(self.obj3, "IndividualObj")
        writer.write(self.param1, "Param1")
        writer.write(self.param2, "Param2")
        writer.close()

    def load(self, filename: str) -> None:
        """Load the data model to an HDF5 file"""
        reader = HDF5Reader(filename)
        created_version = reader.read("created_version")
        self.obj1, self.obj2 = reader.read_object_list("ObjList", self.MYDATAOBJCLASS)
        self.obj3 = reader.read("IndividualObj", self.MYDATAOBJCLASS)
        self.param1 = reader.read("Param1", self.MYDATASETCLASS1)
        self.param2 = reader.read("Param2", self.MYDATASETCLASS2)
        execenv.print("Created version:", created_version)
        execenv.print("Current version:", self.VERSION)
        execenv.print("Model data:", self)
        reader.close()


# The following class represents a new version of the data model: let's assume that
# it replaces the previous version and we want to be able to deserialize the old
# version as well as the new version.
class MyFirstDataSetV11(MyFirstDataSetV10):
    """First data set version 1.1"""

    # Adding a new item
    beta = gds.FloatItem("Beta", default=0.0)


class MySecondDataSetV11(gds.DataSet):
    """Second data set version 1.1"""

    # Redefining the data set with new items (replacing the previous version)
    width = gds.FloatItem("Width", default=10.0)
    height = gds.FloatItem("Height", default=20.0)


class MyDataObjectV11(MyDataObjectV10):
    """Data object version 1.1"""

    def __init__(self, title: str = "", subtitle: str = "") -> None:
        super().__init__(title)
        self.subtitle = subtitle  # New attribute

    def __str__(self) -> str:
        """Return the string representation of the object"""
        return f"{self.__class__.__name__}({self.title}, {self.subtitle})"

    def serialize(self, writer: HDF5Writer):
        """Serialize the data model to an HDF5 file"""
        super().serialize(writer)
        writer.write(self.subtitle, "subtitle")

    def deserialize(self, reader: HDF5Reader):
        """Deserialize the data model from an HDF5 file"""
        super().deserialize(reader)
        # Handling compatibility with the previous version is done by providing a
        # default value for the new attribute:
        self.subtitle = reader.read("subtitle", default="<default (test)>")


class MyDataModelV11(MyDataModelV10):
    """Data model version 1.1"""

    VERSION = "1.1"
    MYDATAOBJCLASS = MyDataObjectV11
    MYDATASETCLASS1 = MyFirstDataSetV11
    MYDATASETCLASS2 = MySecondDataSetV11

    def __init__(self) -> None:
        self.obj1 = MyDataObjectV11("first_obj_title")
        self.obj2 = MyDataObjectV11("second_obj_title")
        self.obj3 = MyDataObjectV11("third_obj_title")
        self.param1 = MyFirstDataSetV11()
        self.param2 = MySecondDataSetV11()


def test_hdf5_datamodel_compatiblity():
    """Test HDF5 I/O with data model compatibility"""
    path = osp.abspath("test.h5")
    atexit.register(os.unlink, path)
    # Serialize the first version of the data model
    model_v10 = MyDataModelV10()
    model_v10.save(path)
    # Deserialize the first version of the data model
    model_v10.load(path)
    # Deserialize using the new version of the data model
    model_v11 = MyDataModelV11()
    model_v11.load(path)


if __name__ == "__main__":
    test_hdf5_datamodel_compatiblity()
