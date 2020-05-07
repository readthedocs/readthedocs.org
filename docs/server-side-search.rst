Server Side Search
==================

Read the Docs provides full-text search across all of the pages of all projects,
this is powered by Elasticsearch_.
You can search all projects at https://readthedocs.org/search/,
or search only on your project from the :guilabel:`Search` tab of your project.

We also override the default search engine of your project with our search engine
to provide you better results within your project.

.. note::

   Currently, we override the default search engine for Sphinx projects only.
   Mkdocs support will be coming soon!

Improvements
------------

Some of the improvements from our search engine are:

- Search results include the section where the results come from.
- Results from :doc:`/subprojects` will be show when searching on the parent project.
- Special query syntax for more specific results.
  Like surrounding a term with `"` to have exact matches,
  see some examples at :ref:`guides/searching-with-readthedocs:search query syntax`.

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
