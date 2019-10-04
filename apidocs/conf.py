# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# http://www.sphinx-doc.org/en/master/config

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys

os.environ["__GEN_DOCS__"] = "1"

HERE_PATH =  os.path.abspath( os.path.dirname( __file__ ))
sys.path.insert(0, HERE_PATH) # for local *.rst files

ROOT_PATH = os.path.abspath( os.path.join(HERE_PATH, "..") )
#if sys.path.count(ROOT_PATH) == 0:
#    sys.path.insert(0, ROOT_PATH)

SRC_PATH = os.path.abspath( os.path.join(ROOT_PATH, "src") )
sys.path.insert(0, SRC_PATH)

# -- Project information -----------------------------------------------------

project = 'pyspread'
copyright = '2019, pyspread.team'
author = 'pyspread.team'

# The full version, including alpha/beta/rc tags
release = 'py3'


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.intersphinx',
    'sphinx.ext.todo',
    # 'sphinx.ext.coverage',
    # 'sphinx.ext.mathjax',
    'sphinx.ext.viewcode',
    'sphinx.ext.graphviz',
    'recommonmark'
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store', "requirements.txt"]

source_suffix = {
    '.rst': 'restructuredtext',
    '.txt': 'markdown',
    '.md': 'markdown',
}

primary_domain = 'py'
highlight_language = 'py'

# -- Options for HTML output -------------------------------------------------
html_title = 'pyspread API docs'
html_short_title = "pyspread"
# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = 'pyramid'
#import sphinxbootstrap4theme
#html_theme_path = [sphinxbootstrap4theme.get_path()]

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']

html_sidebars = { '**': ['globaltoc.html', 'relations.html', 'sourcelink.html', 'searchbox.html'], }

# If true, links to the reST sources are added to the pages.
#
html_show_sourcelink = False

# If true, "Created using Sphinx" is shown in the HTML footer. Default is True.
#
html_show_sphinx = False

# If true, "(C) Copyright ..." is shown in the HTML footer. Default is True.
#
html_show_copyright = False
