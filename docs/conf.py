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

from multiproject.utils import get_project

sys.path.append(os.path.abspath("_ext"))

extensions = [
    "multiproject",
    "myst_parser",
    # For testing, conditionally disable the custom 404 pages on dev docs
    # "notfound.extension",
    "sphinx_copybutton",
    "sphinx_design",
    "sphinx_tabs.tabs",
    "sphinx_prompt",
    "sphinx.ext.autodoc",
    "sphinx.ext.autosectionlabel",
    "sphinx.ext.extlinks",
    "sphinx.ext.intersphinx",
    "sphinxcontrib.httpdomain",
    "sphinxcontrib.video",
    "sphinxemoji.sphinxemoji",
    "sphinxext.opengraph",
]

multiproject_projects = {
    "user": {
        "use_config_file": False,
        "config": {
            "project": "Read the Docs user documentation",
            "html_title": "Read the Docs user documentation",
        },
    },
    "dev": {
        "use_config_file": False,
        "config": {
            "project": "Read the Docs developer documentation",
            "html_title": "Read the Docs developer documentation",
        },
    },
}

docset = get_project(multiproject_projects)

# Disable custom 404 on dev docs
if docset == "user":
    extensions.append("notfound.extension")

ogp_site_name = "Read the Docs Documentation"
ogp_use_first_image = True  # https://github.com/readthedocs/blog/pull/118
ogp_image = "https://docs.readthedocs.io/en/latest/_static/img/logo-opengraph.png"
# Inspired by https://github.com/executablebooks/MyST-Parser/pull/404/
ogp_custom_meta_tags = (
    '<meta name="twitter:card" content="summary_large_image" />',
)
ogp_enable_meta_description = True
ogp_description_length = 300

templates_path = [os.path.join(os.path.dirname(__file__), "_templates")]

# This may be elevated as a general issue for documentation and behavioral
# change to the Sphinx build:
# This will ensure that we use the correctly set environment for canonical URLs
# Old Read the Docs injections makes it point only to the default version,
# for instance /en/stable/
html_baseurl = os.environ.get("READTHEDOCS_CANONICAL_URL", "/")

master_doc = "index"
copyright = "Read the Docs, Inc & contributors"
version = "2026.5.5"
release = version
exclude_patterns = ["_build", "shared", "_includes"]
# Exclude design docs from dev documentation
if docset == "dev":
    exclude_patterns.append("design")
default_role = "obj"
intersphinx_cache_limit = 14  # cache for 2 weeks
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
    "myst-parser": ("https://myst-parser.readthedocs.io/en/stable/", None),
    "writethedocs": ("https://www.writethedocs.org/", None),
    "jupyterbook": ("https://jupyterbook.org/en/stable/", None),
    "executablebook": ("https://executablebooks.org/en/latest/", None),
    "rst-to-myst": ("https://rst-to-myst.readthedocs.io/en/stable/", None),
    "rtd": ("https://docs.readthedocs.io/en/stable/", None),
    "rtd-dev": ("https://dev.readthedocs.io/en/latest/", None),
    "rtd-blog": ("https://blog.readthedocs.com/", None),
    "jupyter": ("https://docs.jupyter.org/en/latest/", None),
}

# Intersphinx: Do not try to resolve unresolved labels that aren't explicitly prefixed.
# The default setting for intersphinx_disabled_reftypes can cause some pretty bad
# breakage because we have rtd and rtd-dev stable versions in our mappings.
# Hence, if we refactor labels, we won't see broken references, since the
# currently active stable mapping keeps resolving.
# Recommending doing this on all projects with Intersphinx.
# https://www.sphinx-doc.org/en/master/usage/extensions/intersphinx.html#confval-intersphinx_disabled_reftypes
intersphinx_disabled_reftypes = ["*"]

myst_enable_extensions = [
    "deflist",
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

html_theme = "furo"
html_static_path = ["_static", f"{docset}/_static"]
html_css_files = ["css/custom.css", "css/sphinx_prompt_css.css"]
html_js_files = ["js/expand_tabs.js"]

# Furo theme: brand colors pulled from the Read the Docs visual identity.
# The accent green (#80ba33) is the marketing primary; the deep navy/teal
# (#2d4955) mirrors the dark wordmark background and gives the sidebar weight.
# The original wordmark is white-on-dark, so we ship a dark-text variant for
# Furo's light mode and reuse the original for dark mode.
html_theme_options = {
    "light_logo": "img/logo-dark-text.svg",
    "dark_logo": "img/logo-light-text.svg",
    "sidebar_hide_name": True,
    "navigation_with_keys": True,
    "top_of_page_buttons": ["view", "edit"],
    "source_repository": "https://github.com/readthedocs/readthedocs.org/",
    "source_branch": "main",
    "source_directory": f"docs/{docset}/",
    "light_css_variables": {
        "color-brand-primary": "#80ba33",
        "color-brand-content": "#5a8a1f",
        "color-brand-visited": "#5a8a1f",
        "color-admonition-title--note": "#80ba33",
        "color-admonition-title-background--note": "rgba(128, 186, 51, 0.1)",
        "color-sidebar-background": "#f7f7f5",
        "color-sidebar-background-border": "#e6e7e6",
        "color-sidebar-search-background": "#ffffff",
        "color-sidebar-link-text--top-level": "#2d4955",
        "color-sidebar-item-background--current": "rgba(128, 186, 51, 0.12)",
        "color-sidebar-item-expander-background--hover": "rgba(128, 186, 51, 0.18)",
        "color-highlighted-background": "#fff4c2",
        "font-stack": (
            "-apple-system, BlinkMacSystemFont, 'Segoe UI', 'Inter', Roboto, "
            "'Helvetica Neue', Arial, sans-serif"
        ),
        "font-stack--monospace": (
            "'JetBrains Mono', 'Fira Code', SFMono-Regular, Menlo, Consolas, "
            "'Liberation Mono', monospace"
        ),
    },
    "dark_css_variables": {
        "color-brand-primary": "#a4d65e",
        "color-brand-content": "#a4d65e",
        "color-brand-visited": "#a4d65e",
        "color-background-primary": "#1a2530",
        "color-background-secondary": "#22303b",
        "color-sidebar-background": "#162028",
        "color-sidebar-background-border": "#0f1820",
        "color-sidebar-search-background": "#1a2530",
        "color-sidebar-item-background--current": "rgba(164, 214, 94, 0.18)",
        "color-sidebar-item-expander-background--hover": "rgba(164, 214, 94, 0.25)",
        "color-highlighted-background": "#3f4d20",
    },
    "footer_icons": [
        {
            "name": "GitHub",
            "url": "https://github.com/readthedocs/readthedocs.org",
            "html": (
                '<svg stroke="currentColor" fill="currentColor" stroke-width="0" '
                'viewBox="0 0 16 16"><path fill-rule="evenodd" d="M8 0C3.58 0 0 '
                '3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01'
                '-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13'
                '-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 '
                '2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.3'
                '1-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18'
                ' 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 '
                '1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 '
                '3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.'
                '38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"></path></svg>'
            ),
            "class": "",
        },
    ],
    "announcement": (
        '<a href="https://about.readthedocs.com/?utm_source=docs&utm_medium='
        'announcement" style="color: inherit; text-decoration: underline;">'
        "Hosted by Read the Docs"
        "</a> &mdash; the documentation platform for open source and teams."
    ),
}

html_context = {
    # Fix the "edit on" links.
    # TODO: remove once we support different rtd config
    # files per project.
    "conf_py_path": f"/docs/{docset}/",
    "display_github": True,
    "github_user": "readthedocs",
    "github_repo": "readthedocs.org",
    "github_version": "main",
    # Use to generate the Plausible "data-domain" attribute from the template
    "plausible_domain": f"{os.environ.get('READTHEDOCS_PROJECT')}.readthedocs.io",
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

extlinks = {
    "rtd-issue": ("https://github.com/readthedocs/readthedocs.org/issues/%s", "#%s"),
}

# Disable epub mimetype warnings
suppress_warnings = ["epub.unknown_project_files"]
