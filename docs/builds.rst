Build Process
=============

Files: `tasks.py`_ - `doc_builder/`_

.. _tasks.py: https://github.com/readthedocs/readthedocs.org/blob/master/readthedocs/projects/tasks.py
.. _doc_builder/: https://github.com/rtfd/readthedocs.org/tree/master/readthedocs/doc_builder

Every documentation build has limited resources.
Our current build limits are:

* 15 minutes of CPU
* 1GB of RAM memory

We can increase build limits on a per-project basis,
sending an email to support@readthedocs.org providing a good reason why your documentation needs more resources.
If your business is hitting build limits hosting documentation on Read the Docs,
please consider :doc:`Read the Docs for Business </commercial/index>`
which has much higher build resources.

You can see the current Docker build images that we use in our `docker repository <https://github.com/readthedocs/readthedocs-docker-images>`_.
`Docker Hub <https://hub.docker.com/r/readthedocs/build/>`_ also shows the latest set of images that have been built.

Currently in production we're using the ``readthedocs/build:latest`` docker image as our default image.

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
If the code is already checked out, we update the copy to the branch that you have specified in your project's configuration.

Then we build the proper backend code for the type of documentation you've selected.

At this point, if you need extra requirements,
or even install your own package in the virtual environment to build your documentation,
you can use a :doc:`config-file/index`.

When we build your Sphinx documentation, we run ``sphinx-build -b html . _build/html``,
where ``html`` would be replaced with the correct backend.
We also create pdf's and ePub's automatically based on your project.
For MkDocs, we run ``mkdocs build``.

Then these files are copied across to our application servers from the build server.
Once on the application servers, they are served from nginx. 

An example in code:

.. code-block:: python

    update_docs_from_vcs(version)
    config = get_config(project)
    if config.python.install.method.setuptools:
        run('python setup.py install')
    if config.python.install.method.pip:
        run('pip install .')
    if config.python.install.requirement:
        run('pip install -r %s' % config.python.install.requirement)
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
by default the image used is ``readthedocs/build:latest``,
but you can change that using a :doc:`config-file/index`.

.. note::
   
   The Docker images have a select number of C libraries installed,
   because they are used across a wide array of python projects.
   We can't install every C library out there,
   but we try and support the major ones.

.. tip::
   
   If you want to know the specific version of a package that is installed in the image
   you can check the `Ubuntu package search page <https://packages.ubuntu.com/>`__.

More details on software installed in images could be found by browsing specific branch in `rtfd/readthedocs-docker-images <https://github.com/readthedocs/readthedocs-docker-images>`__ repository.

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

.. _The builder backends: https://github.com/readthedocs/readthedocs.org/tree/master/readthedocs/doc_builder/backends

Deleting a stale or broken build environment
--------------------------------------------

If you're having trouble getting your version to build, try wiping out the existing build/environment files.  On your version list page ``/projects/[project]/versions`` there is a "Wipe" button that will remove all of the files associated with your documentation build, but not the documentation itself.

Build environment
-----------------

Build environments use `Docker`_ to handle container virtualization. To perform
any development on the Docker build system, you will need to set up `Docker`_ on
your host system. Setup of Docker will vary by system, and so is out of the
scope of this documentation.

Once you have Docker set up, you will need to pull down our build image. These
images are found on our `Docker Hub repository`_, the source comes from our
`container image repo`_.

.. note:: The size of the Docker images is around 5 to 9 GB.

To get started using Docker for build environments, you'll need to pull down at
least one build image. For example, to pull down our latest image::

    docker pull readthedocs/build:latest

The default image used by our build servers is :djangosetting:`DOCKER_IMAGE`.
This would be a good place to start testing as the ``latest`` version could
operate differently. See ``DOCKER_IMAGE`` below for setting this configuration
option.

After this image is downloaded, you can update your settings to use the new
image -- see `Configuration`_.

.. _`Docker`: http://docker.com
.. _`Docker Hub repository`: https://hub.docker.com/r/readthedocs/build/
.. _`container image repo`: https://github.com/readthedocs/readthedocs-docker-images

Configuration
-------------

There are several settings used to configure usage of virtual machines:

DOCKER_ENABLE
    True/False value used to enable the Docker build environment.

    Default: :djangosetting:`DOCKER_ENABLE`

DOCKER_LIMITS
    A dictionary of limits to virtual machines. These limits include:

        time
            An integer representing the total allowed time limit (in
            seconds) of build processes. This time limit affects the parent
            process to the virtual machine and will force a virtual machine
            to die if a build is still running after the allotted time
            expires.

        memory
            The maximum memory allocated to the virtual machine. If this
            limit is hit, build processes will be automatically killed.
            Examples: '200m' for 200MB of total memory, or '2g' for 2GB of
            total memory.

    Default: :djangosetting:`DOCKER_LIMITS`

DOCKER_IMAGE
    Tag of a Docker image to use as a base image.

    Default: :djangosetting:`DOCKER_IMAGE`

DOCKER_SOCKET
    URI of the socket to connect to the Docker daemon. Examples include:
    ``unix:///var/run/docker.sock`` and ``tcp://127.0.0.1:2375``.

    Default: :djangosetting:`DOCKER_SOCKET`

DOCKER_VERSION
    Version of the API to use for the Docker API client.

    Default: :djangosetting:`DOCKER_VERSION`


Local development
-----------------

On Linux development environments, it's likely that your UID and GID do not
match the ``docs`` user that is set up as the default user for builds. In this
case, it's necessary to make a new image that overrides the UID and GID for the
normal container user::

    contrib/docker_build.sh latest

This will create a new image, ``readthedocs/build-dev:latest``. To build a
different image, you can instead specify a version to build::

    contrib/docker_build.sh 5.0

This will create a new image, ``readthedocs/build-dev:5.0``.

You can set a ``local_settings.py`` option to automatically patch the image
names to the development image names that are built here:

DOCKER_USE_DEV_IMAGES
    If set to ``True``, replace the normal Docker image name used in building
    ``readthedocs/build`` with the image name output for these commands,
    ``readthedocs/build-dev``.

The *Sphinx* and *Mkdocs* builders set the following RTD-specific environment variables when building your documentation:

.. csv-table::
   :header-rows: 1

 Environment variable, Description, Example value  
 ``READTHEDOCS``, Whether the build is running inside RTD, ``True``   
 ``READTHEDOCS_VERSION``, The RTD name of the version which is being built, ``latest``   
 ``READTHEDOCS_PROJECT``, The RTD slug of the project which is being built, ``my-example-project``
 ``READTHEDOCS_LANGUAGE``, The RTD language slug of the project which is being built, ``en``

.. tip::

   In case extra environment variables are needed to the build process (like secrets, tokens, etc),
   you can add them going to :guilabel:`Admin` > :guilabel:`Environment Variables` in your project.
   See :doc:`guides/environment-variables`.



