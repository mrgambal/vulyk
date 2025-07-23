#!/usr/bin/env python
# -*- coding: utf-8 -*-
import datetime
import os
import sys

# Get the project root dir, which is the parent dir of this
cwd = os.getcwd()
project_root = os.path.dirname(cwd)

# Insert the project root dir as the first element in the PYTHONPATH.
# This lets us ensure that the source package is imported, and that its
# version is used.
sys.path.insert(0, project_root)
# Build the documentation in an autochthonous manner.
os.environ["LOGGING_LOCATION"] = "/tmp/vulyk.log"
os.environ["mongodb_host"] = "mongodb://localhost"

import vulyk

# -- General configuration ---------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom ones.
extensions = ["sphinx.ext.autodoc", "sphinx.ext.viewcode"]

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# The suffix of source filenames.
source_suffix = ".rst"

# The encoding of source files.
# source_encoding = 'utf-8-sig'

# The master toctree document.
master_doc = "index"

# General information about the project.
project = "Vulyk"
copyright = "{0}, Dmytro Hambal".format(datetime.date.today().year)

# The version info for the project you're documenting, acts as replacement
# for |version| and |release|, also used in various other places throughout
# the built documents.
#
# The short X.Y version.
version = vulyk.__version__
# The full version, including alpha/beta/rc tags.
release = vulyk.__version__

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
exclude_patterns = ["_build"]

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = "sphinx"


# -- Options for HTML output -------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
html_theme = "alabaster"

# If true, "Created using Sphinx" is shown in the HTML footer.
# Default is True.
html_show_sphinx = False

# Output file base name for HTML help builder.
htmlhelp_basename = "vulykdoc"


# -- Options for LaTeX output ------------------------------------------

latex_elements = {}

# Grouping the document tree into LaTeX files. List of tuples
# (source start file, target name, title, author, documentclass
# [howto/manual]).
latex_documents = [("index", "vulyk.tex", "Vulyk Documentation", "Dmytro Hambal", "manual")]


# -- Options for manual page output ------------------------------------

# One entry per manual page. List of tuples
# (source start file, name, description, authors, manual section).
man_pages = [("index", "vulyk", "Vulyk Documentation", ["Dmytro Hambal"], 1)]


# -- Options for Texinfo output ----------------------------------------

# Grouping the document tree into Texinfo files. List of tuples
# (source start file, target name, title, author,
#  dir menu entry, description, category)
texinfo_documents = [
    (
        "index",
        "vulyk",
        "Vulyk Documentation",
        "Dmytro Hambal",
        "vulyk",
        "Flask/Mongo application to provide intuitive web-interface for tasks distribution.",
        "Miscellaneous",
    ),
]
