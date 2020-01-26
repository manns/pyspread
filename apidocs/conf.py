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
if sys.path.count(ROOT_PATH) == 0:
    sys.path.insert(0, ROOT_PATH)

SRC_PATH = os.path.abspath( os.path.join(ROOT_PATH, "src") )
sys.path.insert(0, SRC_PATH)

# -- Project information -----------------------------------------------------

project = 'pyspread'
copyright = '2019 Martin Manns'
author = 'Martin Manns'

# The full version, including alpha/beta/rc tags
# TODO use proper version here
# from src.settings import VERSION
release = 'v2-dev'


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
    'sphinx.ext.intersphinx',
    'sphinx.ext.todo',
    # 'sphinx.ext.coverage',
    # 'sphinx.ext.mathjax',
    'sphinx.ext.viewcode',
    'sphinx.ext.graphviz',
    'sphinx.ext.napoleon',

    'recommonmark'
]

master_doc = 'index'

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


## Were autodoc so set stuff aphabetically
autodoc_member_order = "alphabetical"

## Flags for the stuff to document..
autodoc_default_flags = [
    'members',
    'undoc-members',
    'private-members',
    #'special-members',
    #'inherited-members',
    #"exclude-members ",
    'show-inheritance'
]
autoclass_content = "both"
autosummary_generate = True


# -- Options for HTML output -------------------------------------------------
html_title = 'pyspread API docs'
html_short_title = "pyspread"


html_theme = 'sphinxbootstrap4theme'
import sphinxbootstrap4theme
html_theme_path = [sphinxbootstrap4theme.get_path()]

html_theme_options = dict(
    navbar_style = "",
    navbar_color_class = "light",
    navbar_bg_class = "light",
    navbar_show_pages = False,
    navbar_pages_title = "Pages",
    #navbar_links =
    #navbar_collapse = md
    #main_width = 80%
    show_sidebar = True,
    sidebar_right = False,
    sidebar_fixed = False,
    table_thead_class = "inverse"
)

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']

#html_sidebars = { '**': ['globaltoc.html', 'relations.html', 'sourcelink.html', 'searchbox.html'], }
html_sidebars = { '**': ['globaltoc.html'], }

# If true, links to the reST sources are added to the pages.
#
html_show_sourcelink = False

# If true, "Created using Sphinx" is shown in the HTML footer. Default is True.
#
html_show_sphinx = False

# If true, "(C) Copyright ..." is shown in the HTML footer. Default is True.
#
html_show_copyright = False

html_context = {
    "git_repos_url": "https://gitlab.com/pyspread/pyspread"

}

html_favicon = "_static/pyspread.png"

intersphinx_mapping = {
    'python': ('http://docs.python.org/3', None),
    'numpy': ('http://docs.scipy.org/doc/numpy', None),
    'scipy': ('http://docs.scipy.org/doc/scipy/reference', None),
    'matplotlib': ('https://matplotlib.org/', None)
}