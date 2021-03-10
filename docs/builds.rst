Build Process
=============

Every documentation build has limited resources.
Our current build limits are:

.. tabs::

   .. tab:: |org_brand|

      * 15 minutes build time
      * 3GB of memory
      * 2 concurrent builds

      We can increase build limits on a per-project basis.
      Send an email to support@readthedocs.org providing a good reason why your documentation needs more resources.

      If your business is hitting build limits hosting documentation on Read the Docs,
      please consider :doc:`Read the Docs for Business </commercial/index>`
      which has much higher build resources.

   .. tab:: |com_brand|

      * 30 minutes build time
      * 7GB of memory
      * Concurrent builds vary based on your pricing plan

      If you are having trouble with your documentation builds,
      you can reach our support at support@readthedocs.com.

Understanding what's going on
-----------------------------

Understanding how Read the Docs builds your project will help you with debugging the problems you have with the site.
It should also allow you to take advantage of certain things that happen during the build process.

The first step of the process is that we check out your code from the repository you have given us.
If the code is already checked out, we update the copy to the branch that you have specified in your project's configuration.

Then we build the proper backend code for the type of documentation you've selected,
this is done inside a :ref:`Docker container <builds:Docker images>`.

At this point, if you need extra requirements,
or even install your own package in the virtual environment to build your documentation,
you can use a :doc:`config-file/index`.

When we build your Sphinx documentation, we run ``sphinx-build -b <format> . _build/<format>``
We also create pdf's and ePub's automatically based on your project.
For MkDocs, we run ``mkdocs build``.

Once these files are built,
they are deployed to our file hosting backend and will be visible to users.

An example in code:

.. code-block:: python

    update_docs_from_vcs(version)
    config = get_config(project)
    if config.python.install.method.pip:
        run('pip install .')
    if config.python.install.requirement:
        run('pip install -r %s' % config.python.install.requirement)
    build_docs(version)
    deploy_docs(version)

.. note::

    Regardless of whether you build your docs with Sphinx or MkDocs,
    we recommend you :ref:`pinning the version <guides/reproducible-builds:pinning dependencies>` of Sphinx or Mkdocs you want us to use.
    Some examples of pinning versions might be ``sphinx<2.0`` or ``mkdocs>=1.0``.

Build environment
-----------------

The *Sphinx* and *Mkdocs* builders set the following RTD-specific environment variables when building your documentation:

.. csv-table:: Environment Variables
   :header: Environment variable, Description, Example value
   :widths: 15, 10, 30

   ``READTHEDOCS``, Whether the build is running inside RTD, ``True``
   ``READTHEDOCS_VERSION``, The RTD name of the version which is being built, ``latest``
   ``READTHEDOCS_PROJECT``, The RTD slug of the project which is being built, ``my-example-project``
   ``READTHEDOCS_LANGUAGE``, The RTD language slug of the project which is being built, ``en``

If you want to learn more about how the build environment works as a low level,
you can read about it in our :doc:`/development/buildenvironments` docs.

.. tip::

   In case extra environment variables are needed to the build process (like secrets, tokens, etc),
   you can add them going to :guilabel:`Admin` > :guilabel:`Environment Variables` in your project.
   See :doc:`guides/environment-variables`.


Docker images
-------------

The build process is executed inside Docker containers,
by default the image used is ``readthedocs/build:latest``,
but you can change that using a :doc:`/config-file/index`.

You can see the current Docker build images that we use in our `docker repository <https://github.com/readthedocs/readthedocs-docker-images>`_.
`Docker Hub <https://hub.docker.com/r/readthedocs/build/>`_ also shows the latest set of images that have been built.
