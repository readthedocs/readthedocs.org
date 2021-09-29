Server Side Search
==================

Read the Docs provides full-text search across all of the pages of all projects,
this is powered by Elasticsearch_.
You can search all projects at https://readthedocs.org/search/,
or search only on your project from the :guilabel:`Search` tab of your project.

We override the default search engine of your project with our search engine
to provide you better results within your project.
We fallback to the built-in search engine from your project
if our search engine doesn't return any results,
just in case we missed something |:smile:|

Search features
---------------

We offer a number of benefits compared to other documentation hosts:

Search across :doc:`subprojects </subprojects>`
   Subprojects allow you to host multiple discrete projects on a single domain.
   Every subproject hosted on that same domain is included in the search results of the main project.

Search results land on the exact content you were looking for
   We index every heading in the document,
   allowing you to get search results exactly to the content that you are searching for.
   Try this out by searching for `"full-text search"`_.

Full control over which results should be listed first
   Set a custom rank per page,
   allowing you to deprecate content, and always show relevant content to your users first.
   See :ref:`config-file/v2:search.ranking`.

Search across projects you have access to (|com_brand|)
   This allows you to search across all the projects you access to in your Dashboard.
   **Don't remember where you found that document the other day?
   No problem, you can search across them all.**

Special query syntax for more specific results.
   We support a full range of search queries.
   You can see some examples in our :ref:`guides/advanced-search:search query syntax` guide.

Configurable.
   Tweak search results according to your needs using a
   :ref:`configuration file <config-file/v2:search>`.

..
   Code object searching
      With the user of :doc:`Sphinx Domains <sphinx:/usage/restructuredtext/domains>` we are able to automatically provide direct search results to your Code objects.
      You can try this out with our docs here by searching for
      TODO: Find good examples in our docs, API maybe?

.. _"full-text search": https://docs.readthedocs.io/en/latest/search.html?q=%22full-text+search%22

Analytics
---------

Know what your users are looking for in your docs.
To see a list of the top queries and an overview from the last month,
go to the :guilabel:`Admin` tab of your project,
and then click on :guilabel:`Search Analytics`.

.. figure:: /_static/images/search-analytics-demo.png
   :width: 50%
   :align: center
   :alt: Search analytics demo

   Search analytics demo

.. _Elasticsearch: https://www.elastic.co/products/elasticsearch

API
---

If you are using :doc:`/commercial/index` you will need to replace
https://readthedocs.org/ with https://readthedocs.com/ in all the URLs used in the following examples.
Check :ref:`server-side-search:authentication and authorization` if you are using private versions.

.. warning::

   This API isn't stable yet, some small things may change in the future.

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
                             Note that the text is HTML escaped with the matching terms inside a <span> tag.
   :>json object blocks:

    A list of block objects containing search results from the page.
    Currently, there are two types of blocks:

    - section: A page section with a linkable anchor (``id`` attribute).
    - domain: A Sphinx :doc:`domain <sphinx:usage/restructuredtext/domains>`
      with a linkable anchor (``id`` attribute).


   **Example request**:

   .. tabs::

      .. code-tab:: bash

         $ curl "https://readthedocs.org/api/v2/search/?project=docs&version=latest&q=server%20side%20search"

      .. code-tab:: python

         import requests
         URL = 'https://readthedocs.org/api/v2/search/'
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
          "next": "https://readthedocs.org/api/v2/search/?page=2&project=read-the-docs&q=server+side+search&version=latest",
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

Authentication and authorization
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you are using :ref:`private versions <versions:privacy levels>`,
users will only be allowed to search projects they have permissions over.
Authentication and authorization is done using the current session,
or any of the valid :doc:`sharing methods </commercial/sharing>`.

To be able to use the user's current session you need to use the API from the domain where your docs are being served
(``<you-docs-domain>/_/api/v2/search/``).
This is ``https://docs.readthedocs-hosted.com/_/api/v2/search/``
for the ``https://docs.readthedocs-hosted.com/`` project, for example.
