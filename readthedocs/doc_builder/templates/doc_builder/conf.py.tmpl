{% load projects_tags %}


###########################################################################
#          auto-created readthedocs.org specific configuration            #
###########################################################################


#
# The following code was added during an automated build on readthedocs.org
# It is auto created and injected for every build. The result is based on the
# conf.py.tmpl file found in the readthedocs.org codebase:
# https://github.com/rtfd/readthedocs.org/blob/main/readthedocs/doc_builder/templates/doc_builder/conf.py.tmpl
#
# Note: this file shouldn't rely on extra dependencies.

import importlib
import sys
import os.path

# Borrowed from six.
PY3 = sys.version_info[0] == 3
string_types = str if PY3 else basestring

from sphinx import version_info

# Get suffix for proper linking to GitHub
# This is deprecated in Sphinx 1.3+,
# as each page can have its own suffix
if globals().get('source_suffix', False):
    if isinstance(source_suffix, string_types):
        SUFFIX = source_suffix
    elif isinstance(source_suffix, (list, tuple)):
        # Sphinx >= 1.3 supports list/tuple to define multiple suffixes
        SUFFIX = source_suffix[0]
    elif isinstance(source_suffix, dict):
        # Sphinx >= 1.8 supports a mapping dictionary for multiple suffixes
        SUFFIX = list(source_suffix.keys())[0]  # make a ``list()`` for py2/py3 compatibility
    else:
        # default to .rst
        SUFFIX = '.rst'
else:
    SUFFIX = '.rst'

# Add RTD Static Path. Add to the end because it overwrites previous files.
if not 'html_static_path' in globals():
    html_static_path = []
if os.path.exists('_static'):
    html_static_path.append('_static')

# Define this variable in case it's not defined by the user.
# It defaults to `alabaster` which is the default from Sphinx.
# https://www.sphinx-doc.org/en/master/usage/configuration.html#confval-html_theme
html_theme = globals().get('html_theme', 'alabaster')

#Add project information to the template context.
context = {
    'html_theme': html_theme,
    'current_version': "{{ version.verbose_name }}",
    'version_slug': "{{ version.slug }}",
    'MEDIA_URL': "{{ settings.MEDIA_URL }}",
    'STATIC_URL': "{{ settings.STATIC_URL }}",
    'PRODUCTION_DOMAIN': "{{ settings.PRODUCTION_DOMAIN }}",
    'proxied_static_path': "{{ proxied_static_path }}",
    'versions': [{% for version in versions %}
    ("{{ version.slug }}", "/{{ version.project.language }}/{{ version.slug}}/"),{% endfor %}
    ],
    'downloads': [ {% for key, val in downloads.items %}
    ("{{ key }}", "{{ val }}"),{% endfor %}
    ],
    'subprojects': [ {% for slug, url in subproject_urls %}
        ("{{ slug }}", "{{ url }}"),{% endfor %}
    ],
    'slug': '{{ project.slug }}',
    'name': u'{{ project.name }}',
    'rtd_language': u'{{ project.language }}',
    'programming_language': u'{{ project.programming_language }}',
    'canonical_url': '{{ project.get_canonical_url }}',
    'analytics_code': '{{ project.analytics_code }}',
    'single_version': {{ project.single_version }},
    'conf_py_path': '{{ conf_py_path }}',
    'api_host': '{{ api_host }}',
    'github_user': '{{ github_user }}',
    'proxied_api_host': '{{ project.proxied_api_host }}',
    'github_repo': '{{ github_repo }}',
    'github_version': '{{ github_version }}',
    'display_github': {{ display_github }},
    'bitbucket_user': '{{ bitbucket_user }}',
    'bitbucket_repo': '{{ bitbucket_repo }}',
    'bitbucket_version': '{{ bitbucket_version }}',
    'display_bitbucket': {{ display_bitbucket }},
    'gitlab_user': '{{ gitlab_user }}',
    'gitlab_repo': '{{ gitlab_repo }}',
    'gitlab_version': '{{ gitlab_version }}',
    'display_gitlab': {{ display_gitlab }},
    'READTHEDOCS': True,
    'using_theme': (html_theme == "default"),
    'new_theme': (html_theme == "sphinx_rtd_theme"),
    'source_suffix': SUFFIX,
    'ad_free': {% if project.show_advertising %}False{% else %}True{% endif %},
    'docsearch_disabled': {{ docsearch_disabled }},
    'user_analytics_code': '{{ project.analytics_code|default_if_none:'' }}',
    'global_analytics_code': {% if project.analytics_disabled %}None{% else %}'{{ settings.GLOBAL_ANALYTICS_CODE }}'{% endif %},
    'commit': {% if project.repo_type == 'git' %}'{{ commit|slice:"8" }}'{% else %}'{{ commit }}'{% endif %},
}

# For sphinx >=1.8 we can use html_baseurl to set the canonical URL.
# https://www.sphinx-doc.org/en/master/usage/configuration.html#confval-html_baseurl
if version_info >= (1, 8):
    if not globals().get('html_baseurl'):
        html_baseurl = context['canonical_url']
    context['canonical_url'] = None


{# Provide block for extending context data from child template #}
{% block extra_context %}{% endblock %}

if 'html_context' in globals():
    for key in context:
        if key not in html_context:
            html_context[key] = context[key]
else:
    html_context = context

# Add custom RTD extension
if 'extensions' in globals():
    # Insert at the beginning because it can interfere
    # with other extensions.
    # See https://github.com/rtfd/readthedocs.org/pull/4054
    extensions.insert(0, "readthedocs_ext.readthedocs")
else:
    extensions = ["readthedocs_ext.readthedocs"]

# Add External version warning banner to the external version documentation
if '{{ version.type }}' == 'external':
    extensions.insert(1, "readthedocs_ext.external_version_warning")
    readthedocs_vcs_url = '{{ vcs_url }}'
    readthedocs_build_url = '{{ build_url }}'

project_language = '{{ project.language }}'

# User's Sphinx configurations
language_user = globals().get('language', None)
latex_engine_user = globals().get('latex_engine', None)
latex_elements_user = globals().get('latex_elements', None)

# Remove this once xindy gets installed in Docker image and XINDYOPS
# env variable is supported
# https://github.com/rtfd/readthedocs-docker-images/pull/98
latex_use_xindy = False

chinese = any([
    language_user in ('zh_CN', 'zh_TW'),
    project_language in ('zh_CN', 'zh_TW'),
])

japanese = any([
    language_user == 'ja',
    project_language == 'ja',
])

if chinese:
    latex_engine = latex_engine_user or 'xelatex'

    latex_elements_rtd = {
        'preamble': '\\usepackage[UTF8]{ctex}\n',
    }
    latex_elements = latex_elements_user or latex_elements_rtd
elif japanese:
    latex_engine = latex_engine_user or 'platex'

# Make sure our build directory is always excluded
exclude_patterns = globals().get('exclude_patterns', [])
exclude_patterns.extend(['_build'])
