Build Process
=============

Files: `tasks.py`_ - `doc_builder/`_

.. _tasks.py: https://github.com/rtfd/readthedocs.org/blob/master/readthedocs/projects/tasks.py
.. _doc_builder/: https://github.com/rtfd/readthedocs.org/tree/master/readthedocs/doc_builder

Every documentation build has limited resources.
Our current build limits are:

* 15 minutes
* 1GB of memory

We can increase build limits on a per-project basis,
if you provide a good reason your documentation needs more resources.

You can see the current Docker build images that we use in our `docker repository <https://github.com/rtfd/readthedocs-docker-images>`_. `Docker Hub <https://hub.docker.com/r/readthedocs/build/>`_ also shows the latest set of images that have been built.

Currently in production we're using the ``readthedocs/build:2.0`` docker image as our default image.

How we build documentation
--------------------------

When we import your documentation, we look at two things first: your *Repository URL* and the *Documentation Type*.
We will clone your repository,
and then build your documentation using the *Documentation Type* specified.

Sphinx
~~~~~~

When you choose *Sphinx* as your *Documentation Type*,
we will first look for a ``conf.py`` file in your repository.
If we don't find one,
we will generate one for you.
We will look inside a ``doc`` or ``docs`` directory first,
and then look within your entire project.

Then Sphinx will build any files with an ``.rst`` extension.
If you have a ``README.rst``,
it will be transformed into an ``index.rst`` automatically.

Mkdocs
~~~~~~

When you choose *Mkdocs* as your *Documentation Type*,
we will first look for a ``mkdocs.yml`` file in your repository.
If we don't find one,
we will generate one for you.
We will look inside a ``doc`` or ``docs`` directory first,
and then default to the top-level of your documentation.

Then Mkdocs will build any files with an ``.md`` extension.
If you have a ``README.md``,
it will be transformed into an ``index.md`` automatically.
As MkDocs doesn't support automatic PDF generation,
Read the Docs cannot create a PDF version of your documentation with the *Mkdocs* option.

Understanding what's going on
-----------------------------

Understanding how Read the Docs builds your project will help you with debugging the problems you have with the site. It should also allow you to take advantage of certain things that happen during the build process.

The first step of the process is that we check out your code from the repository you have given us. If the code is already checked out, we update the copy to the branch that you have specified in your projects configuration.

Then we build the proper backend code for the type of documentation you've selected.

If you have the *Install Project* option enabled, we will run ``setup.py install`` on your package, installing it into a virtual environment. You can also define additional packages to install with the *Requirements File* option.

When we build your documentation, we run `sphinx-build -b html . _build/html`, where `html` would be replaced with the correct backend. We also create man pages and pdf's automatically based on your project.

Then these files are copied across to our application servers from the build server. Once on the application servers, they are served from nginx. 

An example in code:

.. code-block:: python

    update_imported_docs(version)
    if exists('setup.py'):
        run('python setup.py install')
    if project.requirements_file:
        run('pip install -r %s' % project.requirements_file)
    build_docs(version=version)
    copy_files(artifact_dir)
    

Builder Responsibility
----------------------

Builders have a very specific job.
They take the updated source code and generate the correct artifacts.
The code lives in ``self.version.project.checkout_path(self.version.slug)``.
The artifacts should end up in ``self.version.project.artifact_path(version=self.version.slug, type=self.type)``
Where ``type`` is the name of your builder.
All files that end up in the artifact directory should be in their final form.

Packages installed in the build environment
-------------------------------------------

The build server does have a select number of C libraries installed, because they are used across a wide array of python projects. We can't install every C library out there, but we try and support the major ones. We currently have the following libraries installed:

    * doxygen
    * LaTeX (texlive-full)
    * libevent (libevent-dev)
    * dvipng
    * graphviz
    * libxslt1.1
    * libxml2-dev

Writing your own builder
------------------------

.. note:: Builds happen on a server using only the RTD Public API. There is no reason that you couldn't build your own independent builder that wrote into the RTD namespace. The only thing that is currently unsupported there is a saner way than uploading the processed files as a zip.

The documentation build system in RTD is made pluggable, so that you can build out your own backend. If you have a documentation format that isn't currently supported, you can add support by contributing a backend.

The :doc:`api/doc_builder` API explains the higher level parts of the API that you need to implement. A basic run goes something like this::

    backend = get_backend(project.documentation_type)
    if force:
        backend.force(version)
    backend.clean(version)
    backend.build(version)
    if success:
        backend.move(version)

Deleting a stale or broken build environment
--------------------------------------------

If you're having trouble getting your version to build, try wiping out the existing build/environment files.  On your version list page ``/projects/[project]/versions`` there is a "Wipe" button that will remove all of the files associated with your documentation build, but not the documentation itself.

Build environment
-----------------

The *Sphinx* and *Mkdocs* builders set the following RTD-specific environment variables when building your documentation:

+-------------------------+--------------------------------------------------+----------------------+
| Environment variable    | Description                                      | Example value        |
+-------------------------+--------------------------------------------------+----------------------+
| ``READTHEDOCS``         | Whether the build is running inside RTD          | ``True``             |
+-------------------------+--------------------------------------------------+----------------------+
| ``READTHEDOCS_VERSION`` | The RTD name of the version which is being built | ``latest``           |
+-------------------------+--------------------------------------------------+----------------------+
| ``READTHEDOCS_PROJECT`` | The RTD name of the project which is being built | ``myexampleproject`` |
+-------------------------+--------------------------------------------------+----------------------+
