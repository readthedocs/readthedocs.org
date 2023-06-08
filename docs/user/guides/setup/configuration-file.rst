How to add a configuration file
===============================

As part of the initial setup for your Read the Docs site,
you need to create a **configuration file** called ``.readthedocs.yaml``.
The configuration file tells Read the Docs what specific settings to use for your project.

This how-to guide covers:

#. Where to put your configuration file.
#. Templates to setup your configuration file from scratch.
#. The most basic sections in the configuration file that can help you get started.
#. Next steps...

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


Getting started with a template
-------------------------------

Here are some variations of the configuration file that can help you get started.
Pick the one that resembles your project the most,
copy its contents to ``.readthedocs.yaml`` and add the file to your Git repository.

.. tabs::

    .. tab:: Sphinx

        If your project uses Sphinx,
        we offer a special builder optimized for Sphinx projects.

        .. literalinclude:: /config-file/examples/sphinx/.readthedocs.yaml
           :language: yaml
           :linenos:


    .. tab:: MkDocs

        If your project uses MkDocs,
        we offer a special builder optimized for MkDocs projects.

        .. literalinclude:: /config-file/examples/mkdocs/.readthedocs.yaml
           :language: yaml
           :linenos:

    .. tab:: Other tools

        If you are using another documentation tool,
        you can configure the commands of your documentation tool in the following code.

        You will need to create the output directories and direct your documentation tool to write its outputs into those directories.

        .. literalinclude:: /config-file/examples/custom-commands-echo/.readthedocs.yaml
           :language: yaml
           :linenos:


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
  We added a lot of comments that explain stuff. They begin with a ``#``.

Commented out features
  Similar to comments, we also use the ``#`` in front of some configuration options that may or may not be relevant.
  To enable something that's commented out,
  simply delete the ``#`` and a blank space in front of the YAML code that you want to enable.

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
you should pay attention to this field if your current project needs to build on an older version of Ubuntu,
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

.. _config_howto_build.tools:

Adjust: Additional build environments?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you need software from additional platforms (nodejs, rust, golang),
you can add and enable such an environment so you can install the packages you need.

.. seealso::

   :ref:`config-file/v2:build.tools`
     List of all tools that are possible to enable.

Adjust: Custom tools
~~~~~~~~~~~~~~~~~~~~

It's possible to build documentation using almost any documentation tool,
as long as an environment is available (see :ref:`the previous step <config_howto_build.tools>`).

.. seealso::

   :doc:`/build-customization`
     Jump to a full guide explaining how to setup (almost) any documentation tool.

   :ref:`config-file/v2:build.commands`
     Configuration file reference for custom build commands.


Next steps
----------

The configuration options that we mentioned in this guide aren't all.
There are more.

Once you have your configuration file added to your Git repository,
and you can see that Read the Docs is building your documentation using the file,
you should have a look at the complete configuration file reference for options that might apply to your project.

.. seealso::

   :doc:`/config-file/v2`.
     The complete list of all possible ``.readthedocs.yaml`` settings,
     including the optional settings not covered in on this page.
