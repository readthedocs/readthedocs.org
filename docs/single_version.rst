Single Version Documentation
----------------------------

Single Version Documentation lets you serve your docs at a root domain.
By default, all documentation served by Read the Docs has a root of ``/<language>/<version>/``.
But, if you enable the "Single Version" option for a project, its documentation will instead be served at ``/``.

.. warning:: This means you can't have translations or multiple versions for your documentation.

You can see a live example of this at http://www.contribution-guide.org

Enabling
~~~~~~~~

You can toggle the "Single Version" option on or off for your project in the Project Admin page. Check your `dashboard`_ for a list of your projects.

Effects
~~~~~~~

Links generated on Read the Docs will now point to the proper URL. For example, if pip was set as a "Single Version" project, then links to its documentation would point to ``http://pip.readthedocs.org/`` rather than the default ``http://pip.readthedocs.org/en/latest/``.

Documentation at ``/<language>/<default_version>/`` will still be served for backwards compatability reasons. However, our usage of :doc:`canonical` should stop these from being indexed by Google.

.. _dashboard: https://readthedocs.org/dashboard/
