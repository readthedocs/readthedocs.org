Single version documentation
----------------------------

*Single version* documentation lets you serve your documentation at the top level of your domain,
for example ``https://docs.example.com/`` or ``https://example.readthedocs.io/``.

By default, all documentation served by Read the Docs has a standard path of ``/<language>/<version>/``.
Documentation can be served at ``/`` if you enable the *single version* option for a project.

.. warning:: This means you can't have translations or multiple versions for your documentation.

Having a single version of a documentation project can be considered the better choice
in cases where there should only always exist one unambiguous copy of your project.

For example, a research project may wish to *only* expose readers to their latest list of publications and research data.
Similarly, a :abbr:`SaaS (Software as a Service)` application might only ever have one version live.

You can see a live example of this at http://www.contribution-guide.org

Enabling
~~~~~~~~

In your project's :guilabel:`Admin` page, you can toggle the :guilabel:`Single version` option on or off for your project .
Check your :term:`dashboard` for a list of your projects.

Effects
~~~~~~~

Links pointing to the :term:`root URL` of the project will now point to the proper URL.
For example, if pip was set as a "Single Version" project,
then links to its documentation would point to ``https://pip.readthedocs.io/``
rather than redirecting to ``https://pip.readthedocs.io/en/latest/``.

.. warning::

   Documentation at ``/<language>/<default_version>/`` will stop working.
   Remember to set :doc:`canonical URLs </canonical-urls>`
   to tell search engines like Google what to index,
   and to create :doc:`user-defined-redirects` to avoid broken incoming links.
