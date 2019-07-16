# -*- coding: utf-8 -*-

from __future__ import division, print_function, unicode_literals

import os
import sys
from configparser import RawConfigParser

import sphinx_rtd_theme

sys.path.insert(0, os.path.abspath('..'))
sys.path.append(os.path.dirname(__file__))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "readthedocs.settings.dev")

from django.conf import settings
from django.utils import timezone

import django
django.setup()


def get_version():
    """Return package version from setup.cfg."""
    config = RawConfigParser()
    config.read(os.path.join('..', 'setup.cfg'))
    return config.get('metadata', 'version')


sys.path.append(os.path.abspath('_ext'))
extensions = [
    'sphinx.ext.autosectionlabel',
    'sphinx.ext.autodoc',
    'sphinx.ext.intersphinx',
    'sphinxcontrib.httpdomain',
    'djangodocs',
    'doc_extensions',
    'sphinx_tabs.tabs',
    'sphinx-prompt',
    'recommonmark',
    'notfound.extension',
]
templates_path = ['_templates']

source_suffix = ['.rst', '.md']

master_doc = 'index'
project = u'Read the Docs'
copyright = '2010-{}, Read the Docs, Inc & contributors'.format(
    timezone.now().year
)
version = get_version()
release = version
exclude_patterns = ['_build']
default_role = 'obj'
intersphinx_mapping = {
    'python': ('https://python.readthedocs.io/en/latest/', None),
    'django': ('https://django.readthedocs.io/en/1.11.x/', None),
    'sphinx': ('https://sphinx.readthedocs.io/en/latest/', None),
}
htmlhelp_basename = 'ReadTheDocsdoc'
latex_documents = [
    ('index', 'ReadTheDocs.tex', u'Read the Docs Documentation',
     u'Eric Holscher, Charlie Leifer, Bobby Grace', 'manual'),
]
man_pages = [
    ('index', 'read-the-docs', u'Read the Docs Documentation',
     [u'Eric Holscher, Charlie Leifer, Bobby Grace'], 1)
]

exclude_patterns = [
    # 'api' # needed for ``make gettext`` to not die.
]

language = 'en'

locale_dirs = [
    'locale/',
]
gettext_compact = False

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
html_theme_path = [sphinx_rtd_theme.get_html_theme_path()]
html_logo = 'img/logo.svg'
html_theme_options = {
    'logo_only': True,
    'display_version': False,
}

# Activate autosectionlabel plugin
autosectionlabel_prefix_document = True

# sphinx-notfound-page
# https://github.com/readthedocs/sphinx-notfound-page
notfound_context = {
    'title': 'Page Not Found',
    'body': '''
<h1>Page Not Found</h1>

<p>Sorry, we couldn't find that page.</p>

<p>Try using the search box or go to the homepage.</p>
''',
}


def setup(app):
    app.add_stylesheet('css/sphinx_prompt_css.css')
