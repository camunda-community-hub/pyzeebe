# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

import importlib.metadata

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys

import sphinx_rtd_theme

sys.path.insert(0, os.path.abspath(".."))

# -- Project information -----------------------------------------------------

sphinx_rtd_theme  # So optimize imports doens't erase it

project = "pyzeebe"
copyright = "2020, Jonatan Martens"
author = "Jonatan Martens"

# The full version, including alpha/beta/rc tags
release = importlib.metadata.version(project)

# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "sphinx_rtd_theme",
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.autosectionlabel",
    "sphinx.ext.intersphinx",
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = []

# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = "sphinx_rtd_theme"

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static"]

version = importlib.metadata.version(project)

master_doc = "index"

# Looks for objects in external projects
intersphinx_mapping = {
    "grpc": ("https://grpc.github.io/grpc/python/", None),
    "requests": ("https://requests.readthedocs.io/en/latest/", None),
    "requests_oauthlib": ("https://requests-oauthlib.readthedocs.io/en/latest/", None),
    "python": ("https://docs.python.org/3/", None),
}
