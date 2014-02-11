Frequently Asked Questions
==========================

My project isn't building with autodoc
--------------------------------------

First, you should check out the Builds tab of your project. That records all of the build attempts that RTD has made to build your project. If you see ``ImportError`` messages for custom Python modules, you should enable the virtualenv feature in the Admin page of your project, which will install your project into a virtualenv, and allow you to specify a ``requirements.txt`` file for your project.

If you are still seeing errors because of C library dependencies, please see the below section about that.

How do I change behavior for Read the Docs?
-------------------------------------------

When RTD builds your project, it sets the `READTHEDOCS` environment variable to the string `True`. So within your Sphinx's conf.py file, you can vary the behavior based on this. For example::

    import os
    on_rtd = os.environ.get('READTHEDOCS', None) == 'True'
    if on_rtd:
        html_theme = 'default'
    else:
        html_theme = 'nature'

The ``READTHEDOCS`` variable is also available in the Sphinx build environment, and will be set to ``True`` when building on RTD::

    {% if READTHEDOCS %}
    Woo
    {% endif %}

I get import errors on libraries that depend on C modules
----------------------------------------------------------

.. note::
    Another use case for this is when you have a module with a C extension.

This happens because our build system doesn't have the dependencies for building your project. This happens with things like libevent and mysql, and other python things that depend on C libraries. We can't support installing random C binaries on our system, so there is another way to fix these imports.

You can mock out the imports for these modules in your conf.py with the following snippet::

    import sys

    class Mock(object):
        
        __all__ = []
       
        def __init__(self, *args, **kwargs):
            pass

        def __call__(self, *args, **kwargs):
            return Mock()

        @classmethod
        def __getattr__(cls, name):
            if name in ('__file__', '__path__'):
                return '/dev/null'
            elif name[0] == name[0].upper():
                mockType = type(name, (), {})
                mockType.__module__ = __name__
                return mockType
            else:
                return Mock()

    MOCK_MODULES = ['pygtk', 'gtk', 'gobject', 'argparse']
    for mod_name in MOCK_MODULES:
        sys.modules[mod_name] = Mock()

Of course, replacing `MOCK_MODULES` with the modules that you want to mock out.

Can I make search engines only see one version of my docs?
----------------------------------------------------------

You can do this for Google at least with a canonical link tag.
It should look like:

.. code-block:: jinja

        <link rel="canonical" href="http://ericholscher.com/
        {%- for word in pagename.split('/') -%}
            {%- if word != 'index' -%}
                {%- if word != '' -%}
                    {{ word }}/
                {%- endif -%}
            {%- endif -%}
        {%- endfor -%}
        {% if builder == "dirhtml" %}/{% else %}.html{% endif %}
        ">


Deleting a stale or broken build environment
--------------------------------------------

RTD doesn't expose this in the UI, but it is possible to remove the build directory of your project. If you want to remove a build environment for your project, hit http://readthedocs.org/wipe/<project_slug>/<version_slug>/. You must be logged in to do this.


How do I host multiple projects on one CNAME?
---------------------------------------------

We support the concept of Subprojects.
If you add a subproject to a project,
that documentation will also be served under the parent project's subdomain.

For example,
Kombu is a subproject of celery,
so you can access it on the `celery.readthedocs.org` domain:

http://celery.readthedocs.org/projects/kombu/en/latest/

This also works the same for CNAME's:

http://docs.celeryproject.org/projects/kombu/en/latest/

You can add subprojects in the Admin section for your project.

Where do I need to put my docs for RTD to find it?
--------------------------------------------------

Read the Docs will crawl your project looking for a ``conf.py``. Where it finds the ``conf.py``, it will run ``sphinx-build`` in that directory. So as long as you only have one set of sphinx documentation in your project, it should Just Work.

I want to use the Blue/Default Sphinx theme
-------------------------------------------

We think that our theme is badass, and better than the default for many reasons. Some people don't like change though :), so there is a hack that will let you keep using the default theme. If you set the ``html_style`` variable in your ``conf.py``, it should default to using the default theme. The value of this doesn't matter, and can be set to ``/default.css`` for default behavior.

I want to use the Read the Docs theme locally
---------------------------------------------

There is a repository for that: https://github.com/snide/sphinx_rtd_theme.
Simply follow the instructions in the README.

Image scaling doesn't work in my documentation
-----------------------------------------------

Image scaling in docutils depends on PIL. PIL is installed in the system that RTD runs on. However, if you are using the virtualenv building option, you will likely need to include PIL in your requirements for your project.

I want comments in my docs
--------------------------

RTD doesn't have explicit support for this. That said, a tool like `Disqus`_ can be used for this purpose on RTD.

.. _Disqus: http://disqus.com/

How do I support multiple languages of documentation?
-----------------------------------------------------

This is something that has been long planned. In fact, we have a language string in the URLs! However, it isn't currently modeled and supported in the code base. However, you can specify the conf.py file to use for a specific version of the documentation. So, you can create a project for each language of documentation, and do it that way. You can then CNAME different domains on your docs to them. Requests does something like this with it's translations:

 * http://ja.python-requests.org/en/latest/index.html
 * http://docs.python-requests.org/en/latest/index.html

Do I need to be whitelisted?
----------------------------

No. Whitelisting has been removed as a concept in Read the Docs. You should have access to all of the features already.

Does Read The Docs work well with "legible" docstrings?
-------------------------------------------------------

Yes. One criticism of Sphinx is that its annotated docstrings are too
dense and difficult for humans to read. In response, many projects
have adopted customized docstring styles that are simultaneously
informative and legible. The
`NumPy <https://github.com/numpy/numpy/blob/master/doc/HOWTO_DOCUMENT.rst.txt>`_
and
`Google <http://google-styleguide.googlecode.com/svn/trunk/pyguide.html?showone=Comments#Comments>`_
styles are two popular docstring formats.  Fortunately, the default
Read The Docs theme handles both formats just fine, provided
your ``conf.py`` specifies an appropriate Sphinx extension that
knows how to convert your customized docstrings.  Two such extensions
are `numpydoc <https://github.com/numpy/numpydoc>`_ and
`napoleon <http://sphinxcontrib-napoleon.readthedocs.org>`_. Only
``napoleon`` is able to handle both docstring formats. Its default
output more closely matches the format of standard Sphinx annotations,
and as a result, it tends to look a bit better with the default theme.
