Single Version Documentation
----------------------------

Single Version Documentation lets you serve your docs at a root domain.
This means that instead of the URL having ``/<language>/<version>/``,
it will simply be served at ``/``.

.. warning:: This means you can't have translations or multiple versions for your documentation.

Enabling
--------

You can set the canonical URL for your project in the Project Admin page. Check your `dashboard`_ for a list of your projects.

Effects
-------

Links generated on Read the Docs will now point to the proper URL.

Documentation at ``/<language>/<version>/`` will still be served for backwards compatability reasons. Our usage of :doc:`canonical` should stop these from being indexed by Google, though.

.. _dashboard: https://readthedocs.org/dashboard/
