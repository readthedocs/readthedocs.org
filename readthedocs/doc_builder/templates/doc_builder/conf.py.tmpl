{% load projects_tags %}


###########################################################################
#          auto-created readthedocs.org specific configuration            #
###########################################################################


#
# The following code was added during an automated build on readthedocs.org
# It is auto created and injected for every build. The result is based on the
# conf.py.tmpl file found in the readthedocs.org codebase:
# https://github.com/rtfd/readthedocs.org/blob/master/readthedocs/doc_builder/templates/doc_builder/conf.py.tmpl
#


import sys
import os.path
from six import string_types

from sphinx import version_info

# Get suffix for proper linking to GitHub
# This is deprecated in Sphinx 1.3+,
# as each page can have its own suffix
if globals().get('source_suffix', False):
    if isinstance(source_suffix, string_types):
        SUFFIX = source_suffix
    else:
        SUFFIX = source_suffix[0]
else:
    SUFFIX = '.rst'

# Add RTD Static Path. Add to the end because it overwrites previous files.
if not 'html_static_path' in globals():
    html_static_path = []
if os.path.exists('_static'):
    html_static_path.append('_static')
html_static_path.append('{{ static_path }}')

# Add RTD Theme only if they aren't overriding it already
using_rtd_theme = False
if 'html_theme' in globals():
    if html_theme in ['default']:
        # Allow people to bail with a hack of having an html_style
        if not 'html_style' in globals():
            import sphinx_rtd_theme
            html_theme = 'sphinx_rtd_theme'
            html_style = None
            html_theme_options = {}
            if 'html_theme_path' in globals():
                html_theme_path.append(sphinx_rtd_theme.get_html_theme_path())
            else:
                html_theme_path = [sphinx_rtd_theme.get_html_theme_path()]

            using_rtd_theme = True
else:
    import sphinx_rtd_theme
    html_theme = 'sphinx_rtd_theme'
    html_style = None
    html_theme_options = {}
    if 'html_theme_path' in globals():
        html_theme_path.append(sphinx_rtd_theme.get_html_theme_path())
    else:
        html_theme_path = [sphinx_rtd_theme.get_html_theme_path()]
    using_rtd_theme = True

if globals().get('websupport2_base_url', False):
    websupport2_base_url = '{{ api_host }}/websupport'
    if 'http' not in settings.MEDIA_URL:
        websupport2_static_url = '{{ settings.STATIC_URL }}'
    else:
        websupport2_static_url = '{{ settings.MEDIA_URL }}/static'


#Add project information to the template context.
context = {
    'using_theme': using_rtd_theme,
    'html_theme': html_theme,
    'current_version': "{{ current_version }}",
    'MEDIA_URL': "{{ settings.MEDIA_URL }}",
    'PRODUCTION_DOMAIN': "{{ settings.PRODUCTION_DOMAIN }}",
    'versions': [{% for version in versions %}
    ("{{ version.slug }}", "/{{ version.project.language }}/{{ version.slug}}/"),{% endfor %}
    ],
    'downloads': [ {% for key, val in downloads.items %}
    ("{{ key }}", "{{ val }}"),{% endfor %}
    ],
    'subprojects': [ {% for slug, url in project.get_subproject_urls %}
        ("{{ slug }}", "{{ url }}"),{% endfor %}
    ],
    'slug': '{{ project.slug }}',
    'name': u'{{ project.name }}',
    'rtd_language': u'{{ project.language }}',
    'canonical_url': '{{ project.get_canonical_url }}',
    'analytics_code': '{{ project.analytics_code }}',
    'single_version': {{ project.single_version }},
    'conf_py_path': '{{ conf_py_path }}',
    'api_host': '{{ api_host }}',
    'github_user': '{{ github_user }}',
    'github_repo': '{{ github_repo }}',
    'github_version': '{{ github_version }}',
    'display_github': {{ display_github }},
    'bitbucket_user': '{{ bitbucket_user }}',
    'bitbucket_repo': '{{ bitbucket_repo }}',
    'bitbucket_version': '{{ bitbucket_version }}',
    'display_bitbucket': {{ display_bitbucket }},
    'READTHEDOCS': True,
    'using_theme': (html_theme == "default"),
    'new_theme': (html_theme == "sphinx_rtd_theme"),
    'source_suffix': SUFFIX,
    'user_analytics_code': '{{ project.analytics_code|default_if_none:'' }}',
    'global_analytics_code': '{{ settings.GLOBAL_ANALYTICS_CODE }}',
    {% if project.repo_type == 'git' %}
    'commit': '{{ commit|slice:"8" }}',
    {% else %}
    'commit': '{{ commit }}',
    {% endif %}
}
if 'html_context' in globals():
    html_context.update(context)
else:
    html_context = context

# Add custom RTD extension
if 'extensions' in globals():
    extensions.append("readthedocs_ext.readthedocs")
else:
    extensions = ["readthedocs_ext.readthedocs"]
