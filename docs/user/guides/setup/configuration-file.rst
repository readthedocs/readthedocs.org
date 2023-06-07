How to add a configuration file
===============================

As part of the initial setup for your Read the Docs site,
you need to create a **configuration file** called ``.readthedocs.yaml``.

The configuration file tells the platform what specific settings to use for your project.

.. TODO: This isn't really how-to content. We might want to add "Configuration as Code" or similar to our features in order to deal with this.
.. I have another PR open where this is added.

.. By using a configuration file,
.. you can tailor the behavior of Read the Docs to match your project's specific needs.
.. In addition that that,
.. using a configuration file can capture important configuration options that might otherwise break in the future if left undefined.

This how-to guide covers:

#. Where to put your configuration file.
#. What to add to your configuration file.

This should be enough to get you started!

.. seealso::

   :doc:`/config-file/index`.
     The complete list of all possible ``.readthedocs.yaml`` settings,
     including the optional settings not covered in on this page.


Where to put your configuration file
------------------------------------

The ``.readthedocs.yaml`` file should be placed in the top-most directory of your project's repository.

Add a new file with the exact name ``.readthedocs.yaml`` in the repository's root directory.
We will get to the contents of the file in a moment.


Examples to get started
-----------------------

Here are some variations of the configuration file that can help you get started.
Pick the one that resembles your project the most.

.. tabs::

    .. tab:: Sphinx

        If your project uses Sphinx,
        we offer a special builder optimized for Sphinx projects.

        .. literalinclude:: /config-file/examples/sphinx/.readthedocs.yaml
           :linenos:


    .. tab:: MkDocs

        If your project uses MkDocs,
        we offer a special builder optimized for MkDocs projects.

        .. literalinclude:: /config-file/examples/mkdocs/.readthedocs.yaml
           :linenos:

    .. tab:: Custom builder

        If you are using another tool,
        you can configure the commands of your documentation tool in the following code.


The required parts of your configuration file
---------------------------------------------

The configuration file is a `YAML`_ file. YAML files are a "map": a collection of
key-value pairs that can be nested. This is not unlike a JSON file or ``dict``
object in Python.

This page won't explain the structure of YAML files, but many resources exist
online.

.. _YAML: https://en.wikipedia.org/wiki/YAML

File header
~~~~~~~~~~~

As a best practice, begin your file by providing the following.

#. The name of the file
#. A quick explanation of what the file is
#. A link to
   :doc:`the configuration file reference page </config-file/index>`.

.. code-block:: yaml
   :linenos:

   # .readthedocs.yaml
   # Read the Docs configuration file
   # See https://docs.readthedocs.io/en/stable/config-file/v2.html for details
   # <--Remove this comment and leave this line blank-->


Version of configuration file schema
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The version key tells the system how to read the rest of the configuration
file. The current and only supported version is **version 2**.

.. code-block:: yaml
   :linenos:
   :lineno-start: 5

   version: 2
   # <--Remove this comment and leave this line blank-->

Python requirements
~~~~~~~~~~~~~~~~~~~

The ``python`` key contains several sub-keys, but only one sub-key is required:
``requirements``. However, since ``requirements`` is required, ``python`` is
too.

The ``requirements`` key is a file path that points to a text (``.txt``) file
that lists the Python packages you want Read the Docs to install.
