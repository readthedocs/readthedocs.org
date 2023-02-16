Versioning your entire configuration
====================================

The life-cycle of a documentation project changes the content and the structure of the documentation.
In addition to this, **the whole configuration of a project also changes**.



Consider the following aspects of a documentation project:

:Software tools:
    You may depend on a number of packages but your method for installing them changes.
    What is installed, how it's installed and what installs it can change.
    For instance,
    you might change between Pip, Pipenv, Conda etc.
    It's also very common to develop the way that software is installed by invoking your dependency manager differently.

:Documentation tools:
    Using Sphinx? Using MkDocs? Or some other tool?
    Changing the documentation tool should be possible in the lifecycle of your documentation or software project.
    Read the Docs understands outputs from several different documentation tools and therefore,
    it's possible to change documentation tools between different versions of documentation.



You can configure your Read the Docs project by adding a special file ``.readthedocs.yaml`` [1]_ to your Git repository.

Because the file is stored in Git,
the configuration will apply to the exact version that is being built.
This allows you to store different configurations for different versions of your documentation.


The main advantages of using a configuration file over the web interface are:

- Settings are per version rather than per project.
- Settings live in your VCS.
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
