Requirements files
==================

This is where we keep the dependency information for our various project parts.

pip-tools
---------

We're experimenting with pip-tools for our ``docs.txt`` file.
You can update dependencies there with::

    pip install pip-tools
    pip-compile docs.in

This will then generate a full set of transitive dependencies,
so that our builds shouldn't break.
