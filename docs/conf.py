"""
Shared Sphinx configuration using sphinx-multiproject.

To build each project, the ``PROJECT`` environment variable is used.

.. code:: console

   $ make html  # build default project
   $ PROJECT=dev make html  # build the dev project

for more information read https://sphinx-multiproject.readthedocs.io/.
"""

import os
import sys

import sphinx_rtd_theme
from multiproject.utils import get_project

sys.path.insert(0, os.path.abspath(".."))
sys.path.append(os.path.dirname(__file__))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "readthedocs.settings.dev")

# Load Django after sys.path and configuration setup
# isort: split
import django

django.setup()

sys.path.append(os.path.abspath("_ext"))
extensions = [
    "multiproject",
    "sphinx.ext.autosectionlabel",
    "sphinx.ext.autodoc",
    "sphinx.ext.intersphinx",
    "sphinxcontrib.httpdomain",
    "sphinxcontrib.video",
    "djangodocs",
    "doc_extensions",
    "sphinx_tabs.tabs",
    "sphinx-prompt",
    "notfound.extension",
    "hoverxref.extension",
    "sphinx_search.extension",
    "sphinxemoji.sphinxemoji",
    "sphinx_design",
    "myst_parser",
]

multiproject_projects = {
    "user": {
        "use_config_file": False,
        "config": {
            "project": "Read the Docs user documentation",
        },
    },
    "dev": {
        "use_config_file": False,
        "config": {
            "project": "Read the Docs developer documentation",
        },
    },
}

docset = get_project(multiproject_projects)


templates_path = ["_templates"]

master_doc = "index"
copyright = "Read the Docs, Inc & contributors"
version = "9.3.0"
release = version
exclude_patterns = ["_build", "shared"]
default_role = "obj"
intersphinx_timeout = 3  # 3 seconds timeout
intersphinx_mapping = {
    "python": ("https://docs.python.org/3.10/", None),
    "django": (
        "https://docs.djangoproject.com/en/stable/",
        "https://docs.djangoproject.com/en/stable/_objects/",
    ),
    "sphinx": ("https://www.sphinx-doc.org/en/master/", None),
    "pip": ("https://pip.pypa.io/en/stable/", None),
    "nbsphinx": ("https://nbsphinx.readthedocs.io/en/latest/", None),
    "myst-nb": ("https://myst-nb.readthedocs.io/en/stable/", None),
    "ipywidgets": ("https://ipywidgets.readthedocs.io/en/stable/", None),
    "jupytext": ("https://jupytext.readthedocs.io/en/stable/", None),
    "ipyleaflet": ("https://ipyleaflet.readthedocs.io/en/latest/", None),
    "poliastro": ("https://docs.poliastro.space/en/stable/", None),
    "qiskit": ("https://qiskit.org/documentation/", None),
    "myst-parser": ("https://myst-parser.readthedocs.io/en/stable/", None),
    "writethedocs": ("https://www.writethedocs.org/", None),
    "jupyterbook": ("https://jupyterbook.org/en/stable/", None),
    "executablebook": ("https://executablebooks.org/en/latest/", None),
    "rst-to-myst": ("https://rst-to-myst.readthedocs.io/en/stable/", None),
    "rtd": ("https://docs.readthedocs.io/en/stable/", None),
    "rtd-dev": ("https://dev.readthedocs.io/en/latest/", None),
    "jupyter": ("https://docs.jupyter.org/en/latest/", None),
}
# Redundant in Sphinx 5.0
# https://www.sphinx-doc.org/en/master/usage/extensions/intersphinx.html#confval-intersphinx_disabled_reftypes
intersphinx_disabled_reftypes = ["std:doc"]
myst_enable_extensions = [
    "deflist",
]
hoverxref_intersphinx = [
    "sphinx",
    "pip",
    "nbsphinx",
    "myst-nb",
    "ipywidgets",
    "jupytext",
]
htmlhelp_basename = "ReadTheDocsdoc"
latex_documents = [
    (
        "index",
        "ReadTheDocs.tex",
        "Read the Docs Documentation",
        "Eric Holscher, Charlie Leifer, Bobby Grace",
        "manual",
    ),
]
man_pages = [
    (
        "index",
        "read-the-docs",
        "Read the Docs Documentation",
        ["Eric Holscher, Charlie Leifer, Bobby Grace"],
        1,
    )
]

language = "en"

locale_dirs = [
    f"{docset}/locale/",
]
gettext_compact = False

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static", f"{docset}/_static"]
html_css_files = ["css/custom.css", "css/sphinx_prompt_css.css"]
html_js_files = ["js/expand_tabs.js"]
html_theme_path = [sphinx_rtd_theme.get_html_theme_path()]
html_logo = "img/logo.svg"
html_theme_options = {
    "logo_only": True,
    "display_version": False,
}
html_context = {
    # Fix the "edit on" links.
    # TODO: remove once we support different rtd config
    # files per project.
    "conf_py_path": f"/docs/{docset}/",
}

hoverxref_auto_ref = True
hoverxref_domains = ["py"]
hoverxref_roles = [
    "option",
    "doc",  # Documentation pages
    "term",  # Glossary terms
]
hoverxref_role_types = {
    "mod": "modal",  # for Python Sphinx Domain
    "doc": "modal",  # for whole docs
    "class": "tooltip",  # for Python Sphinx Domain
    "ref": "tooltip",  # for hoverxref_auto_ref config
    "confval": "tooltip",  # for custom object
    "term": "tooltip",  # for glossaries
}

# See dev/style_guide.rst for documentation
rst_epilog = """
.. |org_brand| replace:: Read the Docs Community
.. |com_brand| replace:: Read the Docs for Business
.. |git_providers_and| replace:: GitHub, Bitbucket, and GitLab
.. |git_providers_or| replace:: GitHub, Bitbucket, or GitLab
"""

# Activate autosectionlabel plugin
autosectionlabel_prefix_document = True

# sphinx-notfound-page
# https://github.com/readthedocs/sphinx-notfound-page
notfound_context = {
    "title": "Page Not Found",
    "body": """
<h1>Page Not Found</h1>

<p>Sorry, we couldn't find that page.</p>

<p>Try using the search box or go to the homepage.</p>
""",
}
linkcheck_retries = 2
linkcheck_timeout = 1
linkcheck_workers = 10
linkcheck_ignore = [
    r"http://127\.0\.0\.1",
    r"http://localhost",
    r"http://community\.dev\.readthedocs\.io",
    r"https://yourproject\.readthedocs\.io",
    r"https?://docs\.example\.com",
    r"https://foo\.readthedocs\.io/projects",
    r"https://github\.com.+?#L\d+",
    r"https://github\.com/readthedocs/readthedocs\.org/issues",
    r"https://github\.com/readthedocs/readthedocs\.org/pull",
    r"https://docs\.readthedocs\.io/\?rtd_search",
    r"https://readthedocs\.org/search",
    # This page is under login
    r"https://readthedocs\.org/accounts/gold",
]

# Disable epub mimetype warnings
suppress_warnings = ["epub.unknown_project_files"]
