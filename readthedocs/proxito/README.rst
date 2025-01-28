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
   This prefix can be different for project defining a custom prefix.

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

Custom path prefixes
--------------------

By default we serve documentation from the following paths:

- Multi version project: ``/<language>/<version>/<filename>``
- Single version project: ``/<filename>``
- Subproject (multi version): ``/projects/<subproject-alias>/<language>/<version>/<filename>``
- Subproject (single version): ``/projects/<subproject-alias>/<filename>``

Custom path prefixes can be used to change the prefix from where the documentation is served from,
and even change the ``/projects`` prefix for subprojects.
These prefixes can be changed per project, with the following Project model attributes:

custom_prefix:
   Add a prefix for multi version and single version projects.

custom_subproject_prefix:
   Change the ``/projects`` prefix for subprojects.
   To change the prefix of the subproject itself, use ``custom_prefix`` on the subproject.

Where to define the custom path prefix
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To change the path prefix of a project,
define the prefix in the ``custom_prefix`` attribute of the project itself.
For a translation, change the main language project ``custom_prefix`` attribute.

And to change the prefix of subprojects (``/projects``),
define the prefix in the ``custom_subproject_prefix`` attribute of the super project.

The custom prefix and subproject prefix can overlap
as long as the first non-overlapping part doesn't match a language code.
For example ``/``/``/``, ``/projects/``/``/projects/``, ``/prefix/``/``/prefix/more/`` are valid,
but ``/``/``/en/``, ``/prefix/``/``/prefix/en/``, ``/prefix/``/``/prefix/en/foo/`` are not.

We have validations in place to ensure that the custom prefix is defined in the correct project
(this validations are run when the project is saved from a form or the admin).

Examples
~~~~~~~~

Say we have the following projects:

- docs (main project)
- docs-es (spanish translation of the docs project)
- subproject (subproject of the docs project)
- subproject-es (spanish translation of the subproject project)

They are normally served from:

- docs.rtd.io/en/latest/
- docs.rtd.io/es/latest/
- docs.rtd.io/projects/subproject/en/latest/
- docs.rtd.io/projects/subproject/es/latest/

Then we add a custom path prefix like:

- docs with a custom path prefix of ``/prefix/``
- docs with a custom subproject path of ``/s/``

Now they will be served from:

- docs.rtd.io/prefix/en/latest/
- docs.rtd.io/prefix/es/latest/
- docs.rtd.io/s/subproject/en/latest/
- docs.rtd.io/s/subproject/es/latest/

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
