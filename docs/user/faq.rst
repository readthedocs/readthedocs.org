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

First, you should check out the :guilabel:`Builds` tab of your project.
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
the C-dependent libraries from your ``install_requires`` in the Read the Docs environment.

.. _autodoc_mock_imports: http://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html#confval-autodoc_mock_imports


Where do I need to put my docs for Read the Docs to find it?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can put your docs wherever your want on your repository.
However, you will need to tell Read the Docs where your Sphinx's (i.e. ``conf.py``)
or MkDocs' (i.e. ``mkdocs.yml``) configuration file lives in order to build your documentation.

This is done by using ``sphinx.configuration`` or ``mkdocs.configuration`` config key in your Read the Docs configuration file.
Read :doc:`config-file/index` to know more about this.


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

You can change the slug of your versions from the versions tab of your project,
see :ref:`versions:Version URL identifier (slug)` for more information.


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
you can specify a requirements file which details your dependencies.
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


How do I change behavior when building with Read the Docs?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When Read the Docs builds your project, it sets the :envvar:`READTHEDOCS` environment
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
environment, and will be set to ``True`` when building on Read the Docs:


.. code-block:: jinja

    {% if READTHEDOCS %}
    Woo
    {% endif %}


I want comments in my docs
~~~~~~~~~~~~~~~~~~~~~~~~~~

Read the Docs doesn't have explicit support for this.
That said, a tool like `Disqus`_ (and the `sphinxcontrib-disqus`_ plugin) can be used for this purpose on Read the Docs.

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

Instead, you can consider *migrating your documentation to another domain*
with :doc:`/user-defined-redirects`.

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

http://docs.celeryq.dev/projects/kombu/en/latest/

You can add subprojects in the project admin dashboard.

For details on custom domains, see our documentation on :doc:`/custom-domains`.

How do I support multiple languages of documentation?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Read the Docs supports multiple languages.
See the section on :doc:`localization`.



Sphinx
------


.. Old references
.. _I want to use the Blue/Default Sphinx theme:
.. _I want to use the Read the Docs theme locally:

I want to use the Read the Docs theme
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To use the Read the Docs theme,
you have to specify that in your Sphinx's ``conf.py`` file.

Read the `sphinx-rtd-theme documentation <https://sphinx-rtd-theme.readthedocs.io/en/stable/installing.html>`_
for instructions to enable it in your Sphinx project.


Image scaling doesn't work in my documentation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Image scaling in ``docutils`` depends on ``Pillow``.
If you notice that image scaling is not working properly on your Sphinx project,
you may need to add ``Pillow`` to your requirements to fix this issue.
Read more about :doc:`guides/reproducible-builds` to define your dependencies in a ``requirements.txt`` file.

Python
------

Can I document a Python package that is not at the root of my repository?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Yes. The most convenient way to access a Python package for example via
`Sphinx's autoapi`_ in your documentation is to use the
``python.install.method: pip`` (:ref:`config-file/v2:python.install`) configuration key.

This configuration will tell Read the Docs to install your package in
the virtual environment used to build your documentation so your documentation tool can access to it.

.. _Sphinx's autoapi: https://sphinx-autoapi.readthedocs.io/en/latest/


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

If you'd like to pin your dependencies outside the package,
you can add this line to your requirements or environment file (if you are using Conda).

In your ``requirements.txt`` file::

    # path to the directory containing setup.py relative to the project root
    -e .

In your Conda environment file (``environment.yml``)::

    # path to the directory containing setup.py relative to the environment file
    -e ..


Other documentation frameworks
------------------------------

How can I deploy Jupyter Book projects on Read the Docs?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

According to `its own documentation <https://jupyterbook.org/>`_,

   Jupyter Book is an open source project for building beautiful,
   publication-quality books and documents from computational material.

Even though `Jupyter Book leverages Sphinx "for almost everything that it
does" <https://jupyterbook.org/explain/sphinx.html#jupyter-book-is-a-distribution-of-sphinx>`_,
it purposely hides Sphinx ``conf.py`` files from the user,
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
