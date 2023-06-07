How to add a configuration file
===============================

As part of the initial setup for your Read the Docs site,
you need to create a **configuration file** called ``.readthedocs.yaml``.
The configuration file tells Read the Docs what specific settings to use for your project.

This how-to guide covers:

#. Where to put your configuration file.
#. Templates to setup your configuration file from scratch.
#. The most basic sections in the configuration file that can help you get started.
#. Next steps

.. seealso::

   :doc:`/tutorial/index`.
     Following the steps in our tutorial will help you setup your first documentation project.


Where to put your configuration file
------------------------------------

The ``.readthedocs.yaml`` file should be placed in the top-most directory of your project's repository.
We will get to the contents of the file in the next steps.

When you have changed the configuration file,
you need to commit and push the changes to your Git repository.
Read the Docs will then automatical find and use the configuration to build your project.

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

But the file probably needs some changes to accomodate exactly your project setup.

The configuration file is a `YAML`_ file. YAML files are a "map": a collection of
key-value pairs that can be nested. This is not unlike a JSON file or ``dict``
object in Python.

This page won't explain the structure of YAML files, but many resources exist
online.

.. _YAML: https://en.wikipedia.org/wiki/YAML

File header
~~~~~~~~~~~

The first part of the file does not need to be edited:

#. A comment explaning the configuration file.
#. A convenient comment with a link to
   :doc:`the configuration file reference page </config-file/index>`.
#. The version key tells the system how to read the rest of the configuration file.
   The current and only supported version is **version 2**.

.. code-block:: yaml

   # .readthedocs.yaml
   # See the reference for the Read the Docs configuration file:
   # https://docs.readthedocs.io/en/stable/config-file/v2.html for details

   version: 2

Python requirements
~~~~~~~~~~~~~~~~~~~

If you are using Python in your builds,
you should define the Python version.
You can also define your additional Python requirements.

The ``python`` key contains a list of sub-keys,
specifying the requirements to install.

The ``requirements`` key is a file path that points to a text (``.txt``) file
that lists the Python packages you want Read the Docs to install.

.. code-block:: yaml

   # Optional but recommended, declare the Python requirements required
   # to build your documentation
   # See https://docs.readthedocs.io/en/stable/guides/reproducible-builds.html
   python:
     install:
     - requirements: docs/requirements.txt

Next steps
----------

Once you have your configuration file added to your Git repository,
and you can see that Read the Docs is building your documentation using the file,
you should have a look at the complete configuration file reference for options that might apply to your project.


.. seealso::

   :doc:`/config-file/v2`.
     The complete list of all possible ``.readthedocs.yaml`` settings,
     including the optional settings not covered in on this page.
