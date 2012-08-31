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



#Add RTD Template Path.
if 'templates_path' in locals():
    templates_path.insert(0, '/Users/eric/projects/readthedocs.org/readthedocs/templates/sphinx')
else:
    templates_path = ['/Users/eric/projects/readthedocs.org/readthedocs/templates/sphinx', 'templates', '_templates', '.templates']

#Add RTD Static Path. Add to the end because it overwrites previous files.
if 'html_static_path' in locals():
    html_static_path.append('/Users/eric/projects/readthedocs.org/readthedocs/templates/sphinx/_static')
else:
    html_static_path = ['_static', '/Users/eric/projects/readthedocs.org/readthedocs/templates/sphinx/_static']

#Add RTD CSS File only if they aren't overriding it already
using_rtd_theme = False
if project == "Python":
    #Do nothing for Python theme-wise
    pass
elif 'html_theme' in locals():
    if html_theme in ['default']:
        if not 'html_style' in locals():
            html_style = 'rtd.css'
            html_theme = 'default'
            html_theme_options = {}
            using_rtd_theme = True
else:
    html_style = 'rtd.css'
    html_theme = 'default'
    html_theme_options = {}
    using_rtd_theme = True

#Add sponsorship and project information to the template context.
context = {
    'using_theme': using_rtd_theme,
    'current_version': "latest",
    'MEDIA_URL': "/media/",
    'versions': [
    ("latest", "/docs/read-the-docs/en/latest/"),
    ("awesome", "/docs/read-the-docs/en/awesome/"),
    ("0.2.2", "/docs/read-the-docs/en/0.2.2/"),
    ("0.2.1", "/docs/read-the-docs/en/0.2.1/"),
    ],
    'slug': 'read-the-docs',
    'name': u'Read The Docs',
    'badge_revsys': False,
    'analytics_code': '',
}
if 'html_context' in locals():
    html_context.update(context)
else:
    html_context = context
