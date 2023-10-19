Understanding the security implications of documentation pages
==============================================================

This article explains the security implications of documentation pages,
this doesn't apply to the main website (readthedocs.org/readthedocs.com),
only to documentation pages.

.. seealso::

   :doc:`/api/cross-site-requests`
      Learn about cross-origin requests in our public APIs.

Cross-origin requests
---------------------

Read the Docs allows `cross-origin requests`_ for documentation resource it serves.
However, internal and proxied APIs, typically found under the ``/_/`` path don't allow cross-origin requests.

To facilitate this, the following headers are added to all responses from documentation pages:

- ``Access-Control-Allow-Origin: *``
- ``Access-Control-Allow-Methods: GET, HEAD, OPTIONS``

These headers allow cross-origin requests from any origin
and only allow the GET, HEAD and OPTIONS methods.
It's important to note that passing credentials (such as cookies or HTTP authentication)
in cross-origin requests is not allowed,
ensuring access to public resources only.

Having cross-origin requests enabled allows third-party websites to make use of files from your documentation,
which allows various third-party integrations to work.

If needed, these headers can be changed for your documentation pages by :doc:`contacting support </support>`.

.. _cross-origin requests: https://en.wikipedia.org/wiki/Cross-origin_resource_sharing

Cookies
-------

On |org_brand|, we don't use cookies, as all resources are public.

On |com_brand|, we use cookies to store user sessions.
These cookies are set when a user authenticates to access private documentation.
Session cookies have the ``SameSite`` attribute set to ``None``,
which allows them to be sent in cross-origin requests where allowed.

Embedding documentation pages
-----------------------------

Embedding documentation pages in an iframe is allowed.
Read the Docs doesn't set the ``X-Frame-Options`` header,
which means that the browser's default behavior is used.

Embedding private documentation pages in an iframe is possible,
but it requires users to be previously authenticated in the embedded domain.

It's important to note that embedding documentation pages in an iframe does not grant the parent page access the iframe's content.
Documentation pages serve static content only, and the exposed APIs are read-only,
making the exploitation of a clickjacking vulnerability very unlikely.

If needed, this header can be set on your documentation pages by :doc:`contacting support </support>`.
