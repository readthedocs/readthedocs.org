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

You can see the current Docker build images that we use in our `docker repository <https://github.com/rtfd/readthedocs-docker-images>`_.
`Docker Hub <https://hub.docker.com/r/readthedocs/build/>`_ also shows the latest set of images that have been built.

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

MkDocs
~~~~~~

When you choose *Mkdocs* as your *Documentation Type*,
we will first look for a ``mkdocs.yml`` file in the root of your repository.
If we don't find one,
we will generate one for you.

Then MkDocs will build any files with a ``.md`` extension within the directory specified as ``docs_dir`` in the ``mkdocs.yml``. 

If no ``mkdocs.yml`` was found in the root of your repository and we generated one for you, 
Read the Docs will attempt to set ``docs_dir`` by sequentially searching for a  ``docs``, ``doc``, ``Doc``, or ``book`` directory. 
The first of these directories that exists and contains files with a ``.md`` extension will be set to ``docs_dir`` within ``mkdocs.yml``,
and MkDocs will build the ``.md`` files in that directory. 
As MkDocs doesn't support automatic PDF generation, 
Read the Docs cannot create a PDF version of your documentation with the *Mkdocs* option.

.. warning::

   We strongly recommend to :ref:`pin the MkDocs version <guides/specifying-dependencies:Specifying Dependencies>`
   used for your project to build the docs to avoid potential future incompatibilities.


Understanding what's going on
-----------------------------

Understanding how Read the Docs builds your project will help you with debugging the problems you have with the site.
It should also allow you to take advantage of certain things that happen during the build process.

The first step of the process is that we check out your code from the repository you have given us.
If the code is already checked out, we update the copy to the branch that you have specified in your projects configuration.

Then we build the proper backend code for the type of documentation you've selected.

If you have the *Install Project* option enabled, we will run ``setup.py install`` on your package, installing it into a virtual environment.
You can also define additional packages to install with the *Requirements File* option.

When we build your Sphinx documentation, we run ``sphinx-build -b html . _build/html``,
where ``html`` would be replaced with the correct backend.
We also create pdf's and ePub's automatically based on your project.
For MkDocs, we run ``mkdocs build``.

Then these files are copied across to our application servers from the build server.
Once on the application servers, they are served from nginx. 

An example in code:

.. code-block:: python

    update_docs_from_vcs(version)
    if exists('setup.py'):
        run('python setup.py install')
    if project.requirements_file:
        run('pip install -r %s' % project.requirements_file)
    build_docs(version=version)
    copy_files(artifact_dir)

.. note::

    Regardless of whether you build your docs with Sphinx or MkDocs,
    we recommend you pin the version of Sphinx or Mkdocs you want us to use.
    You can do this the same way other
    :doc:`dependencies are specified <guides/specifying-dependencies>`.
    Some examples of pinning versions might be ``sphinx<2.0`` or ``mkdocs>=1.0``.

Builder responsibility
----------------------

Builders have a very specific job.
They take the updated source code and generate the correct artifacts.
The code lives in ``self.version.project.checkout_path(self.version.slug)``.
The artifacts should end up in ``self.version.project.artifact_path(version=self.version.slug, type=self.type)``
Where ``type`` is the name of your builder.
All files that end up in the artifact directory should be in their final form.

The build environment
---------------------

The build process is executed inside Docker containers,
by default the image used is ``readthedocs/build:2.0``,
but you can change that using a :doc:`configuration file <yaml-config>`.

.. note::
   
   The Docker images have a select number of C libraries installed,
   because they are used across a wide array of python projects.
   We can't install every C library out there,
   but we try and support the major ones.

.. tip::
   
   If you want to know the specific version of a package that is installed in the image
   you can check the `Ubuntu package search page <https://packages.ubuntu.com/>`__.

2.0 (stable)
~~~~~~~~~~~~

:O.S: Ubuntu 16.04
:Conda: Miniconda 4.3.31
:Python:
  * ``m2crypto``
  * ``matplolib``
  * ``numpy``
  * ``pandas``
  * ``pip``
  * ``scipy``
:Other packages:
  * ``doxygen``
  * ``graphviz``
  * ``libevent``
  * ``libjpeg``
  * ``libxml2-dev``
  * ``libxslt1.1``
  * ``pandoc``
  * ``textlive-full``

`More details <https://github.com/rtfd/readthedocs-docker-images/blob/releases/2.x/Dockerfile>`__

3.0 (latest)
~~~~~~~~~~~~

:O.S: Ubuntu 16.04
:Conda: Miniconda 4.4.10
:Python:
  * ``matplolib``
  * ``numpy``,
  * ``pandas``
  * ``pip``
  * ``scipy``
:JavaScript:
  * ``jsdoc``
  * ``nodejs``
  * ``npm``
:Other packages:
  * ``doxygen``
  * ``libevent-dev``
  * ``libgraphviz-dev``
  * ``libjpeg``
  * ``libxml2-dev``
  * ``libxslt1-dev``
  * ``pandoc``
  * ``plantuml``
  * ``textlive-full``

`More details <https://github.com/rtfd/readthedocs-docker-images/blob/releases/3.x/Dockerfile>`__

Writing your own builder
------------------------

.. note:: Builds happen on a server using only the RTD Public API. There is no reason that you couldn't build your own independent builder that wrote into the RTD namespace. The only thing that is currently unsupported there is a saner way than uploading the processed files as a zip.

The documentation build system in RTD is made pluggable, so that you can build out your own backend. If you have a documentation format that isn't currently supported, you can add support by contributing a backend.

`The builder backends`_ detail the higher level parts of the API that you need to implement. A basic run goes something like this:

.. sourcecode:: python

    backend = get_backend(project.documentation_type)
    if force:
        backend.force(version)
    backend.clean(version)
    backend.build(version)
    if success:
        backend.move(version)

.. _The builder backends: https://github.com/rtfd/readthedocs.org/tree/master/readthedocs/doc_builder/backends

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
