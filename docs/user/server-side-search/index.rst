Server Side Search
==================

Read the Docs provides full-text search across all of the pages of all projects,
this is powered by Elasticsearch_.
You can search all projects at https://readthedocs.org/search/,
or search only on your project from the :guilabel:`Search` tab of your project.

.. contents:: Table of contents
   :local:
   :backlinks: none
   :depth: 3

.. toctree::
   :maxdepth: 2
   :glob:
   :hidden:

   *

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

Search across projects you have access to
   Search across all the projects you access to in your Dashboard.
   **Don't remember where you found that document the other day?
   No problem, you can search across them all.**

   You can also specify what projects you want to search
   using the ``project:{name}`` syntax, for example:
   `"project:docs project:dev search"`_.
   See :doc:`/server-side-search/syntax`.

Special query syntax for more specific results
   We support a full range of search queries.
   You can see some examples at :ref:`server-side-search/syntax:special queries`.

Configurable
   Tweak search results according to your needs using a
   :ref:`configuration file <config-file/v2:search>`.

Ready to use
   We override the default search engine of your Sphinx project with ours
   to provide you with all these benefits within your project.
   We fallback to the built-in search engine from your project if ours doesn't return any results,
   just in case we missed something |:smile:|.

API
   Integrate our search as you like.
   See :doc:`/server-side-search/api`.

.. _"full-text search": https://docs.readthedocs.io/en/latest/search.html?q=%22full-text+search%22
.. _"project:docs project:dev search": https://docs.readthedocs.io/en/latest/search.html?q=project:docs+project:dev+search

Search analytics
----------------

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


Search as you type
------------------

`readthedocs-sphinx-search`_ is a Sphinx extension that integrates your
documentation more closely with the search implementation of Read the Docs.
It adds a clean and minimal full-page search UI that supports a **search as you type** feature.

To try this feature,
you can press :guilabel:`/` (forward slash) and start typing or just visit these URLs:

- https://docs.readthedocs.io/?rtd_search=contributing
- https://docs.readthedocs.io/?rtd_search=api/v3/projects/

.. _readthedocs-sphinx-search: https://readthedocs-sphinx-search.readthedocs.io/
