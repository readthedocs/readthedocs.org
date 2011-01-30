# -*- coding: utf-8 -*-

import sys, os
extensions = []
templates_path = ['{{ template_dir }}', 'templates', '_templates', '.templates']
source_suffix = '{{ project.suffix }}'
master_doc = 'index'
project = u'{{ project.name }}'
copyright = u'{{ project.copyright }}'
version = '{{ project.version }}'
release = '{{ project.version }}'
exclude_patterns = ['_build']
pygments_style = 'sphinx'
html_theme = '{{ project.theme }}'
html_theme_path = ['.', '_theme', '.theme']
htmlhelp_basename = '{{ project.slug }}'
file_insertion_enabled = False
latex_documents = [
  ('index', '{{ project.slug }}.tex', u'{{ project.name }} Documentation',
   u'{{ project.copyright }}', 'manual'),
]
