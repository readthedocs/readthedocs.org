Configuration File
==================

In addition to using the admin panel of your project to configure your project,
you can use a configuration file in the root of your project.
The configuration file should be named ``.readthedocs.yaml``.

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
    Version 1 <v1>
