Using a configuration file
==========================

During a documentation project's life, both content and structure of the documentation may undergo big and small changes.
And eventually, the configuration of a documentation project also changes.

In this article,
we cover the major concepts that are applied by having a configuration file:

Versioning the configuration
  A documentation project and its configuration file live together in a Git repository
  and are versioned together.

Configuration as code
  A commonly used term which is good to know the background and meaning of.

Options that are **not** found in the configuration file
  Not everything is suitable for *configuration as code*.

.. TODO: Add upcoming configuration file how-to

.. seealso::

   :doc:`/config-file/v2`
      Reference of all the settings offered in the build configuration file.

Why version your project's configuration?
-----------------------------------------

Consider the following aspects of a documentation project:

Build environments change 📦️
  You may depend on a number of packages but your method for installing them changes.
  What is installed, how it's installed and what installs it can change.

  For instance,
  you might change between Pip, Pipenv, Conda etc.
  You might also jump between Python 2 and 3 or Python 3.8 and Python 3.10.

Documentation tool setups change ⚙️
  Using Sphinx? Using MkDocs? Or some other tool?
  All these tools have their own configuration files and special ways to invoke them.
  In order to switch between how you are invoking the tool and setting up its environment,
  you will need external build configuration.

Switching documentation tools 💣️
  Long-lived software projects can go through many phases in their history.
  This includes changing the documentation tool.


You can configure your Read the Docs project by adding a special file ``.readthedocs.yaml`` [1]_ to your Git repository.

Because the file is stored in Git,
the configuration will apply to the exact version that is being built.
This allows you to store different configurations for different versions of your documentation.

The main advantages of using a configuration file over the web interface are:

- Settings are per version rather than per project.
- Settings live in your Git repository.
- They enable reproducible build environments over time.
- Some settings are only available using a configuration file

.. [1] Other variants of the configuration file name like ``readthedocs.yaml``, ``.readthedocs.yml``, etc. are deprecated.
       You may however, :doc:`configure a custom sub-folder </guides/setup/monorepo>`.

Configuration as Code
---------------------

"Configuration as Code" is a concept whereby the configuration or settings of software is maintained in a Git repository as *code*.
Alternatively, configurations are often added and managed inside the software's own UI,
making it hard to track changes, and reproduce and copy behavior to other projects.

Most users of Read the Docs will already be familiar with the concept since many popular tools already require you to store their configuration in your Git repository:

* Sphinx uses a ``conf.py`` file.
* MkDocs uses a ``mkdocs.yaml`` file.
* Python projects in general have a ``requirements.txt`` or similar.

Because of its fragility and uniqueness,
the alternative to "Configuration as Code" is also often referred to as snowflake ❄️ configuration.
Such configurations are hard to copy between projects and also hard to introspect for people without authorization to access the configuration UI.


Expressing a configuration *as code* is therefore considered by many to be the easier option.
It might seem harder to have to write the configuration code from scratch,
but in order to use Read the Docs,
you can usually start by copy-pasting a template and adapting it.

Read the Docs has chosen to offer as much configuration as possible through the usage of ``.readthedocs.yaml``.
Our experience is that projects benefit from such a setup,
and even when the benefits aren't obvious in the beginning of a project's lifecycle,
they will emerge over time.

What's not covered by ``.readthedocs.yaml``?
--------------------------------------------

There are a number of things that aren't possible to cover in the configuration file,
which still belong in your project's Dashboard.

These configuration items are for instance:

Git settings
  Since the configuration file is stored in Git,
  it doesn't make sense that it would configure the Git setup.

Custom domains and redirects
  Settings

Other general non-versioned settings
  In general,
  settings that aren't versioned and do not relate to how your project is built are accessed via your :term:`dashboard`.

.. seealso::

   :doc:`/guides/reproducible-builds`
      In addition to storing your configuration in Git,
      we also recommend special practices for making your builds resilient to changes in your software dependencies.
