Read the Docs data passed to Sphinx build context
=================================================

Before calling `sphinx-build` to render your docs, Read the Docs injects some
extra context in the templates by using the `html_context Sphinx setting`_ in the ``conf.py`` file.
This extra context can be used to build some awesome features in your own theme.

.. _html_context Sphinx setting: http://www.sphinx-doc.org/en/stable/config.html#confval-html_context

.. warning::

    This design document details future features that are **not yet implemented**.
    To discuss this document, please get in touch in the `issue tracker`_.

.. _issue tracker: https://github.com/rtfd/readthedocs.org/issues

.. note::

   The `Read the Docs Sphinx Theme`_ uses this context to add additional features to the built documentation.

.. _Read the Docs Sphinx Theme: https://sphinx-rtd-theme.readthedocs.io/en/latest/

Context injected
----------------

Here is the full list of values injected by Read the Docs as a Python dictionary.
Note that this dictionary is injected under the main key `readthedocs`:


.. This context comes from ``readthedocs.doc_builder.backends.sphinx.BaseSphinx.get_config_params`` class.
   The source code is at, https://github.com/rtfd/readthedocs.org/blob/0c547f47fb9dffbeb17e4e9ccf205a10caf31189/readthedocs/doc_builder/backends/sphinx.py#L65

.. code:: python

   {
       'readthedocs': {
           'v1': {
               'version': {
                   'id': int,
                   'slug': str,
                   'verbose_name': str,
                   'identifier': str,
                   'type': str,
                   'build_date': str,
                   'downloads': {
                       'pdf': str,
                       'htmlzip': str,
                       'epub': str
                   },
                   'links': [{
                       'href': 'https://readthedocs.org/api/v2/version/{id}/',
                       'rel': 'self'
                   }],
               },
               'project': {
                   'id': int,
                   'name': str,
                   'slug': str,
                   'description': str,
                   'language': str,
                   'canonical_url': str,
                   'subprojects': [{
                       'id': int,
                       'name': str,
                       'slug': str,
                       'description': str,
                       'language': str,
                       'canonical_url': str,
                       'links': [{
                           'href': 'https://readthedocs.org/api/v2/project/{id}/',
                           'rel': 'self'
                       }]
                   }],
                   'links': [{
                       'href': 'https://readthedocs.org/api/v2/project/{id}/',
                       'rel': 'self'
                   }]
               },
               'sphinx': {
                   'html_theme': str,
                   'source_suffix': str
               },
               'analytics': {
                   'user_analytics_code': str,
                   'global_analytics_code': str
               },
               'vcs': {
                   'type': str,  # 'bitbucket', 'github', 'gitlab' or 'svn'
                   'user': str,
                   'repo': str,
                   'commit': str,
                   'version': str,
                   'display': bool,
                   'conf_py_path': str
               },
               'meta': {
                   'API_HOST': str,
                   'MEDIA_URL': str,
                   'PRODUCTION_DOMAIN': str,
                   'READTHEDOCS': True
               }
           }
       }
   }


.. warning::

   Read the Docs passes information to `sphinx-build` that may change in the future
   (e.g. at the moment of building the version `0.6` this was the `latest`
   but then `0.7` and `0.8` were added to the project and also built under Read the Docs)
   so it's your responsibility to use this context in a proper way.

   In case you want *fresh data* at the moment of reading your documentation,
   you should consider using the :doc:`Read the Docs Public API </api/index>` via Javascript.


Using Read the Docs context in your theme
-----------------------------------------

In case you want to access to this data from your theme, you can use it like this:

.. code:: html

    {% if readthedocs.v1.vcs.type == 'github' %}
        <a href="https://github.com/{{ readthedocs.v1.vcs.user }}/{{ readthedocs.v1.vcs.repo }}
        /blob/{{ readthedocs.v1.vcs.version }}{{ readthedocs.v1.vcs.conf_py_path }}{{ pagename }}.rst">
        Show on GitHub</a>
    {% endif %}


.. note::

   In this example, we are using ``pagename`` which is a Sphinx variable
   representing the name of the page you are on. More information about Sphinx
   variables can be found in the `Sphinx documentation`_.


.. _`Sphinx documentation`: http://www.sphinx-doc.org/en/stable/templating.html#global-variables


Customizing the context
-----------------------

In case you want to add some extra context you will have to declare your own
``html_context`` in your ``conf.py`` like this:

.. code:: python

   html_context = {
       'author': 'My Name',
       'date': datetime.date.today().strftime('%d/%m/%y'),
   }

and use it inside your theme as:

.. code:: html

    <p>This documentation was written by {{ author }} on {{ date }}.</p>


.. warning::

   Take into account that the Read the Docs context is injected after your definition of ``html_context`` so,
   it's not possible to override Read the Docs context values.
