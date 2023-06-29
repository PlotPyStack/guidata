# -*- coding: utf-8 -*-
#
# Copyright © 2009-2010 CEA
# Pierre Raybaut
# Licensed under the terms of the CECILL License
# (see guidata/__init__.py for details)

"""Config test"""

import pytest

from guidata.config import UserConfig
from guidata.tests.test_all_features import Parameters


@pytest.fixture()
def config():
    """Create a config object"""
    CONF = UserConfig({})
    eta = Parameters()
    eta.write_config(CONF, "TestParameters", "")
    yield CONF


def test_load(config):
    """Test load config"""
    eta = Parameters()
    eta.read_config(config, "TestParameters", "")


def test_default(config):
    """Test default config"""
    eta = Parameters()
    eta.write_config(config, "etagere2", "")
    eta = Parameters()
    eta.read_config(config, "etagere2", "")


def test_restore(config):
    """Test restore config"""
    eta = Parameters()
    eta.fl2 = 2
    eta.integer = 6
    eta.write_config(config, "etagere3", "")

    eta = Parameters()
    eta.read_config(config, "etagere3", "")

    assert eta.fl2 == 2.0
    assert eta.integer == 6
