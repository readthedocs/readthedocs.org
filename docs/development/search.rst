Search
======

Read The Docs uses Elasticsearch_ instead of the built in Sphinx search for providing better search
results. Documents are indexed in the Elasticsearch index and the search is made through the API.
All the Search Code is open source and lives in the `GitHub Repository`_.
Currently we are using the `Elasticsearch 6.8.3`_ version.

Local Development Configuration
-------------------------------

Installing and running Elasticsearch
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
You need to install and run Elasticsearch_ version 6.8.3 on your local development machine.
You can get the installation instructions
`here <https://www.elastic.co/guide/en/elasticsearch/reference/6.8/install-elasticsearch.html>`_.
Otherwise, you can also start an Elasticsearch Docker container by running the following command::

    docker run -p 9200:9200 -p 9300:9300 \
           -e "discovery.type=single-node" \
           docker.elastic.co/elasticsearch/elasticsearch:6.8.3

Indexing into Elasticsearch
^^^^^^^^^^^^^^^^^^^^^^^^^^^
For using search, you need to index data to the Elasticsearch Index. Run ``reindex_elasticsearch``
management command::

    ./manage.py reindex_elasticsearch

For performance optimization, we implemented our own version of management command rather than
the built in management command provided by the `django-elasticsearch-dsl`_ package.

Auto Indexing
^^^^^^^^^^^^^
By default, Auto Indexing is turned off in development mode. To turn it on, change the
``ELASTICSEARCH_DSL_AUTOSYNC`` settings to `True` in the `readthedocs/settings/dev.py` file.
After that, whenever a documentation successfully builds, or project gets added,
the search index will update automatically.

Architecture
------------
The search architecture is divided into 2 parts.

* One part is responsible for **indexing** the documents and projects (``documents.py``)
* The other part is responsible for **querying** the Index to show the proper results to users (``faceted_search.py``)

We use the `django-elasticsearch-dsl`_ package for our Document abstraction.
`django-elasticsearch-dsl`_ is a wrapper around `elasticsearch-dsl`_ for easy configuration
with Django.

Indexing
^^^^^^^^
All the Sphinx documents are indexed into Elasticsearch after the build is successful.
Currently, we do not index MkDocs documents to elasticsearch, but
`any kind of help is welcome <https://github.com/readthedocs/readthedocs.org/issues/1088>`_.

How we index documentations
~~~~~~~~~~~~~~~~~~~~~~~~~~~

After any build is successfully finished, `HTMLFile` objects are created for each of the
``HTML`` files and the old version's `HTMLFile` object is deleted. By default,
`django-elasticsearch-dsl`_ package listens to the `post_create`/`post_delete` signals
to index/delete documents, but it has performance drawbacks as it send HTTP request whenever
any `HTMLFile` objects is created or deleted. To optimize the performance, `bulk_post_create`
and `bulk_post_delete` signals_ are dispatched with list of `HTMLFIle` objects so its possible
to bulk index documents in elasticsearch ( `bulk_post_create` signal is dispatched for created
and `bulk_post_delete` is dispatched for deleted objects). Both of the signals are dispatched
with the list of the instances of `HTMLFile` in `instance_list` parameter.

We listen to the `bulk_post_create` and `bulk_post_delete` signals in our `Search` application
and index/delete the documentation content from the `HTMLFile` instances.


How we index projects
~~~~~~~~~~~~~~~~~~~~~

We also index project information in our search index so that the user can search for projects
from the main site. We listen to the `post_create` and `post_delete` signals of
`Project` model and index/delete into Elasticsearch accordingly.


Elasticsearch Document
~~~~~~~~~~~~~~~~~~~~~~

`elasticsearch-dsl`_ provides a model-like wrapper for `the Elasticsearch document`_.
As per requirements of `django-elasticsearch-dsl`_, it is stored in the
`readthedocs/search/documents.py` file.

    **ProjectDocument:** It is used for indexing projects. Signal listener of
    `django-elasticsearch-dsl`_ listens to the `post_save` signal of `Project` model and
    then index/delete into Elasticsearch.

    **PageDocument**: It is used for indexing documentation of projects. 
    As mentioned above, our `Search` app listens to the `bulk_post_create` and `bulk_post_delete`
    signals and indexes/deleted documentation into Elasticsearch. The signal listeners are in
    the `readthedocs/search/signals.py` file. Both of the signals are dispatched
    after a successful documentation build.

    The fields and ES Datatypes are specified in the `PageDocument`. The indexable data is taken
    from `processed_json` property of `HTMLFile`. This property provides python dictionary with
    document data like `title`, `sections`, `path` etc.


.. _Elasticsearch: https://www.elastic.co/products/elasticsearch
.. _Elasticsearch 6.8.3: https://www.elastic.co/guide/en/elasticsearch/reference/6.8/index.html
.. _GitHub Repository: https://github.com/readthedocs/readthedocs.org/tree/master/readthedocs/search
.. _the Elasticsearch document: https://www.elastic.co/guide/en/elasticsearch/guide/current/document.html
.. _django-elasticsearch-dsl: https://github.com/sabricot/django-elasticsearch-dsl
.. _elasticsearch-dsl: http://elasticsearch-dsl.readthedocs.io/en/latest/
.. _signals: https://docs.djangoproject.com/en/2.1/topics/signals/
