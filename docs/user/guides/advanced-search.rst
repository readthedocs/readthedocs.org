Using advanced search features
==============================

Read the Docs uses :doc:`/server-side-search` to power our search.
This guide explains how to add a "search as you type" feature to your documentation,
and how to use advanced query syntax to get more accurate results.

You can find information on the search architecture and how we index documents in our
:doc:`Search </development/search>` docs.

.. contents:: Table of contents
   :local:
   :backlinks: none
   :depth: 3

Enable "search as you type" in your documentation
-------------------------------------------------

`readthedocs-sphinx-search`_ is a Sphinx extension that integrates your
documentation more closely with the search implementation of Read the Docs.
It adds a clean and minimal full-page search UI that supports a **search as you type** feature.

To try this feature,
you can press :guilabel:`/` (forward slash) and start typing or just visit these URLs:

- https://docs.readthedocs.io/?rtd_search=contributing
- https://docs.readthedocs.io/?rtd_search=api/v3/projects/

Search query syntax
-------------------

Read the Docs uses the `Simple Query String`_ feature from `Elasticsearch`_.
This means that as the search query becomes more complex,
the results yielded become more specific.

Exact phrase search
~~~~~~~~~~~~~~~~~~~

If a query is wrapped in ``"`` (double quotes),
then only those results where the phrase is exactly matched will be returned.

Example queries:

- https://docs.readthedocs.io/?rtd_search=%22custom%20css%22
- https://docs.readthedocs.io/?rtd_search=%22adding%20a%20subproject%22
- https://docs.readthedocs.io/?rtd_search=%22when%20a%20404%20is%20returned%22

Exact phrase search with slop value
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``~N`` (tilde N) after a phrase signifies slop amount.
It can be used to match words that are near one another.

Example queries:

- https://docs.readthedocs.io/?rtd_search=%22dashboard%20admin%22~2
- https://docs.readthedocs.io/?rtd_search=%22single%20documentation%22~1
- https://docs.readthedocs.io/?rtd_search=%22read%20the%20docs%20story%22~5

Prefix query
~~~~~~~~~~~~

``*`` (asterisk) at the end of any term signifies a prefix query.
It returns the results containing the words with specific prefix.

Example queries:

- https://docs.readthedocs.io/?rtd_search=API%20v*
- https://docs.readthedocs.io/?rtd_search=single%20v*%20doc*
- https://docs.readthedocs.io/?rtd_search=build*%20and%20c*%20to%20doc*

Fuzzy query
~~~~~~~~~~~

``~N`` after a word signifies edit distance (fuzziness).
This type of query is helpful when the exact spelling of the keyword is unknown.
It returns results that contain terms similar to the search term as measured by a `Levenshtein edit distance`_.

Example queries:

- https://docs.readthedocs.io/?rtd_search=reedthedcs~2
- https://docs.readthedocs.io/?rtd_search=authentation~3
- https://docs.readthedocs.io/?rtd_search=configurtion~1


Build complex queries
~~~~~~~~~~~~~~~~~~~~~

The search query syntaxes described in the previous sections can be used with one another to build complex queries.

For example:

- https://docs.readthedocs.io/?rtd_search=auto*%20redirect*
- https://docs.readthedocs.io/?rtd_search=abandon*%20proj*
- https://docs.readthedocs.io/?rtd_search=localisation~3%20of%20doc*

.. _Elasticsearch: https://www.elastic.co/products/elasticsearch
.. _readthedocs-sphinx-search: https://readthedocs-sphinx-search.readthedocs.io/
.. _Simple Query String: https://www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl-simple-query-string-query.html#
.. _Levenshtein edit distance: https://en.wikipedia.org/wiki/Levenshtein_distance
