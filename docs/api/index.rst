Public API
==========

This section of the documentation details the public API
usable to get details of projects, builds, versions and other details
from Read the Docs.

.. toctree::
   :maxdepth: 3

   v3
   v2

Other APIs
----------

Some Read the Docs features have their own APIs.

- :ref:`Server Side Search <server-side-search:api>`
- :doc:`/embed-api`

Internal APIs
-------------

There are some undocumented endpoints in our APIs that are for internal usage.
These should not be used and could change at any time.

- Footer data (``/_/api/v2/footer_html/``)
- Analytics (``/_/api/v2/analytics/``)
- Advertising (``/api/v2/sustainability/``)
- Any other endpoints not documented

.. note::

   Endpoints that start with ``/_`` are served from the same domain of the documentation.
