Searching with Read the Docs
============================

Read the Docs uses Elasticsearch to provide a better search experience.
This guide is intended to show that how to add "search as you type" feature to your documentation,
how to use advanced query syntax to get more accurate results and
many other search features that Read the Docs supports with example searches.

You can find information on the search architecture and how we index document on our
:doc:`Search <../development/search>` docs.


.. contents:: Table of contents
   :local:
   :backlinks: none
   :depth: 3


Improvements over Sphinx search
-------------------------------

Sphinx is designed to create a self-contained webpage and
all search indexing is done when the documentation is built.
As a result, it would be impossible for Sphinx to add features like searching translations
or subprojects or having analytics on common searches.
Read the Docs supports a powerful documentation search unlike
Sphinx which only have a basic search support.

Features of Read the Docs documentation search are:

- Search as you type feature supported.
- Search analytics.
- Search across multiple projects.
- Search inside subprojects.
- Advanced query syntax.
- Improved search result order.
- Public search API (documentation pending).
- Case insensitive search.
- Results from sections of the documentation.
- Code search.


Search features for project admins
----------------------------------

Enable "search as you type" in your documentation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

`readthedocs-sphinx-search`_ is a Sphinx extension which integrates your
documentation more closely with Read the Docs' search implementation.
It adds a clean and minimal full page search UI which supports **search as you type** feature.

To get a glimpse of it, you can press :guilabel:`/` (forward slash) and start typing
or just visit these URLs:

- https://docs.readthedocs.io/?rtd_search=contributing
- https://docs.readthedocs.io/?rtd_search=api/v3/projects/


Search analytics
~~~~~~~~~~~~~~~~

Search queries are recorded and are stored in database to provide valuable analytics to the project admins.
These analytics makes it easy to know what your users are looking for in your documentation.
You can see these analytics in your project admin dashboard.

.. note::

    Currently, this feature is in beta state and is available under a
    :ref:`feature flag <guides/feature-flags:Available Flags>`.
    We plan to make this available for everyone soon.
    If you want to test this feature out and help giving us feedback,
    please contact us via `GitHub issues`_.

.. figure:: /_static/images/guides/search-analytics-demo.png
    :width: 40%
    :align: center
    :alt: Search analytics in project admin dashboard

    Search analytics demo


Search features for readers
---------------------------

Search across all projects
~~~~~~~~~~~~~~~~~~~~~~~~~~

Our `main site search`_ supports searching for projects and
searching across all projects.
You can also use it to select the specific project and version to narrow down the search results.

Example queries:

- https://readthedocs.org/search/?q=celery&type=project
- https://readthedocs.org/search/?q=celery._state&type=file
- https://readthedocs.org/search/?q=celery._state&type=file&project=celery
- https://readthedocs.org/search/?q=celery._state&type=file&project=celery&version=master


Search inside subprojects
~~~~~~~~~~~~~~~~~~~~~~~~~

We allow projects to configured as subprojects of another project.
You can read more about this in our :doc:`Subprojects <../subprojects>` documentation.

If a search is made in a project which have one or more subprojects under it,
the search results then also includes the results from subprojects because
they share a search index with their parent and sibling projects.
For example: `Kombu`_ is one of the subprojects of `Celery`_,
so if you search in Celery docs, then the results from Kombu will also be there.
Example: https://docs.celeryproject.org/en/master/search.html?q=utilities&check_keywords=yes&area=default


Search query syntax
~~~~~~~~~~~~~~~~~~~

Read the Docs uses `Simple Query String`_ feature of `Elasticsearch`_,
hence the search query can be made complex to get more accurate results.

Exact phrase search
+++++++++++++++++++

If a query is wrapped in ``"``,
then only those results where the phrase is exactly matched will be returned.

Example queries:

- https://docs.readthedocs.io/?rtd_search=%22custom%20css%22
- https://docs.readthedocs.io/?rtd_search=%22adding%20a%20subproject%22
- https://docs.readthedocs.io/?rtd_search=%22when%20a%20404%20is%20returned%22

Exact phrase search with slop value
+++++++++++++++++++++++++++++++++++

``~N`` after a phrase signifies slop amount.
It can be used to match words which are near one another.

Example queries:

- https://docs.readthedocs.io/?rtd_search=%22dashboard%20admin%22~2
- https://docs.readthedocs.io/?rtd_search=%22single%20documentation%22~1
- https://docs.readthedocs.io/?rtd_search=%22read%20the%20docs%20story%22~5

Prefix query
++++++++++++

``*`` at the end of any term signifies a prefix query.
It returns the results containg the words with specific prefix.

Example queries:

- https://docs.readthedocs.io/?rtd_search=API%20v*
- https://docs.readthedocs.io/?rtd_search=single%20v*%20doc*
- https://docs.readthedocs.io/?rtd_search=build*%20and%20c*%20to%20doc*

Fuzzy query
+++++++++++

``~N`` after a word signifies edit distance (fuzziness).
This type of query is helpful when spelling of the actual keyword is unsure.
It returns results that contain terms similar to the search term,
as measured by a `Levenshtein edit distance`_.

Example queries:

- https://docs.readthedocs.io/?rtd_search=reedthedcs~2
- https://docs.readthedocs.io/?rtd_search=authentation~3
- https://docs.readthedocs.io/?rtd_search=configurtion~1


Using the search query syntax to build complex queries
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The search query syntaxes described in the previous section
can be used with one another to build complex queries.

Example queries:

- https://docs.readthedocs.io/?rtd_search=auto*%20redirect*
- https://docs.readthedocs.io/?rtd_search=abandon*%20proj*
- https://docs.readthedocs.io/?rtd_search=localisation~3%20of%20doc*


.. _readthedocs-sphinx-search: https://readthedocs-sphinx-search.readthedocs.io/
.. _GitHub issues: https://github.com/readthedocs/readthedocs.org/issues/new
.. _main site search: https://readthedocs.org/search/?q=&type=file&version=latest
.. _Kombu: http://docs.celeryproject.org/projects/kombu/en/master/
.. _Celery: http://docs.celeryproject.org/en/master/
.. _Simple Query String: https://www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl-simple-query-string-query.html#
.. _Elasticsearch: https://www.elastic.co/products/elasticsearch
.. _Levenshtein edit distance: https://en.wikipedia.org/wiki/Levenshtein_distance
