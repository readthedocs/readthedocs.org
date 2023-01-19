Configuring your project with "Configuration as Code"
=====================================================

You can configure your Read the Docs project by adding a special file ``.readthedocs.yaml`` to your Git repository.
The file can contain a number of settings that are not accessible through the Read the Docs website.

The recommended way to configure a project is therefore also through ``.readthedocs.yaml``.

"Configuration as Code" is a concept whereby the configuration or settings of software is maintained in a Git repository as *code*.
Alternatively, configurations are often added and managed inside the software's own UI,
making it hard to track changes, and reproduce and copy behavior to other projects.

Because of its fragility and uniqueness,
the alternative to "Configuration as Code" is also often referred to as snowflake ❄️ configuration.

.. note::

   Some other variants like ``readthedocs.yaml``, ``.readthedocs.yml``, etc
   are deprecated.

The main advantages of using a configuration file over the web interface are:

- Settings are per version rather than per project.
- Settings live in your VCS.
- They enable reproducible build environments over time.
- Some settings are only available using a configuration file

.. tip::

   Using a configuration file is the recommended way of using Read the Docs.

.. toctree::
    :maxdepth: 3

    Version 2 <v2>
