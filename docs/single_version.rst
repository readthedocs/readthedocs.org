Single Version Documentation
----------------------------

Single Version Documentation lets you serve your docs at a root domain.
By default, all documentation served by Read the Docs has a root of ``/<language>/<version>/``.
But, if you enable the "Single Version" option for a project, its documentation will instead be served at ``/``.

.. warning:: This means you can't have translations or multiple versions for your documentation.

You can see a live example of this at http://www.contribution-guide.org

Enabling
~~~~~~~~

You can toggle the "Single Version" option on or off for your project in the Project Admin page.
Check your :term:`dashboard` for a list of your projects.

Effects
~~~~~~~

Links pointing to the :term:`root URL` of the project will now point to the proper URL.
For example, if pip was set as a "Single Version" project,
then links to its documentation would point to ``http://pip.readthedocs.io/``
rather than redirecting to ``http://pip.readthedocs.io/en/latest/``.

.. warning::

   Documentation at ``/<language>/<default_version>/`` will stop working.
   Remember to set :ref:`custom_domains:Canonical URLs`
   to tell search engines like Google what to index,
   and to create :doc:`user-defined-redirects` to avoid broken incoming links.
