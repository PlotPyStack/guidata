# -*- coding: utf-8 -*-
#
# Copyright © 2009-2010 CEA
# Pierre Raybaut
# Licensed under the terms of the CECILL License
# (see guidata/__init__.py for details)

"""
Reader and Writer for the serialization of DataSets into HDF5 files
"""

import sys
import h5py
import numpy as np

from guidata.utils import utf8_to_unicode


class TypeConverter(object):
    def __init__(self, to_type, from_type=None):
        self._to_type = to_type
        if from_type:
            self._from_type = from_type
        else:
            self._from_type = to_type

    def to_hdf(self, value):
        try:
            return self._to_type(value)
        except:
            print >>sys.stderr, "ERR", repr(value)
            raise

    def from_hdf(self, value):
        return self._from_type(value)


unicode_hdf = TypeConverter(lambda x: x.encode("utf-8"), utf8_to_unicode)
int_hdf = TypeConverter(int)


class Attr(object):
    """Helper class representing class attribute that
    should be saved/restored to/from a corresponding HDF5 attribute
    
    hdf_name : name of the attribute in the HDF5 file
    struct_name : name of the attribute in the object (default to hdf_name)
    type : attribute type (guess it if None)
    optional : indicates whether we should fail if the attribute is not present
    """ 
    def __init__(self, hdf_name, struct_name=None, type=None, optional=False):
        self.hdf_name = hdf_name
        if struct_name is None:
            struct_name = hdf_name
        self.struct_name = struct_name
        self.type = type
        self.optional = optional

    def get_value(self, struct):
        if self.optional:
            return getattr(struct, self.struct_name, None)
        else:
            return getattr(struct, self.struct_name)

    def set_value(self, struct, value):
        setattr(struct, self.struct_name, value)

    def save(self, group, struct):
        value = self.get_value(struct)
        if self.optional and value is None:
            #print ".-", self.hdf_name, value
            if self.hdf_name in group.attrs:
                del group.attrs[self.hdf_name]
            return
        if self.type is not None:
            value = self.type.to_hdf(value)
        #print ".", self.hdf_name, value, self.optional
        try:
            group.attrs[self.hdf_name] = value
        except:
            print >>sys.stderr, "ERROR saving:", repr(value), "into", self.hdf_name
            raise
    
    def load(self, group, struct):
        #print "LoadAttr:", group, self.hdf_name
        if self.optional:
            if self.hdf_name not in group.attrs:
                self.set_value(struct, None)
                return
        try:
            value = group.attrs[self.hdf_name]
        except KeyError:
            raise KeyError, 'Unable to locate attribute %s' % self.hdf_name
        if self.type is not None:
            value = self.type.from_hdf(value)
        self.set_value(struct, value)


def createdset(group,name,value):
    group.create_dataset(name,
                         compression=None,
                         #compression_opts=3,
                         data=value)


class Dset(Attr):
    """
    Generic load/save for an hdf5 dataset:
    scalar=float -> used to convert the value when it is scalar
    """
    def __init__(self, hdf_name, struct_name=None, type=None, scalar=None,
                 optional=False):
        Attr.__init__(self, hdf_name, struct_name, type, optional)
        self.scalar = scalar

    def save(self, group, struct):
        value = self.get_value(struct)
        if isinstance(value, float):
            value = np.float64(value)
        elif isinstance(value, int):
            value = np.int32(value)
        if value is None or value.size==0:
            value = np.array([0.0])
        if value.shape == ():
            value = value.reshape( (1,) )
        group.require_dataset(self.hdf_name, shape=value.shape,
                              dtype=value.dtype, data=value,
                              compression="gzip", compression_opts=1)
    
    def load(self, group, struct):
        if self.optional:
            if self.hdf_name not in group:
                self.set_value(struct, None)
                return
        try:
            value = group[self.hdf_name][...]
        except KeyError:
            raise KeyError, 'Unable to locate dataset %s' % self.hdf_name
        if self.scalar is not None:
            value = self.scalar(value)
        self.set_value(struct, value)


class Dlist(Dset):
    def get_value(self, struct):
        return np.array( getattr(struct, self.struct_name) )

    def set_value(self, struct, value):
        setattr(struct, self.struct_name, list(value))


#==============================================================================
# Base HDF5 Store object: do not break API compatibility here as this class is 
# used in various critical projects for saving/loading application data
#==============================================================================
class H5Store(object):
    def __init__(self, filename):
        self.filename = filename
        self.h5 = None
    
    def open(self, mode="a"):
        """Open an hdf5 file"""
        if self.h5:
            return self.h5
        try:
            self.h5 = h5py.File(self.filename,mode=mode)
        except Exception:
            print >>sys.stderr, "Error trying to load:", self.filename, "in mode:", mode
            raise
        return self.h5

    def close(self):
        if self.h5:
            self.h5.close()
        self.h5 = None
        
    def generic_save(self, parent, source, structure):
        """save the data from source into the file using 'structure'
        as a descriptor.

        structure is a list of Attribute Descriptor (Attr, Dset, Dlist or anything
        with a save interface) that describe the conversion of data and the name
        of the attribute in the source and in the file
        """
        for instr in structure:
            instr.save(parent, source)

    def generic_load(self, parent, dest, structure):
        """load the data from the file into dest using 'structure'
        as a descriptor.
        
        structure is the same as in generic_save
        """
        for instr in structure:
            try:
                instr.load(parent, dest)
            except Exception:
                print >>sys.stderr, "Error loading HDF5 item:", instr.hdf_name
                raise


#==============================================================================
# HDF5 reader/writer: do not break API compatibility here as this class is 
# used in various critical projects for saving/loading application data and 
# in guiqwt for saving/loading plot items.
#==============================================================================
class HDF5Handler(H5Store):
    """Base HDF5 I/O Handler object"""
    def __init__(self, filename):
        super(HDF5Handler, self).__init__(filename)
        self.option = []
        
    def get_parent_group(self):
        parent = self.h5
        for option in self.option[:-1]:
            parent = parent.require_group(option)
        return parent
    
    def group(self, group_name):
        """Enter a HDF5 group. This returns a context manager, to be used with 
        the `with` statement"""
        from guidata.userconfig import GroupContext
        return GroupContext(self, group_name)

class HDF5Writer(HDF5Handler):
    """Writer for HDF5 files"""
    def __init__(self, filename):
        super(HDF5Writer, self).__init__(filename)
        self.open("w")
    
    def write(self, val, group_name=None):
        """Write value using the appropriate routine depending on value type
        
        group_name: if None, writing the value in current group"""
        from numpy import ndarray
        from guidata.dataset.datatypes import DataSet
        if group_name:
            self.begin(group_name)
        if isinstance(val, bool):
            self.write_bool(val)
        elif isinstance(val, int):
            self.write_int(val)
        elif isinstance(val, float):
            self.write_int(val)
        elif isinstance(val, unicode):
            self.write_unicode(val)
        elif isinstance(val, str):
            self.write_any(val)
        elif isinstance(val, ndarray):
            self.write_array(val)
        elif isinstance(val, DataSet):
            val.serialize(self)
        elif val is None:
            self.write_none()
        elif isinstance(val, (list, tuple)):
            self.write_sequence(val)
        else:
            raise NotImplementedError("cannot serialize %r of type %r" %
                                      (val, type(val)))
        if group_name:
            self.end(group_name)

    def write_any(self, val):
        group = self.get_parent_group()
        group.attrs[self.option[-1]] = val
    
    write_int = write_float = write_any
    
    def write_bool(self, val):
        self.write_int(int(val))
    
    def write_unicode(self, val):
        group = self.get_parent_group()
        group.attrs[self.option[-1]] = val.encode("utf-8")

    def write_array(self, val):
        group = self.get_parent_group()
        group[self.option[-1]] = val
    
    write_sequence = write_any
    
    def write_none(self):
        group = self.get_parent_group()
        group.attrs[self.option[-1]] = ""

    def begin(self, section):
        self.option.append(section)
        
    def end(self, section):
        sect = self.option.pop(-1)
        assert sect == section

class HDF5Reader(HDF5Handler):
    """Reader for HDF5 files"""
    def __init__(self, filename):
        super(HDF5Reader, self).__init__(filename)
        self.open("r")

    def read(self, group_name=None, func=None, dataset=None):
        """Read value within current group or group_name"""
        if group_name:
            self.begin(group_name)
        if dataset is None:
            if func is None:
                func = self.read_any
            val = func()
        else:
            dataset.deserialize(self)
            val = dataset
        if group_name:
            self.end(group_name)
        return val

    def read_any(self):
        group = self.get_parent_group()
        return group.attrs[self.option[-1]]

    def begin(self, section):
        self.option.append(section)
        
    def end(self, section):
        sect = self.option.pop(-1)
        assert sect == section

    def read_int(self):
        return int(self.read_any())

    def read_float(self):
        return float(self.read_any())

    def read_str(self):
        # Convert `numpy.string_` to `str`
        return str(self.read_any())

    def read_unicode(self):
        return unicode(self.read_any(), "utf-8")
    
    def read_array(self):
        group = self.get_parent_group()
        return group[self.option[-1]][...]
        
    def read_sequence(self):
        group = self.get_parent_group()
        return list(group.attrs[self.option[-1]])

    read_none = read_any
