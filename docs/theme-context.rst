Read the Docs data passed to Sphinx build context
=================================================

Before calling `sphinx-build` to render your docs, Read the Docs injects some
extra context in the templates by using the `html_context Sphinx setting`_ in
the ``conf.py`` file. This extra context is used by the Read the Docs Sphinx Theme
to add additional features to the built documentation

.. _html_context Sphinx setting: http://www.sphinx-doc.org/en/stable/config.html#confval-html_context

Context injected
----------------

Here is the full list of values injected by Read the Docs as a Python dictionary.
Note that this dictionary is injected under the main key `readthedocs`:


.. code:: python

    'readthedocs': {
        'version': {
            'pk': int,
            'name': str,
            'slug': str,
            'downloads': {
                'pdf: str,
                'htmlzip': str,
                'epub': str
            },
            'resource_uri': '/api/v2/version/{pk}/'
        },
        'project': {
            'pk': int
            'name': str,
            'slug': str,
            'canonical_url': str,
            'resource_uri': '/api/v2/project/{pk}/'
        },
        'sphinx': {
            'html_theme': str,
            'source_suffix': str,
        },
        'analytics': {
            'user_analytics_code': str,
            'global_analytics_code': str
        },
        'vcs': {
            'type': str,  # 'bitbucket', 'github' or 'gitlab'
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


.. note::

   By design, Read the Docs passes only static information to `sphinx-build`
   to avoid versions to be inconsistent in case the project is updated after the version is built.
   In case you need more information than the context supplies here, you will
   need to use :doc:`Read the Docs Public API <api>` to retrieve fresh data about the project
   (e.g. know if the current version is the `latest` or `stable`, get all versions of a project, etc).


Using Read the Docs context in your theme
-----------------------------------------

In case you want to access to this data from your theme, you can use it like this:

.. code:: html

    {% if readthedocs.vcs.type == 'github' %}
        <a href="https://github.com/{{ readthedocs.vcs.user }}/{{ readthedocs.vcs.repo }}
        /blob/{{ readthedocs.vcs.version }}{{ readthedocs.vcs.conf_py_path }}{{ pagename }}.rst">
        Show on GitHub</a>
    {% endif %}


.. note::

   In this example, we are using ``pagename`` which is a Sphinx variable
   representing the name of the page you are on. More information about Sphinx
   variables can be found on `Sphinx documentation`_.


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


.. note::

   Take into account that the Read the Docs context is injected after your definition of ``html_context`` so,
   it's not possible to override Read the Docs context values.
