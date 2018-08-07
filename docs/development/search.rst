Search
============

Read The Docs uses Elasticsearch_ instead of built in Sphinx search for providing better search results. Documents are indexed in Elasticsearch index and the search is made through API. All the Search Code is Opensource and lives in `Github Repository`_. Currently we are using `Elasticsearch 6.3`_ version.

Local Development Configuration
-------------------------------

Installing and running Elasticsearch
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
You must need to install and run `Elasticsearch 6.3`_ version in your local development machine. You can get installation instruction `here <https://www.elastic.co/guide/en/elasticsearch/reference/6.3/install-elasticsearch.html>`_.
Otherwise, you can also start a Elasticsearch Docker container by running following command::

    docker run -p 9200:9200 -p 9300:9300 \
           -e "discovery.type=single-node" \
           docker.elastic.co/elasticsearch/elasticsearch:6.3.2

Indexing
^^^^^^^^
For using search, you need to index data to Elasticsearch Index. Run `reindex_elasticsearch` management command::

    ./manage.py reindex_elasticsearch

Auto Indexing
^^^^^^^^^^^^^
By default, Auto Indexing is turned off in development mode. To turn in on, change the `ELASTICSEARCH_DSL_AUTOSYNC` settings to `True` in `readthedocs/settings/dev.py` file. After that, whenever a documentation successfully build, or project gets added, the search index will update automatically.

.. _Elasticsearch: https://www.elastic.co/products/elasticsearch
.. _Elasticsearch 6.3: https://www.elastic.co/guide/en/elasticsearch/reference/6.3/index.html
.. _Github Repository: https://github.com/rtfd/readthedocs.org/tree/master/readthedocs/search
