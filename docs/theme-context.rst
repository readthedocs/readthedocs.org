Read the Docs data passed to Sphinx build context
=================================================

Before calling `sphinx-build` to render your docs, Read the Docs injects some
extra context in the templates by using the ``html_context`` Sphinx setting in
the ``conf.py`` file. This extra context allows Read the Docs to add some
features like "Edit on GitHub" and use a custom Analytics code, among others.


Context injected by default
---------------------------

Here is the full list of values injected by Read the Docs as a Python
dictionary. Note that this dictionary is injected under the main key
`readthedocs`:


.. code:: python

    'readthedocs': {
        'version': {
            'name': str,
            'slug': str,
            'latest': bool,
            'stable': bool,
        },
        'project': {
            'name': str,
            'slug': str,
            'rtd_language': str,  # can be different than language in conf.py
            'canonical_url': str,
            'single_version': bool,
            'versions': [
                {
                    'slug': str,
                    'href': str
                }
            ],
            'subprojects': [
                {
                    'slug': str,
                    'href': str
                }
            ]
        },
        'build': {
            'html_theme': str,
            'source_suffix': str,
            'api_host': str,
            'user_analytics_code': str,
            'global_analytics_code': str
        },
        'vcs': {
            'type': str,  # 'bitbucket', 'github' or 'gitlab'
            'user': str,
            'repo': str,
            'commit': str,
            'version': str,
            'display': bool
            'conf_py_path': str
        },
        'meta': {
            'READTHEDOCS': True,
            'MEDIA_URL': str, 
            'PRODUCTION_DOMAIN': str
        }
    }


Using Read the Docs context in your theme
-----------------------------------------

In case you want to access to this data from your theme, you can use it like
this:

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
