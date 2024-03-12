# -*- coding: utf-8 -*-
#
# Licensed under the terms of the BSD 3-Clause
# (see guidata/LICENSE for details)

"""Generate install requirements RST table."""

import pytest

from guidata.tests import get_path
from guidata.utils import genreqs

GR_PATH = get_path("genreqs")


def test_compare_cfg_toml():
    """Compare requirements generated from setup.cfg and pyproject.toml."""
    req_toml = genreqs.extract_requirements_from_toml(GR_PATH)
    req_cfg = genreqs.extract_requirements_from_cfg(GR_PATH)
    assert req_toml == req_cfg


@pytest.mark.skip(reason="This test should be run manually (development only)")
def test_generate_requirement_tables():
    """Test generate_requirement_tables."""
    genreqs.gen_path_req_rst(GR_PATH, "guidata", ["Python>=3.8", "PyQt>=5.11"], GR_PATH)


if __name__ == "__main__":
    test_compare_cfg_toml()
    test_generate_requirement_tables()
