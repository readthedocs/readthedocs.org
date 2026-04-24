.. TODO: This is another place where I'd love to share this content with users, but it's not quite there yet.

:orphan:

Why keep configuration files in Git
===================================

Content and structure of documentation undergo big and small changes.
And eventually, the configuration of a documentation project also changes.
This means you need to be able to track these changes over time,
and keep them up to date.

In this article,
we cover the major concepts of using a configuration file:

Versioning the configuration
  A documentation project and its configuration file live together in a Git repository
  and are versioned together.

Configuration as code
  Configuration uses the same workflow as your source code,
  including being reviewed and tested in a pull request.

Options that are not found in the configuration file
  Not everything is suitable for version-specific configuration,
  like the Git repository where the configuration file is read after cloning.

.. seealso::

   :doc:`/config-file/index`
      Practical steps to add a configuration file to your documentation project.

   :doc:`/config-file/v2`
      Reference for configuration file settings.


Why version your project's configuration?
-----------------------------------------

Consider the following aspects of a documentation project:

Build environments change 📦️
  You may depend on a number of packages but your method for installing them changes.
  What is installed, how it's installed and what installs can change,
  especially across multiple versions.

  You might change between Pip and Poetry.
  You might also jump between Python 2 and 3 or Python 3.8 and Python 3.10.

Documentation tools change ⚙️
  Using Sphinx? Using MkDocs? Or some other tool?
  All these tools have their own configuration files and special ways to invoke them.
  In order to switch between how you are invoking the tool and setting up its environment,
  you will need external build configuration.

Comparing changes over time ⚖️
  As your project changes, you will need to change your configuration.
  You might wonder how something was done in the past,
  and having it versioned means you can see each commit as it has changed.

You can configure your Read the Docs project by adding a ``.readthedocs.yaml`` file [1]_ to your Git repository.
The configuration will apply to the exact version that is being built.
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

"Configuration as Code" is a concept where the configuration or settings of software is maintained in a Git repository as *code*.
Contrast this with the approach where configuration is managed inside the software's own UI,
making it hard to track changes, and copy settings to other projects.

Most users of Read the Docs will already be familiar with the concept since many popular tools already require you to store their configuration in your Git repository:

* Sphinx uses a ``conf.py`` file.
* MkDocs uses a ``mkdocs.yaml`` file.
* Python projects often have a ``requirements.txt`` or ``environment.yaml``.

Because of its fragility and uniqueness,
the alternative to "Configuration as Code" is also often referred to as snowflake ❄️ configuration.
Such configurations are hard to copy between projects and also hard to introspect for people without authorization to access the configuration UI.

*Configuration as code* is considered by many to be the easier option.
It might seem harder to have to write the configuration code from scratch,
but in order to use Read the Docs,
you can usually start with a template and adapt it.

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

Domain-level settings
  Since many settings apply to the domain a project is hosted on,
  they are configured for the project itself, and not a specific version.

The goal over time is to have everything that can be managed in a version-specific YAML file configured that way.

.. seealso::

   :doc:`/guides/reproducible-builds`
      In addition to storing your configuration in Git,
      we also recommend special practices for making your builds resilient to changes in your software dependencies.
