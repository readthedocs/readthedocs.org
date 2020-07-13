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
   Every project hosted on that same domain is included in results for search.

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
   You can see some examples in our :ref:`guides/searching-with-readthedocs:search query syntax` guide.

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
