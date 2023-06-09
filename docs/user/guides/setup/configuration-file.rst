How to add a configuration file
===============================

As part of the initial set up for your Read the Docs site,
you need to create a **configuration file** called ``.readthedocs.yaml``.
The configuration file tells Read the Docs what specific settings to use for your project.

This how-to guide covers:

#. Where to put your configuration file.
#. What to put in the configuration file.
#. How to customize the configuration for your project.

.. seealso::

   :doc:`/tutorial/index`.
     Following the steps in our tutorial will help you setup your first documentation project.


Where to put your configuration file
------------------------------------

The ``.readthedocs.yaml`` file should be placed in the top-most directory of your project's repository.
We will get to the contents of the file in the next steps.

When you have changed the configuration file,
you need to commit and push the changes to your Git repository.
Read the Docs will then automatically find and use the configuration to build your project.

.. note::

    Why is it called .yaml? What is that?
      The configuration file is a `YAML`_ file. YAML files are a "map": a collection of
      key-value pairs that can be nested. This is not unlike a JSON file or ``dict``
      object in Python. This page won't explain the structure of YAML files, but many resources exist
      online.


.. _YAML: https://en.wikipedia.org/wiki/YAML

.. _howto_templates:

Getting started with a template
-------------------------------

Here are some configuration file examples to help you get started.
Pick an example based on the tool that your project is using,
copy its contents to ``.readthedocs.yaml`` and add the file to your Git repository.

.. tabs::

    .. tab:: Sphinx

        If your project uses Sphinx,
        we offer a special builder optimized for Sphinx projects.

        .. literalinclude:: /config-file/examples/sphinx/.readthedocs.yaml
           :language: yaml
           :linenos:
           :caption: .readthedocs.yaml


    .. tab:: MkDocs

        If your project uses MkDocs,
        we offer a special builder optimized for MkDocs projects.

        .. literalinclude:: /config-file/examples/mkdocs/.readthedocs.yaml
           :language: yaml
           :linenos:
           :caption: .readthedocs.yaml

    .. tab:: Docusaurus

        If you are using `Docusaurus <https://docusaurus.io/>`__,
        we provide support through the following template.

        Each step is explained in the comments and elaborated in this how-to.

        .. literalinclude:: /config-file/examples/docusaurus/.readthedocs.yaml
           :language: yaml
           :linenos:

    .. tab:: Other tools

        Using another documentation tool than the ones shown here?

        You can overwrite the commands of your documentation tool in a similar fashion shown in the Docusaurus template.
        We recommend looking at :ref:`build_commands_introduction` for a more complete introduction to setting up a custom documentation tool.

        Meanwhile, we are brewing together templates for additional documentation tools,
        and we very much welcome you to proposals in `our GitHub issue tracker <https://github.com/readthedocs/readthedocs.org/issues>`__ 🍰️


Editing the template
--------------------

Now that you have a ``.readthedocs.yaml`` file added to your Git repository,
you should see Read the Docs trying to build your project with the configuration file.
The configuration file probably needs some adjustments to accommodate exactly your project setup.

.. note::

   If you added the configuration file in a separate branch,
   you may have to activate a :doc:`version </versions>` for that branch.

   If you have added the file in a pull request,
   you should enable :doc:`pull request builds </guides/pull-requests>`.

Skip: file header and comments
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

There are some parts of the templates that you can leave in place:

Comments
  We added comments that explain the configuration options and optional features.
  These lines begin with a ``#``.

Commented out features
  We use the ``#`` in front of some popular configuration options.
  They are there as examples,
  which you can choose to enable, delete or save for later.

``version`` key
  The version key tells the system how to read the rest of the configuration file.
  The current and only supported version is **version 2**.


Adjust: ``build.os``
~~~~~~~~~~~~~~~~~~~~

In our examples,
we are using Read the Docs' custom image based on the latest Ubuntu LTS release.
LTS means long-term support,
meaning that your builds should not break within next many years.

However,
you should pay attention to this field if your project needs to build on an older version of Ubuntu,
or in the future when you need features from a newer Ubuntu.

.. seealso::

   :ref:`config-file/v2:build.os`
     Configuration file reference with all values possible for ``build.os``.


Adjust: Python configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you are using Python in your builds,
you should define the Python version in ``build.tools.python``.

The ``python`` key contains a list of sub-keys,
specifying the requirements to install.

- Use ``python.install.package`` to install the project itself as a Python package using pip
- Use ``python.install.requirements`` to install packages from a requirements file
- Use ``build.jobs`` to install packages using Poetry or PDM

.. seealso::

   :ref:`config-file/v2:build.tools.python`
     Configuration file reference with all Python versions available for ``build.tools.python``.

   :ref:`config-file/v2:python`
     Configuration file reference for configuring the Python environment activated by ``build.tools.python``.

Adjust: Sphinx and MkDocs version
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you are using either the ``sphinx`` or ``mkdocs`` builder,
then Sphinx or MkDocs will be installed automatically in its latest version.

But we recommend that you specify the version that your documentation project uses.
The ``requirements`` key is a file path that points to a text (``.txt``) file
that lists the Python packages you want Read the Docs to install.

.. seealso::

   :ref:`guides/reproducible-builds:Use a requirements file for Python dependencies`
      This guide explains how to specify Python requirements,
      such as the version of Sphinx or MkDocs.

   :ref:`config-file/v2:sphinx`
     Configuration file reference for configuring the Sphinx builder.

   :ref:`config-file/v2:mkdocs`
     Configuration file reference for configuring the MkDocs builder.

Adjust: Docusaurus
~~~~~~~~~~~~~~~~~~

The template for :ref:`Docusaurus <howto_templates>` shows a slightly more complex example of using a custom documentation tool.

What's needed are the following steps:

1. Install the custom documentation tool in its environment.
   To build a Docusaurus project,
   we need to enable a Node.js environment and then we install docusarus.

2. Run the documentation tool!

3. Move the outputs into their expected location.
   Here, we use the pre-defined ``$READTHEDOCS_OUTPUT`` :doc:`environment variable </reference/environment-variables>`.

Notice in the template that ``docs/`` is used as the path for your Docusaurus project.
If it's stored in another location,
you should adjust this.

.. seealso::

   :ref:`build_commands_introduction`
     Read more about how to add your own commands in the build process.

Next steps
----------

There are more configuration options that the ones mentioned in this guide.

After you add a configuration file your Git repository,
and you can see that Read the Docs is building your documentation using the file,
you should have a look at the complete configuration file reference for options that might apply to your project.

.. seealso::

   :doc:`/config-file/v2`.
     The complete list of all possible ``.readthedocs.yaml`` settings,
     including the optional settings not covered in on this page.

   :doc:`/build-customization`
     Are familiar with running a command line?
     Perhaps there are special commands that you know you want Read the Docs to run.
     Read this guide and learn more about how you add your own commands to ``.readthedocs.yaml``.
