# -*- coding: utf-8 -*-
#
import os
import sys

sys.path.insert(0, os.path.abspath('../readthedocs'))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings.sqlite")
from django.conf import settings


sys.path.append(os.path.abspath('_ext'))
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.intersphinx',
    'sphinx_http_domain',
    'djangodocs',
]
templates_path = ['_templates']
source_suffix = '.rst'
master_doc = 'index'
project = u'Read The Docs'
copyright = u'2010, Eric Holscher, Charlie Leifer, Bobby Grace'
version = '1.0'
release = '1.0'
exclude_patterns = ['_build']
default_role = 'obj'
pygments_style = 'sphinx'
intersphinx_mapping = {
    'python': ('http://python.readthedocs.org/en/latest/', None),
    'django': ('http://django.readthedocs.org/en/latest/', None),
    'sphinx': ('http://sphinx.readthedocs.org/en/latest/', None),
}
# This doesn't exist since we aren't shipping any static files ourselves.
#html_static_path = ['_static']
htmlhelp_basename = 'ReadTheDocsdoc'
latex_documents = [
    ('index', 'ReadTheDocs.tex', u'Read The Docs Documentation',
     u'Eric Holscher, Charlie Leifer, Bobby Grace', 'manual'),
]
man_pages = [
    ('index', 'read-the-docs', u'Read The Docs Documentation',
     [u'Eric Holscher, Charlie Leifer, Bobby Grace'], 1)
]

exclude_patterns = [
    #'api' # needed for ``make gettext`` to not die.
]

language = 'en'

locale_dirs = [
    'locale/',
]
gettext_compact = False


on_rtd = os.environ.get('READTHEDOCS', None) == 'True'
if not on_rtd:  # only import and set the theme if we're building docs locally
    import sphinx_rtd_theme
    html_theme = 'sphinx_rtd_theme'
    html_theme_path = [sphinx_rtd_theme.get_html_theme_path()]
