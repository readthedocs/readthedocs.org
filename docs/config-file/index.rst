Configuration File
==================

In addition to using the admin panel of your project to configure your project,
you can use a configuration file in the root of your project.
The configuration file can be named as:

- ``readthedocs.yml``
- ``readthedocs.yaml``
- ``.readthedocs.yml``
- ``.readthedocs.yaml``

The main advantages of using a configuration file over the web interface are:

- Some settings are only available using a configuration file
- The settings are per version rather than per project.
- The settings live in your VCS.
- Reproducible build environments over time.

.. tip::
   
   Using a configuration file is the recommended way of using Read the Docs.

.. toctree::
    :maxdepth: 3

    Version 2 <v2>
    Version 1 <v1>
