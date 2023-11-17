# -*- coding: utf-8 -*-

import os
import sys

sys.path.insert(0, os.path.abspath(".."))

import guidata  # noqa: E402

creator = "Pierre Raybaut"
project = "guidata"
copyright = "2009 CEA, " + creator
version = ".".join(guidata.__version__.split(".")[:2])
release = guidata.__version__

extensions = [
    "sphinx.ext.autodoc",
    "myst_parser",
    "sphinx.ext.intersphinx",
    "sphinx.ext.doctest",
    "sphinx_copybutton",
    "sphinx.ext.napoleon",
    "sphinx_qt_documentation",
]
if "htmlhelp" in sys.argv:
    extensions += ["sphinx.ext.imgmath"]
else:
    extensions += ["sphinx.ext.mathjax"]
templates_path = ["_templates"]
source_suffix = ".rst"
master_doc = "index"

exclude_trees = []
pygments_style = "sphinx"
modindex_common_prefix = ["guidata."]
autodoc_member_order = "bysource"

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "numpy": ("https://numpy.org/doc/stable/", None),
    "h5py": ("https://docs.h5py.org/en/stable/", None),
}
# nitpicky = True  # Uncomment to warn about all broken links

if "htmlhelp" in sys.argv:
    html_theme = "classic"
else:
    html_theme = "python_docs_theme"
html_title = "%s %s Manual" % (project, version)
html_short_title = "%s Manual" % project
html_logo = "images/guidata-vertical.png"
html_favicon = "_static/favicon.ico"
html_static_path = ["_static"]
html_use_modindex = True
htmlhelp_basename = "guidata"
latex_documents = [
    ("index", "guidata.tex", "guidata Manual", creator, "manual"),
]
