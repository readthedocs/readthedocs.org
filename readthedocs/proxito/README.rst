Proxito
=======

Module in charge of serving documentation pages.

Read the Docs core team members can view the `Proxito design doc <https://github.com/readthedocs/el-proxito/blob/master/docs/design/architecture.rst>`_

URL parts
---------

In our code we use the following terms to refer to the different parts of the URL:

url:
   The full URL including the protocol, for example ``https://docs.readthedocs.io/en/latest/api/index.html``.
path:
   The whole path from the URL without query arguments or fragment,
   for example ``/en/latest/api/index.html``.
domain:
   The domain/subdomain without the protocol, for example ``docs.readthedocs.io``.
language:
   The language of the documentation, for example ``en``.
version:
   The version of the documentation, for example ``latest``.
filename:
   The name of the file being served, for example ``/api/index.html``.
path prefix:
   The path prefix of the URL without version or language,
   for a normal project this is ``/``, and for subprojects this is ``/projects/<subproject-alias>/``.
   This prefix can be different for project defining their own urlconf.

.. code:: text

                         URL
   |----------------------------------------------------|
                                        path
                              |-------------------------|
    https://docs.readthedocs.io/en/latest/api/index.html
   |-------|-------------------|--|------|--------------|
    protocol         |          |     |         |
                   domain       |     |         |
                             language |         |
                                    version     |
                                             filename

CDN
---

We use the ``CDN-Cache-Control`` header to control caching at the CDN level,
this doesn't affect caching at the browser level (``Cache-Control``).
See https://developers.cloudflare.com/cache/about/cdn-cache-control.

The cache control header is only used when privacy levels
are enabled (otherwise everything is public by default).

By default, all requests on proxito are marked as private,
but individual views may mark a request as public.
This was done since what is considered public varies on each view,
or the details to know this are only accessible on the view itself
(like the final project attached to the request).

What can/can't be cached?
~~~~~~~~~~~~~~~~~~~~~~~~~

- Footer: should never be cached.
  We show a different footer depending on the user,
  even if they are on a public version.
- ServePageRedirect: can be cached for public versions, or for all versions,
  as the final URL will check for authz.
- ServeDocs: can be cached for public versions.
- ServeError404:
  This view checks for user permissions, can't be cached.

  We could cache it only:
  - If the response is a redirect (slash redirect or user redirect) and the version is public.
  - If current version and the default version are public (when serving a custom 404 page).

- ServeRobotsTXT: can be cached, we don't serve a custom robots.txt
  to any user if the default version is private.
- ServeSitemapXML: can be cached. It displays only public versions, for everyone.
- ServeStaticFiles: can be cached, all files are the same for all projects and users.
- Embed API: can be cached for public versions.
- Search:
  This view checks for user permissions, can't be cached.
  Additionally, to the privacy level of the version,
  we check for authz when including results from subprojects,
  so search results may be distinct for each user.

  We could cache it only:
  - If the project doesn't have subprojects.
  - All subprojects are public.
- Analytics API: can't be cached, we want to always hit our serves with this one.
- Health check view: shouldn't be cached, we always want to hit our serves with this one.
