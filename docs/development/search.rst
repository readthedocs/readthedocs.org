Search
============

Read The Docs uses Elasticsearch_ instead of the built in Sphinx search for providing better search
results. Documents are indexed in the Elasticsearch index and the search is made through the API.
All the Search Code is open source and lives in the `Github Repository`_.
Currently we are using the `Elasticsearch 6.3`_ version.

Local Development Configuration
-------------------------------

Installing and running Elasticsearch
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
You need to install and run the `Elasticsearch 6.3`_ version on your local development machine.
You can get the installation instructions
`here <https://www.elastic.co/guide/en/elasticsearch/reference/6.3/install-elasticsearch.html>`_.
Otherwise, you can also start a Elasticsearch Docker container by running the following command::

    docker run -p 9200:9200 -p 9300:9300 \
           -e "discovery.type=single-node" \
           docker.elastic.co/elasticsearch/elasticsearch:6.3.2

Indexing into Elasticsearch
^^^^^^^^^^^^^^^^^^^^^^^^^^^
For using search, you need to index data to Elasticsearch Index. Run `reindex_elasticsearch`
management command::

    ./manage.py reindex_elasticsearch

Auto Indexing
^^^^^^^^^^^^^
By default, Auto Indexing is turned off in development mode. To turn it on, change the
`ELASTICSEARCH_DSL_AUTOSYNC` settings to `True` in `readthedocs/settings/dev.py` file.
After that, whenever a documentation successfully builds, or project gets added,
the search index will update automatically.


Architecture
------------
The search architecture is devided into 2 parts.
One part is responsible for **indexing** the documents and projects and
other part is responsible to query through the Index for showing proper results to users.
We use `django-elasticsearch-dsl`_ package mostly to the keep the search working.
`django-elasticsearch-dsl`_ is a wrapper around `elasticsearch-dsl`_ for easy configuration
with Django.

Indexing
^^^^^^^^
All the Sphinx documents are indexed into elasticsearch after the build is successful.
Currently, we do not index MkDocs documents to elasticsearch, but
`any kind of help is welcome <https://github.com/rtfd/readthedocs.org/issues/1088>`_.

How we index documentations
~~~~~~~~~~~~~~~~~~~~~~~~~~~

After any build gets successfully finished, `HTMLFile` objects are created for each of the
`HTML` files and the old version's `HTMLFile` object is deleted. Signal_
`bulk_post_create` is dispatched for created and `bulk_post_delete` is dispatched for deleted
files. Both of the signals are dispatched with the list of the instances of `HTMLFile`
in `instance_list` parameter.

We listen to the `bulk_post_create` and `bulk_post_delete` signals in our `Search` application and
index/delete the documentation content from the `HTMLFile` instances.


How we index projects
~~~~~~~~~~~~~~~~~~~~~
We also index project information in our search index so that the user can search for projects
from the main site. `django-elasticsearch-dsl`_ listen `post_create` and `post_delete` signals of
`Project` model and index/delte into Elasticsearch accordingly.


Elasticsearch Document
~~~~~~~~~~~~~~~~~~~~~~

`elasticsearch-dsl`_ provides model like wrapper for the `Elasticsearch document`_.
As per requirements of `django-elasticsearch-dsl`_, it is stored in
`readthedocs/search/documents.py` file.

    **ProjectDocument:** It is used for indexing projects. Signal listener of
    `django-elasticsearch-dsl`_ listen the `post_save` singal of `Project` model and
    then index/delete into Elasticsearch.

    **PageDocument**: It is used for indexing documentation of projects. By default, the auto
    indexing is turned off by `ignore_signals = settings.ES_PAGE_IGNORE_SIGNALS`.
    `settings.ES_PAGE_IGNORE_SIGNALS` is `False` both in development and production.
    As mentioned above, our `Search` app listens to the `bulk_post_create` and `bulk_post_delete`
    signals and index/delete documentations into Elasticsearch. The signal listeners are in
    the `readthedocs/search/signals.py` file. Both of the signals are dispatched
    after a successful documentation build.


.. _Elasticsearch: https://www.elastic.co/products/elasticsearch
.. _Elasticsearch 6.3: https://www.elastic.co/guide/en/elasticsearch/reference/6.3/index.html
.. _Github Repository: https://github.com/rtfd/readthedocs.org/tree/master/readthedocs/search
.. _Elasticsearch document: https://www.elastic.co/guide/en/elasticsearch/guide/current/document.html
.. _django-elasticsearch-dsl: https://github.com/sabricot/django-elasticsearch-dsl
.. _elasticsearch-dsl: http://elasticsearch-dsl.readthedocs.io/en/latest/
.. _Signal: https://docs.djangoproject.com/en/2.1/topics/signals/
