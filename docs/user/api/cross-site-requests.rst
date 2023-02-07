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
This means you can make use of those APIs to get information from public versions only.

Cookies
-------

For |org_brand| our session cookies have the ``SameSite`` attribute set to ``None``,
this means they can be sent in cross site requests.
This is needed for our sustainability API only,
to not show ads if the current user is a :ref:`Gold User <advertising/ad-blocking:Going ad-free>`.
All resources in |org_brand| are public, you don't need to pass cookies to make use
of our allowed APIs from other sites.

For |com_brand| our session cookies have the ``SameSite`` attribute set to ``Lax``,
this means they can't be included in cross site requests.
If you need to have access to versions that the current user has permissions over,
you can make use of our proxied APIs, they can be accessed from docs domains with the `/_/` prefix.
For example, you can make use of our search API from `<your-docs-domain>/_/api/v2/search/`.
