New search API
==============

Goals
-----

- Allow to configure search at the API level,
  instead of having the options in the database.
- Allow to search a group of projects/versions at the same time.
- Bring the same syntax to the dashboard search.

Syntax
------

The parameters will be given in the query using the ``key:value`` syntax.
Inspired by `GitHub <https://docs.github.com/en/rest/search>`__ and other services.

Currently the values from all parameters don't include spaces,
so surrounding the value with quotes won't be supported (``key:"value"``).

To avoid interpreting a query as a parameter,
an escape character can be put in place,
for example ``project\:docs`` won't be interpreted as
a parameter, but as the search term ``project:docs``.
This is only necessary if the query includes a valid parameter,
unknown parameters (``foo:bar``) don't require escaping.

All other tokens that don't match a valid parameter,
will be join to form the final search term.

Parameters
----------

project:
  Indicates the project and version
  to includes results from (this doesn't include subprojects).
  If the version isn't provided,
  the default version is used.

  Examples:

  - ``project:docs/latest``
  - ``project:docs``

  It can be one or more project parameters.
  At least one is required.

  If the user doesn't have permission over one version or if the version doesn't exist,
  we don't include results from that version.
  We don't fail the search, this is so users can use one endpoint for all their users,
  without worrying about what permissions each user has or updating it after a version or project
  has been deleted.

  The ``/`` is used as separator,
  but it could be any other character that isn't present in the slug of a version or project.
  ``:`` was considered (``project:docs:latest``), but it could be hard to read
  since ``:`` is already used to separate the key from the value.

subprojects:
  This allows to specify from what project exactly
  we are going to return subprojects from,
  and also include the version we are going to try to match.
  This includes the parent project in the results.

  As the ``project`` parameter, the version can be optional,
  and defaults to the default version of the parent project.

user:
  Include results from projects the given user has access to.
  The only supported value is ``@me``,
  which is an alias for the current user.

Including subprojects
~~~~~~~~~~~~~~~~~~~~~

Now that we are returning results only
from the given projects, we need an easy way to
include results from subprojects.
Some ideas for implementing this feature are:

``include-subprojects:true``
  This doesn't make it clear from what
  projects we are going to include subprojects from.
  We could make it so it returns subprojects for all projects.
  Users will probably use this with one project only.

``subprojects:project/version`` (inclusive)
  This allows to specify from what project exactly
  we are going to return subprojects from,
  and also include the version we are going to try to match.
  This includes the parent project in the results.

  As the ``project`` parameter, the version can be optional,
  and defaults to the default version of the parent project.

``subprojects:project/version`` (exclusive)
  This is the same as the above,
  but it doesn't include the parent project in the results.
  If we want to include the results from the project, then
  the query will be ``project:project/latest subprojects:project/latest``.
  Is this useful?

The second option was chosen, since that's the current behavior
of our search when searching on a project with subprojects,
and avoids having to repeat the project if the user wants to
include it in the search too.

Cache
-----

Since the request could be attached to more than one project.
We will return all the list of projects for the cache tags,
this is ``project1, project1:version, project2, project2:version``.

CORS
----

Since the request could be attached to more than one project.
we can't make the decision if we should enable CORS or not on a given request from the middleware easily,
so we won't allow cross site requests when using the new API for now.
We would need to refactor our CORS code,
so every view can decide if CORS should be allowed or not,
for this case, cross site requests will be allowed only if all versions of the final search are public,
another alternative could be to always allow cross site requests,
but when a request is cross site, we only return results from public versions.

Analytics
---------

We will record the same query for each project that was used in the final search.

Response
--------

The response will be similar to the old one,
but will include extra information about the search,
like the projects, versions, and the query that were used in the final search.

And the ``version``, ``project``, and ``project_alias`` attributes will
now be objects.

We could just reuse the old response too,
since the only breaking changes would be the attributes now being objects,
and we aren't adding any new information to those objects (yet).
But also, re-using the current serializers shouldn't be a problem either.

.. code-block:: json

   {
     "count": 1,
     "next": null,
     "previous": null,
     "projects": [
       {
         "slug": "docs",
         "versions": [
           {
             "slug": "latest"
           }
         ]
       }
     ],
     "query": "The final query used in the search",
     "results": [
       {
         "type": "page",
         "project": {
           "slug": "docs",
           "alias": null
         },
         "version": {
           "slug": "latest"
         },
         "title": "Main Features",
         "path": "/en/latest/features.html",
         "domain": "https://docs.readthedocs.io",
         "highlights": {
           "title": []
         },
         "blocks": [
           {
             "type": "section",
             "id": "full-text-search",
             "title": "Full-Text Search",
             "content": "We provide search across all the projects that we host. This actually comes in two different search experiences: dashboard search on the Read the Docs dashboard and in-doc search on documentation sites, using your own theme and our search results. We offer a number of search features: Search across subprojects Search results land on the exact content you were looking for Search across projects you have access to (available on Read the Docs for Business) A full range of search operators including exact matching and excluding phrases. Learn more about Server Side Search.",
             "highlights": {
               "title": [
                 "Full-<span>Text</span> Search"
               ],
               "content": []
             }
           },
           {
             "type": "domain",
             "role": "http:post",
             "name": "/api/v3/projects/",
             "id": "post--api-v3-projects-",
             "content": "Import a project under authenticated user. Example request: BashPython$ curl \\ -X POST \\ -H \"Authorization: Token <token>\" https://app.readthedocs.org/api/v3/projects/ \\ -H \"Content-Type: application/json\" \\ -d @body.json import requests import json URL = 'https://app.readthedocs.org/api/v3/projects/' TOKEN = '<token>' HEADERS = {'Authorization': f'token {TOKEN}'} data = json.load(open('body.json', 'rb')) response = requests.post( URL, json=data, headers=HEADERS, ) print(response.json()) The content of body.json is like, { \"name\": \"Test Project\", \"repository\": { \"url\": \"https://github.com/readthedocs/template\", \"type\": \"git\" }, \"homepage\": \"http://template.readthedocs.io/\", \"programming_language\": \"py\", \"language\": \"es\" } Example response: See Project details Note Read the Docs for Business, also accepts",
             "highlights": {
               "name": [],
               "content": [
                 ", json=data, headers=HEADERS, ) print(response.json()) The content of body.json is like,  &quot;name&quot;: &quot;<span>Test</span>"
               ]
             }
           }
         ]
       }
     ]
   }

Examples
--------

- ``project:docs project:dev/latest test``: search for ``test`` in the default
  version of the ``docs`` project, and in the latest version of the ``dev`` project.
- ``a project:docs/stable search term``: search for ``a search term`` in the
  stable version of the ``docs`` project.

- ``project:docs project\:project/version``: search for ``project::project/version`` in the
  default version of the ``docs`` project.

- ``search``: invalid, at least one project is required.

Dashboard search
----------------

This is the search feature that you can access from
the readthedocs.org/readthedocs.com domains.

We have two types:

Project scoped search:
   Search files and versions of the current project only.

Global search:
   Search files and versions of all projects in .org,
   and only the projects the user has access to in .com.

   Global search also allows to search projects by name/description.

This search also allows you to see the number of results
from other projects/versions/sphinx domains (facets).

Project scoped search
~~~~~~~~~~~~~~~~~~~~~

Here the new syntax won't have effect,
since we are searching for the files of one project only!

Another approach could be linking to the global search
with ``project:{project.slug}`` filled in the query.

Global search (projects)
~~~~~~~~~~~~~~~~~~~~~~~~

We can keep the project search as is,
without using the new syntax (since it doesn't make sense there).

Global search (files)
~~~~~~~~~~~~~~~~~~~~~

Using the same syntax from the API will be allowed,
by default it will search all projects in .org,
and all projects the user has access to in .com.

Another approach could be to allow
filtering by user on .org, this is ``user:stsewd`` or ``user:@me``
so a user can search all their projects easily.
We could allow just ``@me`` to start.

Facets
~~~~~~

We will support only the ``projects`` facet to start.

We can keep the facets, but they would be a little different,
since with the new syntax we need to specify a project in order to search for
a version, i.e, we can't search all ``latest`` versions of all projects.

By default we will use/show the ``project`` facet,
and after the user has filtered by a project,
we will use/show the ``version`` facet.

If the user searches more than one project,
things get complicated, should we keep showing the ``version`` facet?
If clicked, should we change the version on all the projects?

If that is too complicated to explain/implement,
we should be fine by just supporting the ``project``
facet for now.

Backwards compatibility
~~~~~~~~~~~~~~~~~~~~~~~

We should be able to keep the old URLs working in the global search,
but we could also just ignore the old syntax, or transform
the old syntax to the new one and redirect the user to it,
for example ``?q=test&project=docs&version=latest``
would be transformed to ``?q=test project:docs/latest``.

Future features
---------------

- Allow searching on several versions of the same project
  (the API response is prepared to support this).
- Allow searching on all versions of a project easily,
  with a syntax like ``project:docs/*`` or ``project:docs/@all``.
- Allow specify the type of search:

  - Multi match (query as is)
  - Simple query string (allows using the ES query syntax)
  - Fuzzy search (same as multi match, but with fuzziness)

- Add the ``org`` filter,
  so users can search by all projects that belong
  to an organization.
  We would show results of the default versions of each project.
