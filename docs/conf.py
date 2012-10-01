# -*- coding: utf-8 -*-
#
import sys, os
sys.path.insert(0, os.path.abspath('../readthedocs'))
import settings.sqlite
from django.core.management import setup_environ
setup_environ(settings.sqlite)

extensions = ['sphinx.ext.autodoc', 'sphinx.ext.intersphinx', 'sphinx_http_domain']
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
on_rtd = os.environ.get('READTHEDOCS', None) == 'True'
if on_rtd:
    html_theme = 'default'
else:
    html_theme = 'nature'
html_static_path = ['_static']
htmlhelp_basename = 'ReadTheDocsdoc'
latex_documents = [
  ('index', 'ReadTheDocs.tex', u'Read The Docs Documentation',
   u'Eric Holscher, Charlie Leifer, Bobby Grace', 'manual'),
]
man_pages = [
    ('index', 'read-the-docs', u'Read The Docs Documentation',
     [u'Eric Holscher, Charlie Leifer, Bobby Grace'], 1)
]
