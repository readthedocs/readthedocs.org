Frequently asked questions
==========================

.. contents::
   :local:

..
  Frequently asked questions should be questions that actually got asked.
  Formulate them as a question and an answer.
  Consider that the answer is best as a reference to another place in the documentation.


Building and publishing your project
------------------------------------


.. Old reference
.. _My project isn't building correctly:

Why does my project have status "failing"?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Projects have the status "failing" because something in the build process has failed.
This can be because the project is not correctly configured,
because the contents of the Git repository cannot be built,
or in the most rare cases because a system that Read the Docs connects to is not working.

First, you should check out the Builds tab of your project.
By clicking on the failing step,
you will be able to see details that can lead to resolutions to your build error.

If the solution is not self-evident,
you can use an important word or message from the error to search for a solution.

.. seealso::

   :doc:`/guides/build-troubleshooting`
      Common errors and solutions for build failures.

   Other FAQ entries
      * :ref:`faq:How do I add additional software dependencies for my documentation?`
      * :ref:`faq:why do i get import errors from libraries depending on c modules?`


.. Old reference
.. _Help, my build passed but my documentation page is 404 Not Found!:

Why does my project have status "passed" but I get a 404 page?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This often happens because you don't have an `index.html` file being generated.

Make sure you have one of the following files at the top level of your documentation source:

    * `index.rst` (Sphinx)
    * `index.md` (MkDocs or Sphinx with MyST)

.. tip::

   To test if your docs actually built correctly,
   you can navigate to a specific page that you know is part of the documentation build,
   for example `/en/latest/README.html`.

Why do I get import errors from libraries depending on C modules?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. note::

   Another use case for this is when you have a module with a C extension.

This happens because the build system does not have the dependencies for
building your project, such as C libraries needed by some Python packages (e.g.
``libevent`` or ``mysql``). For libraries that cannot be :ref:`installed via apt
<config-file/v2:build.apt_packages>` in the builder there is another way to
successfully build the documentation despite missing dependencies.

With Sphinx you can use the built-in `autodoc_mock_imports`_ for mocking. If
such libraries are installed via ``setup.py``, you also will need to remove all
the C-dependent libraries from your ``install_requires`` in the RTD environment.

.. _autodoc_mock_imports: http://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html#confval-autodoc_mock_imports

Where do I need to put my docs for RTD to find it?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Read the Docs will crawl your project looking for a ``conf.py``. Where it finds the ``conf.py``,
it will run ``sphinx-build`` in that directory.
So as long as you only have one set of sphinx documentation in your project, it should Just Work.

You can specify an exact path to your documentation using a Read the Docs :doc:`config-file/index`.

How can I avoid search results having a deprecated version of my docs?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If readers search something related to your docs in Google, it will probably return the most relevant version of your documentation.
It may happen that this version is already deprecated and you want to stop Google indexing it as a result,
and start suggesting the latest (or newer) one.

To accomplish this, you can add a ``robots.txt`` file to your documentation's root so it ends up served at the root URL of your project
(for example, https://yourproject.readthedocs.io/robots.txt).
We have documented how to set this up in :doc:`/reference/robots`.


How do I change the version slug of my project?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

We don't support allowing folks to change the slug for their versions.
But you can rename the branch/tag to achieve this.
If that isn't enough,
you can request the change sending an email to support@readthedocs.org.


What commit of Read the Docs is in production?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

We deploy readthedocs.org from the ``rel`` branch in our GitHub repository.
You can see the latest commits that have been deployed by looking on GitHub: https://github.com/readthedocs/readthedocs.org/commits/rel

We also keep an up-to-date :doc:`changelog </changelog>`.



Additional features and configuration
-------------------------------------

How do I add additional software dependencies for my documentation?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For most Python dependencies,
you can can specify a requirements file which details your dependencies.
You can also set your project documentation to install your Python project itself as a dependency.

.. seealso::

   :doc:`/builds`
     An overview of the build process.

   :doc:`/guides/reproducible-builds`
     General information about adding dependencies and best-practices for maintaining them.

   :doc:`/build-customization`
     How to customize your builds, for example if you need to build with different tools from Sphinx or
     if you need to add additional packages for the Ubuntu-based builder.

   :doc:`/config-file/v2`
     Reference for the main configuration file, `.readthedocs.yaml`

   :ref:`build.apt_packages <config-file/v2:build.apt_packages>`
     Reference for adding Debian packages with apt for the Ubuntu-based builders

   Other FAQ entries
      * :ref:`faq:How do I add additional software dependencies for my documentation?`
      * :ref:`faq:Why do I get import errors from libraries depending on C modules?`


Can I have access to additional features or settings?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If this is just a dependency issue,
see :ref:`faq:How do I add additional software dependencies for my documentation?`.

Read the Docs offers some settings (feature flags) which can be used for a variety of purposes.
To enable these settings,
please send an email to support@readthedocs.org and we will change the settings for the project.

.. seealso::

   :doc:`/feature-flags`
     Reference of all Feature Flags that can be requested.


How do I change behavior when building with Read the Docs?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When RTD builds your project, it sets the :envvar:`READTHEDOCS` environment
variable to the string ``'True'``. So within your Sphinx :file:`conf.py` file, you
can vary the behavior based on this. For example:

.. code-block:: python

    import os

    on_rtd = os.environ.get("READTHEDOCS") == "True"
    if on_rtd:
        html_theme = "default"
    else:
        html_theme = "nature"

The :envvar:`READTHEDOCS` variable is also available in the Sphinx build
environment, and will be set to ``True`` when building on RTD:


.. code-block:: jinja

    {% if READTHEDOCS %}
    Woo
    {% endif %}


I want comments in my docs
~~~~~~~~~~~~~~~~~~~~~~~~~~

RTD doesn't have explicit support for this.
That said, a tool like `Disqus`_ (and the `sphinxcontrib-disqus`_ plugin) can be used for this purpose on RTD.

.. _Disqus: https://disqus.com/
.. _sphinxcontrib-disqus: https://pypi.python.org/pypi/sphinxcontrib-disqus

Can I remove advertising from my documentation?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Yes. See :ref:`Opting out of advertising <advertising/ethical-advertising:Opting Out>`.


How do I change my project slug (the URL your docs are served at)?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

We don't support allowing folks to change the slug for their project.
You can update the name which is shown on the site,
but not the actual URL that documentation is served.

The main reason for this is that all existing URLs to the content will break.
You can delete and re-create the project with the proper name to get a new slug,
but you really shouldn't do this if you have existing inbound links,
as it `breaks the internet <http://www.w3.org/Provider/Style/URI.html>`_.

If that isn't enough,
you can request the change sending an email to support@readthedocs.org.

Big projects
------------

How do I host multiple projects on one custom domain?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

We support the concept of subprojects, which allows multiple projects to share a
single domain. If you add a subproject to a project, that documentation will
be served under the parent project's subdomain or custom domain.

For example,
Kombu is a subproject of Celery,
so you can access it on the `celery.readthedocs.io` domain:

https://celery.readthedocs.io/projects/kombu/en/latest/

This also works the same for custom domains:

http://docs..org/projects/kombu/en/latest/

You can add subprojects in the project admin dashboard.

For details on custom domains, see our documentation on :doc:`/custom-domains`.

How do I support multiple languages of documentation?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Read the Docs supports multiple languages.
See the section on :doc:`localization`.



Sphinx
------

I want to use the Blue/Default Sphinx theme
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

We think that our theme is badass,
and better than the default for many reasons.
Some people don't like change though |:smile:|,
so there is a hack that will let you keep using the default theme.
If you set the ``html_style`` variable in your ``conf.py``,
it should default to using the default theme.
The value of this doesn't matter, and can be set to ``/default.css`` for default behavior.


I want to use the Read the Docs theme locally
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Read the Docs automatically applies the sphinx-rtd-theme to projects that do not have a defined theme.
If you build a Sphinx project locally,
you should specify that you are using sphinx-rtd-theme.

.. seealso::

   `sphinx-rtd-theme documentation <https://sphinx-rtd-theme.readthedocs.io/en/stable/installing.html>`_
     See the official documentation for instructions to enable it in your Sphinx theme.


Image scaling doesn't work in my documentation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Image scaling in docutils depends on PIL. PIL is installed in the system that RTD runs on. However, if you are using the virtualenv building option, you will likely need to include PIL in your requirements for your project.


Python
------

Can I document a Python package that is not at the root of my repository?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Yes. The most convenient way to access a Python package for example via
`Sphinx's autoapi`_ in your documentation is to use the *Install your project
inside a virtualenv using setup.py install* option in the admin panel of
your project. However this assumes that your ``setup.py`` is in the root of
your repository.

If you want to place your package in a different directory or have multiple
Python packages in the same project, then create a pip requirements file. You
can specify the relative path to your package inside the file.
For example you want to keep your Python package in the ``src/python``
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

Does Read the Docs work well with "legible" docstrings?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Yes. One criticism of Sphinx is that its annotated docstrings are too
dense and difficult for humans to read. In response, many projects
have adopted customized docstring styles that are simultaneously
informative and legible. The
`NumPy <https://numpydoc.readthedocs.io/en/latest/format.html#docstring-standard>`__
and
`Google <https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings>`__
styles are two popular docstring formats.  Fortunately, the default
Read the Docs theme handles both formats just fine, provided
your ``conf.py`` specifies an appropriate Sphinx extension that
knows how to convert your customized docstrings.  Two such extensions
are `numpydoc <https://github.com/numpy/numpydoc>`_ and
`napoleon <http://sphinxcontrib-napoleon.readthedocs.io>`_. Only
``napoleon`` is able to handle both docstring formats. Its default
output more closely matches the format of standard Sphinx annotations,
and as a result, it tends to look a bit better with the default theme.

.. note::

   To use these extensions you need to specify the dependencies on your project
   by following this :doc:`guide </guides/reproducible-builds>`.


I need to install a package in a environment with pinned versions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To ensure proper installation of a Python package, the ``pip`` :ref:`install method <config-file/v2:python.install>` will automatically upgrade every dependency to its most recent version in case they aren't:term:`pinned <pinning>` by the package definition.
If instead you'd like to pin your dependencies outside the package, you can add this line to your requirements or environment file (if you are using Conda).

In your ``requirements.txt`` file::

    # path to the directory containing setup.py relative to the project root
    -e .

In your Conda environment file (``environment.yml``)::

    # path to the directory containing setup.py relative to the environment file
    -e ..


Can I use Anaconda Project and ``anaconda-project.yml``?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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




Other documentation frameworks
------------------------------

How can I deploy Jupyter Book projects on Read the Docs?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

According to `its own documentation <https://jupyterbook.org/>`_,

   Jupyter Book is an open source project for building beautiful,
   publication-quality books and documents from computational material.

Even though `Jupyter Book leverages Sphinx "for almost everything that it
does" <https://jupyterbook.org/explain/sphinx.html#jupyter-book-is-a-distribution-of-sphinx>`_,
it purposedly hides Sphinx ``conf.py`` files from the user,
and instead generates them on the fly from its declarative ``_config.yml``.
As a result, you need to follow some extra steps
to make Jupyter Book work on Read the Docs.

As described in :doc:`the official documentation <jupyterbook:publish/readthedocs>`,
you can manually convert your Jupyter Book project to Sphinx with the following configuration:

.. code-block:: yaml
   :caption: .readthedocs.yaml

    build:
        jobs:
            pre_build:
            # Generate the Sphinx configuration for this Jupyter Book so it builds.
            - "jupyter-book config sphinx docs/"
