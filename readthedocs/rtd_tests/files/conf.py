# -*- coding: utf-8 -*-

from __future__ import division, print_function, unicode_literals

from datetime import datetime

from recommonmark.parser import CommonMarkParser

extensions = []
templates_path = ['templates', '_templates', '.templates']
source_suffix = ['.rst', '.md']
source_parsers = {
            '.md': CommonMarkParser,
        }
master_doc = 'index'
project = u'Pip'
copyright = str(datetime.now().year)
version = '0.8.1'
release = '0.8.1'
exclude_patterns = ['_build']
pygments_style = 'sphinx'
htmlhelp_basename = 'pip'
html_theme = 'sphinx_rtd_theme'
file_insertion_enabled = False
latex_documents = [
  ('index', 'pip.tex', u'Pip Documentation',
   u'', 'manual'),
]
