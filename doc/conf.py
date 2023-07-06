# -*- coding: utf-8 -*-

import os
import sys

sys.path.insert(0, os.path.abspath(".."))

import guidata  # noqa: E402
from guidata.utils.genreqs import generate_requirement_tables  # noqa: E402

generate_requirement_tables(guidata, ["Python>=3.7", "PyQt>=5.11"])

project = "guidata"
copyright = "2009 CEA - Commissariat à l'Energie Atomique et aux Energies Alternatives"
version = ".".join(guidata.__version__.split(".")[:2])
release = guidata.__version__

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.intersphinx",
    "sphinx.ext.doctest",
    "sphinx.ext.mathjax",
    "sphinx_copybutton",
    "sphinx.ext.napoleon",
]
templates_path = ["_templates"]
source_suffix = ".rst"
master_doc = "index"

exclude_trees = []
pygments_style = "sphinx"
modindex_common_prefix = ["guidata."]
autodoc_member_order = "bysource"

html_theme = "classic"
html_title = "%s %s Manual" % (project, version)
html_short_title = "%s Manual" % project
html_logo = "images/guidata-vertical.png"
html_favicon = "_static/favicon.ico"
html_static_path = ["_static"]
html_use_modindex = True
htmlhelp_basename = "guidata"
latex_documents = [
    ("index", "guidata.tex", "guidata Manual", "Pierre Raybaut", "manual"),
]
