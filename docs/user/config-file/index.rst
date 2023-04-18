.. TODO: Use new glossary terms added in another PR

Versioning your configuration
=============================

The lifecycle of a documentation project changes the content and the structure of the documentation.
In addition to this,
**the whole configuration of a project also changes**.

But changing your configuration for your documentation's version 2.x should not make it impossible to keep maintaining the documentation for version 1.x using a previous configuration.

.. seealso::

   :doc:`/config-file/v2`
      Reference of all the settings offered in the build configuration file.

Consider the following aspects of a documentation project:

:Build environment:
    You may depend on a number of packages but your method for installing them changes.
    What is installed, how it's installed and what installs it can change.

    For instance,
    you might change between Pip, Pipenv, Conda etc.

    You might also jump between Python 2 and 3 or Python 3.8 and Python 3.10.

:Documentation tools:
    Using Sphinx? Using MkDocs? Or some other tool?
    All these tools have their own configuration files and special ways to invoke them.

    Changing the documentation tool should also be possible in the lifecycle of your documentation.
    Read the Docs understands outputs from several different documentation tools and therefore,
    it's possible to change documentation tools between different versions of documentation.


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

Configuration as Code
---------------------

"Configuration as Code" is a concept whereby the configuration or settings of software is maintained in a Git repository as *code*.
Alternatively, configurations are often added and managed inside the software's own UI,
making it hard to track changes, and reproduce and copy behavior to other projects.

Because of its fragility and uniqueness,
the alternative to "Configuration as Code" is also often referred to as snowflake ❄️ configuration.

.. seealso::

   :doc:`/guides/reproducible-builds`
      In addition to storing your configuration in Git,
      we also recommend special practices for making your builds resilient to changes in your software dependencies.
