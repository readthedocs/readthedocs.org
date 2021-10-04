Frequently Asked Questions
==========================

My project isn't building correctly
-----------------------------------

First, you should check out the Builds tab of your project.
That records all of the build attempts that RTD has made to build your project.
If you see ``ImportError`` messages for custom Python modules,
see our section on :ref:`faq:My documentation requires additional dependencies`.

If you are still seeing errors because of C library dependencies,
please see :ref:`faq:I get import errors on libraries that depend on C modules`.


Help, my build passed but my documentation page is 404 Not Found!
-----------------------------------------------------------------

This often happens because you don't have an `index.html` file being generated.
Make sure you have one of the following files:

    * `index.rst`
    * `index.md`

At the top level of your built documentation,
otherwise we aren't able to serve a "default" index page.

To test if your docs actually built correctly,
you can navigate to a specific page (`/en/latest/README.html` for example).


My documentation requires additional dependencies
-------------------------------------------------

For most Python dependencies, you can can specify a requirements file
which details your dependencies. See our guide on :ref:`guides/reproducible-builds:using a configuration file`.
You can also set your project documentation to install your project itself
as a dependency.

If your project or its dependencies rely on C libraries,
see :ref:`faq:I get import errors on libraries that depend on C modules`.


My project requires some additional settings
--------------------------------------------

If this is just a dependency issue,
see :ref:`faq:My documentation requires additional dependencies`.

Read the Docs offers some settings which can be used for a variety of purposes.
To enable these settings,
please send an email to support@readthedocs.org and we will change the settings for the project.
Read more about these settings :doc:`here <feature-flags>`.


I get import errors on libraries that depend on C modules
---------------------------------------------------------

.. note::

   Another use case for this is when you have a module with a C extension.

This happens because our build system doesn't have the dependencies for building your project.
This happens with things like ``libevent``, ``mysql``, and other python packages that depend on C libraries.
We can't support installing random C binaries on our system, so there is another way to fix these imports.

With Sphinx you can use the built-in `autodoc_mock_imports`_ for mocking.
If such libraries are installed via ``setup.py``, you also will need to remove all the C-dependent libraries from your ``install_requires`` in the RTD environment.

.. _autodoc_mock_imports: http://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html#confval-autodoc_mock_imports


How do I change behavior when building with Read the Docs?
----------------------------------------------------------

When RTD builds your project, it sets the :envvar:`READTHEDOCS` environment
variable to the string ``'True'``. So within your Sphinx :file:`conf.py` file, you
can vary the behavior based on this. For example::

    import os
    on_rtd = os.environ.get('READTHEDOCS') == 'True'
    if on_rtd:
        html_theme = 'default'
    else:
        html_theme = 'nature'

The :envvar:`READTHEDOCS` variable is also available in the Sphinx build
environment, and will be set to ``True`` when building on RTD::

    {% if READTHEDOCS %}
    Woo
    {% endif %}



`Client Error 401` when building documentation
----------------------------------------------

If you did not install the `test_data` fixture during the installation
instructions, you will get the following error::

    slumber.exceptions.HttpClientError: Client Error 401: http://localhost:8000/api/v1/version/

This is because the API admin user does not exist, and so cannot authenticate.
You can fix this by loading the test_data::

    ./manage.py loaddata test_data

If you'd prefer not to install the test data, you'll need to provide a database
account for the builder to use. You can provide these credentials by editing the
following settings::

    SLUMBER_USERNAME = 'test'
    SLUMBER_PASSWORD = 'test'


Deleting a stale or broken build environment
--------------------------------------------

See :doc:`guides/wipe-environment`.


How do I host multiple projects on one custom domain?
-----------------------------------------------------

We support the concept of subprojects, which allows multiple projects to share a
single domain. If you add a subproject to a project, that documentation will
be served under the parent project's subdomain or custom domain.

For example,
Kombu is a subproject of Celery,
so you can access it on the `celery.readthedocs.io` domain:

https://celery.readthedocs.io/projects/kombu/en/latest/

This also works the same for custom domains:

http://docs.celeryproject.org/projects/kombu/en/latest/

You can add subprojects in the project admin dashboard.

For details on custom domains, see our documentation on :doc:`/custom_domains`.


Where do I need to put my docs for RTD to find it?
--------------------------------------------------

Read the Docs will crawl your project looking for a ``conf.py``. Where it finds the ``conf.py``,
it will run ``sphinx-build`` in that directory.
So as long as you only have one set of sphinx documentation in your project, it should Just Work.

You can specify an exact path to your documentation using a Read the Docs :doc:`config-file/index`.


I want to use the Blue/Default Sphinx theme
-------------------------------------------

We think that our theme is badass,
and better than the default for many reasons.
Some people don't like change though |:smile:|,
so there is a hack that will let you keep using the default theme.
If you set the ``html_style`` variable in your ``conf.py``,
it should default to using the default theme.
The value of this doesn't matter, and can be set to ``/default.css`` for default behavior.


I want to use the Read the Docs theme locally
---------------------------------------------

There is a repository for that: https://github.com/readthedocs/sphinx_rtd_theme.
Simply follow the instructions in the README.


Image scaling doesn't work in my documentation
-----------------------------------------------

Image scaling in docutils depends on PIL. PIL is installed in the system that RTD runs on. However, if you are using the virtualenv building option, you will likely need to include PIL in your requirements for your project.


I want comments in my docs
--------------------------

RTD doesn't have explicit support for this.
That said, a tool like `Disqus`_ (and the `sphinxcontrib-disqus`_ plugin) can be used for this purpose on RTD.

.. _Disqus: https://disqus.com/
.. _sphinxcontrib-disqus: https://pypi.python.org/pypi/sphinxcontrib-disqus


How do I support multiple languages of documentation?
-----------------------------------------------------

See the section on :doc:`localization`.


Does Read The Docs work well with "legible" docstrings?
-------------------------------------------------------

Yes. One criticism of Sphinx is that its annotated docstrings are too
dense and difficult for humans to read. In response, many projects
have adopted customized docstring styles that are simultaneously
informative and legible. The
`NumPy <https://numpydoc.readthedocs.io/en/latest/format.html#docstring-standard>`__
and
`Google <https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings>`__
styles are two popular docstring formats.  Fortunately, the default
Read The Docs theme handles both formats just fine, provided
your ``conf.py`` specifies an appropriate Sphinx extension that
knows how to convert your customized docstrings.  Two such extensions
are `numpydoc <https://github.com/numpy/numpydoc>`_ and
`napoleon <http://sphinxcontrib-napoleon.readthedocs.io>`_. Only
``napoleon`` is able to handle both docstring formats. Its default
output more closely matches the format of standard Sphinx annotations,
and as a result, it tends to look a bit better with the default theme.

.. note::

   To use these extensions you need to specify the dependencies on your project
   by following this :ref:`guide <guides/reproducible-builds:using a configuration file>`.

Can I document a python package that is not at the root of my repository?
-------------------------------------------------------------------------

Yes. The most convenient way to access a python package for example via
`Sphinx's autoapi`_ in your documentation is to use the *Install your project
inside a virtualenv using setup.py install* option in the admin panel of
your project. However this assumes that your ``setup.py`` is in the root of
your repository.

If you want to place your package in a different directory or have multiple
python packages in the same project, then create a pip requirements file. You
can specify the relative path to your package inside the file.
For example you want to keep your python package in the ``src/python``
directory, then create a ``requirements.txt`` file with the
following contents::

    src/python/

Please note that the path must be relative to the working directory where ``pip`` is launched,
rather than the directory where the requirements file is located.
Therefore, even if you want to move the requirements file to a ``requirements/`` directory,
the example path above would work.

You can customize the path to your requirements file and any other installed dependency
using a Read the Docs :doc:`config-file/index`.

.. _Sphinx's autoapi: http://sphinx-doc.org/ext/autodoc.html
.. _pip requirements file: https://pip.pypa.io/en/stable/user_guide.html#requirements-files


I need to install a package in a environment with pinned versions
-----------------------------------------------------------------

To ensure proper installation of a python package, the ``pip`` :ref:`install method <config-file/v2:python.install>` will automatically upgrade every dependency to its most recent version in case they aren't pinned by the package definition.
If instead you'd like to pin your dependencies outside the package, you can add this line to your requirements or environment file (if you are using Conda).

In your ``requirements.txt`` file::

    # path to the directory containing setup.py relative to the project root
    -e .

In your Conda environment file (``environment.yml``)::

    # path to the directory containing setup.py relative to the environment file
    -e ..


Can I use Anaconda Project and ``anaconda-project.yml``?
--------------------------------------------------------

Yes. With ``anaconda-project>=0.8.4`` you can use the `Anaconda Project`_ configuration
file ``anaconda-project.yaml`` (or ``anaconda-project.yml``) directly in place of a
Conda environment file by using ``dependencies:`` as an alias for ``packages:``.

I.e., your ``anaconda-project.yaml`` file can be used as a ``conda.environment`` config
in the ``.readthedocs.yaml`` config file if it contains::

    dependencies:
      - python=3.9
      - scipy
      ...
      
.. _Anaconda Project: https://anaconda-project.readthedocs.io/en/latest/


How can I avoid search results having a deprecated version of my docs?
----------------------------------------------------------------------

If readers search something related to your docs in Google, it will probably return the most relevant version of your documentation.
It may happen that this version is already deprecated and you want to stop Google indexing it as a result,
and start suggesting the latest (or newer) one.

To accomplish this, you can add a ``robots.txt`` file to your documentation's root so it ends up served at the root URL of your project
(for example, https://yourproject.readthedocs.io/robots.txt).
We have documented how to set this up in our :ref:`hosting:Custom robots.txt Pages` docs.


Can I remove advertising from my documentation?
-----------------------------------------------

See :ref:`Opting out of advertising <advertising/ethical-advertising:Opting Out>`.


How do I change my project slug (the URL your docs are served at)?
------------------------------------------------------------------

We don't support allowing folks to change the slug for their project.
You can update the name which is shown on the site,
but not the actual URL that documentation is served.

The main reason for this is that all existing URLs to the content will break.
You can delete and re-create the project with the proper name to get a new slug,
but you really shouldn't do this if you have existing inbound links,
as it `breaks the internet <http://www.w3.org/Provider/Style/URI.html>`_.

If that isn't enough,
you can request the change sending an email to support@readthedocs.org.


How do I change the version slug of my project?
-----------------------------------------------

We don't support allowing folks to change the slug for their versions.
But you can rename the branch/tag to achieve this.
If that isn't enough,
you can request the change sending an email to support@readthedocs.org.


What commit of Read the Docs is in production?
----------------------------------------------

We deploy readthedocs.org from the ``rel`` branch in our GitHub repository.
You can see the latest commits that have been deployed by looking on GitHub: https://github.com/readthedocs/readthedocs.org/commits/rel

We also keep an up-to-date :doc:`changelog </changelog>`.
