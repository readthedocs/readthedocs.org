Cross-site requests
===================

Cross site requests are allowed for the following endpoints:

- :ref:`/api/v2/footer_html/ <api/v2:Undocumented resources and endpoints>`
- :ref:`/api/v2/search/ <server-side-search/api:API V2 (deprecated)>`
- :ref:`/api/v2/embed/ <api/v2:Embed>`
- :ref:`/api/v2/sustainability/ <api/v2:Undocumented resources and endpoints>`
- :ref:`/api/v3/embed/ <api/v3:Embed>`

Except for the sustainability API, all of the above endpoints
don't allow you to pass credentials in cross-site requests.
In other words, these API endpoints allow you to access **public information only**.

On a technical level, this is achieved by implementing the CORS_ standard,
which is supported by all major browsers.
We implement it such way that it strictly match the intention of the API endpoint.

.. _CORS: https://en.wikipedia.org/wiki/Cross-origin_resource_sharing

Cookies
-------

On |org_brand|, our session cookies have the ``SameSite`` attribute set to ``Lax``,
This means that browsers will not include them in cross site requests.
All resources in |org_brand| are public, you don't need to pass cookies to make use
of our allowed APIs from other sites.

On |com_brand|, our session cookies have the ``SameSite`` attribute set to ``Lax``,
this means that browsers will not include them in cross site requests.
If you need to have access to versions that the current user has permissions over,
you can make use of our proxied APIs, they can be accessed from docs domains with the `/_/` prefix.
For example, you can make use of our search API from `<your-docs-domain>/_/api/v2/search/`.
