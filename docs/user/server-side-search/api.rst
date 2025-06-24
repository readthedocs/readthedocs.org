Server side search API
======================

You can integrate our :doc:`server side search </server-side-search/index>` in your documentation by using our API.

If you are using :doc:`/commercial/index` you will need to replace
https://app.readthedocs.org/ with https://app.readthedocs.com/ in all the URLs used in the following examples.
Check :ref:`server-side-search/api:authentication and authorization` if you are using private versions.

API v3
------

.. http:get:: /api/v3/search/

   Return a list of search results for a project or subset of projects.
   Results are divided into sections with highlights of the matching term.

   .. Request

   :query q: Search query (see :doc:`/server-side-search/syntax`)
   :query page: Jump to a specific page
   :query page_size: Limits the results per page, default is 50

   .. Response

   :>json string type: The type of the result, currently page is the only type.
   :>json string project: The project object
   :>json string version: The version object
   :>json string title: The title of the page
   :>json string domain: Canonical domain of the resulting page
   :>json string path: Path to the resulting page
   :>json object highlights: An object containing a list of substrings with matching terms.
                             Note that the text is HTML escaped with the matching terms inside a ``<span>`` tag.
   :>json object blocks:

    A list of block objects containing search results from the page.
    Currently, there is one type of block:

    - section: A page section with a linkable anchor (``id`` attribute).

   .. warning::

      Except for highlights, any other content is not HTML escaped,
      you shouldn't include it in your page without escaping it first.

   **Example request**:

   .. tabs::

      .. code-tab:: bash

         $ curl "https://app.readthedocs.org/api/v3/search/?q=project:docs%20server%20side%20search"

      .. code-tab:: python

         import requests
         URL = 'https://app.readthedocs.org/api/v3/search/'
         params = {
            'q': 'project:docs server side search',
         }
         response = requests.get(URL, params=params)
         print(response.json())

   **Example response**:

   .. sourcecode:: json

      {
          "count": 41,
          "next": "https://app.readthedocs.org/api/v3/search/?page=2&q=project:docs%20server+side+search",
          "previous": null,
          "projects": [
             {
               "slug": "docs",
               "versions": [
                 {"slug": "latest"}
               ]
             }
          ],
          "query": "server side search",
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
                  "title": "Server Side Search",
                  "domain": "https://docs.readthedocs.io",
                  "path": "/en/latest/server-side-search.html",
                  "highlights": {
                      "title": [
                          "<span>Server</span> <span>Side</span> <span>Search</span>"
                      ]
                  },
                  "blocks": [
                     {
                        "type": "section",
                        "id": "server-side-search",
                        "title": "Server Side Search",
                        "content": "Read the Docs provides full-text search across all of the pages of all projects, this is powered by Elasticsearch.",
                        "highlights": {
                           "title": [
                              "<span>Server</span> <span>Side</span> <span>Search</span>"
                           ],
                           "content": [
                              "You can <span>search</span> all projects at https:&#x2F;&#x2F;readthedocs.org&#x2F;<span>search</span>&#x2F"
                           ]
                        }
                     },
                     {
                        "type": "domain",
                        "role": "http:get",
                        "name": "/_/api/v2/search/",
                        "id": "get--_-api-v2-search-",
                        "content": "Retrieve search results for docs",
                        "highlights": {
                           "name": [""],
                           "content": ["Retrieve <span>search</span> results for docs"]
                        }
                     }
                  ]
              },
          ]
      }


Migrating from API v2
~~~~~~~~~~~~~~~~~~~~~

Instead of using query arguments to specify the project
and version to search, you need to do it from the query itself,
this is if you had the following parameters:

- project: docs
- version: latest
- q: test

Now you need to use:

- q: project:docs/latest test

The response of the API is very similar to V2,
with the following changes:

- ``project`` is an object, not a string.
- ``version`` is an object, not a string.
- ``project_alias`` isn't present,
  it is contained in the ``project`` object.

When searching on a parent project,
results from their subprojects won't be included automatically,
to include results from subprojects use the ``subprojects`` parameter.

Authentication and authorization
--------------------------------

If you are using :ref:`private versions <versions:Version states>`,
users will only be allowed to search projects they have permissions over.
Authentication and authorization is done using the current session,
or any of the valid :doc:`sharing methods </commercial/sharing>`.

To be able to use the user's current session you need to use the API from the domain where your docs are being served
(``<you-docs-domain>/_/api/v3/search/``).
This is ``https://docs.readthedocs-hosted.com/_/api/v3/search/``
for the ``https://docs.readthedocs-hosted.com/`` project, for example.

API v2 (deprecated)
-------------------

.. note::

   Please use our :ref:`server-side-search/api:api v3` instead,
   see :ref:`server-side-search/api:migrating from api v2`.

.. http:get:: /api/v2/search/

   Return a list of search results for a project,
   including results from its :doc:`/subprojects`.
   Results are divided into sections with highlights of the matching term.

   .. Request

   :query q: Search query
   :query project: Project slug
   :query version: Version slug
   :query page: Jump to a specific page
   :query page_size: Limits the results per page, default is 50

   .. Response

   :>json string type: The type of the result, currently page is the only type.
   :>json string project: The project slug
   :>json string project_alias: Alias of the project if it's a subproject.
   :>json string version: The version slug
   :>json string title: The title of the page
   :>json string domain: Canonical domain of the resulting page
   :>json string path: Path to the resulting page
   :>json object highlights: An object containing a list of substrings with matching terms.
                             Note that the text is HTML escaped with the matching terms inside a ``<span>`` tag.
   :>json object blocks:

    A list of block objects containing search results from the page.
    Currently, there is one type of block:

    - section: A page section with a linkable anchor (``id`` attribute).

   .. warning::

      Except for highlights, any other content is not HTML escaped,
      you shouldn't include it in your page without escaping it first.

   **Example request**:

   .. tabs::

      .. code-tab:: bash

         $ curl "https://app.readthedocs.org/api/v2/search/?project=docs&version=latest&q=server%20side%20search"

      .. code-tab:: python

         import requests
         URL = 'https://app.readthedocs.org/api/v2/search/'
         params = {
            'q': 'server side search',
            'project': 'docs',
            'version': 'latest',
         }
         response = requests.get(URL, params=params)
         print(response.json())

   **Example response**:

   .. sourcecode:: json

      {
          "count": 41,
          "next": "https://app.readthedocs.org/api/v2/search/?page=2&project=read-the-docs&q=server+side+search&version=latest",
          "previous": null,
          "results": [
              {
                  "type": "page",
                  "project": "docs",
                  "project_alias": null,
                  "version": "latest",
                  "title": "Server Side Search",
                  "domain": "https://docs.readthedocs.io",
                  "path": "/en/latest/server-side-search.html",
                  "highlights": {
                      "title": [
                          "<span>Server</span> <span>Side</span> <span>Search</span>"
                      ]
                  },
                  "blocks": [
                     {
                        "type": "section",
                        "id": "server-side-search",
                        "title": "Server Side Search",
                        "content": "Read the Docs provides full-text search across all of the pages of all projects, this is powered by Elasticsearch.",
                        "highlights": {
                           "title": [
                              "<span>Server</span> <span>Side</span> <span>Search</span>"
                           ],
                           "content": [
                              "You can <span>search</span> all projects at https:&#x2F;&#x2F;readthedocs.org&#x2F;<span>search</span>&#x2F"
                           ]
                        }
                     }
                  ]
              },
          ]
      }
