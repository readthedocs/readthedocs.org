Configuration file overview
===========================

As part of the initial set up of a Read the Docs project,
you need to create a **configuration file** called ``.readthedocs.yaml``.
The configuration file tells Read the Docs what specific settings to use for your project.

This tutorial covers:

.. contents::
    :local:
    :depth: 1

Where to put your configuration file
------------------------------------

The ``.readthedocs.yaml`` file should be placed in the top-most directory of your project's repository.
When you have changed the configuration file,
you need to commit and push the changes to your Git repository.
Read the Docs will then automatically find and use the configuration to build your project.

.. note::

    The Read the Docs configuration file is a `YAML`_ file.
    YAML is a human-friendly data serialization language for all programming languages.
    To learn more about the structure of these files, see the `YAML language overview`_.

.. _YAML: https://yaml.org/
.. _YAML language overview: https://yaml.org/spec/1.2.2/#chapter-1-introduction-to-yaml

.. _howto_templates:

Getting started with a template
-------------------------------

Here are some configuration file examples to help you get started.
Pick an example based on the tool that your project is using,
copy its contents to ``.readthedocs.yaml``,
and add the file to your Git repository.

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

You can find more information about these tools in our :doc:`/intro/doctools`.

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

``version`` key
  The version key tells the system how to read the rest of the configuration file.
  The current and only supported version is **version 2**.

Comments
  We added comments that explain the configuration options and optional features.
  These lines begin with a ``#``.

Commented out features
  We use the ``#`` in front of some popular configuration options.
  They are there as examples,
  which you can choose to enable, delete or save for later.

Adjust: ``build.os``
~~~~~~~~~~~~~~~~~~~~

In our examples,
we are using Read the Docs' custom image based on the latest Ubuntu release.
Package versions in these images will not change drastically,
though will receive periodic security updates.

You should pay attention to this field if your project needs to build on an older version of Ubuntu,
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

- Use ``python.install.path`` to install the project itself as a Python package using pip
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
