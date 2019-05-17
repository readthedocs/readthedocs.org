In Doc Search UI
================

Search will be designed to provide instant results as soon as the user starts
typing in the search bar with a clean and minimal frontend.


Current Status of Doc Search
----------------------------

Currently we only provide basic search, i.e. user won't be able to see the results
until and unless the search form is not submitted.


Implementing The Backend
------------------------

We have a few options to support ``search as you type`` feature,
but we need to decide that which option would be best for our use-case.

1. Edge NGram Tokenizer
+++++++++++++++++++++++

According to the `official docs`_, ``edge_ngram`` tokenizer first breaks text down into words
whenever it encounters one of a list of specified characters,
then it emits N-grams of each word where the start of the N-gram is anchored to the beginning of the word.

For example: "Quick Foxes" will give the following tokens (3grams) - [ Qui, uic, ick, Fox, oxe, xes ].
Edge Ngram, will be something like NGram but only tokenize from the beginning.

For using it, we have to modify the :ref:`PageDocument <development/search:Elasticsearch Document>` mapping,
and make use of `multi-fields`_ feature of Elasticsearch.


Sample Mapping
~~~~~~~~~~~~~~

.. code:: json

  {
    "map_test" : {
      "mappings" : {
        "doc" : {
          "properties" : {
            "commit" : {
              "type" : "text",
              "fields" : {
                "keyword" : {
                  "type" : "keyword",
                  "ignore_above" : 256
                }
              }
            },
            "content" : {
              "type" : "text",
              "analyzer" : "autocomplete",
              "search_analyzer" : "autocomplete_search"
            },
            "headers" : {
              "type" : "text",
              "analyzer" : "autocomplete",
              "search_analyzer" : "autocomplete_search"
            },
            "path" : {
              "type" : "text",
              "fields" : {
                "keyword" : {
                  "type" : "keyword",
                  "ignore_above" : 256
                }
              }
            },
            "project" : {
              "type" : "text",
              "fields" : {
                "keyword" : {
                  "type" : "keyword",
                  "ignore_above" : 256
                }
              }
            },
            "title" : {
              "type" : "text",
              "analyzer" : "autocomplete",
              "search_analyzer" : "autocomplete_search"
            },
            "version" : {
              "type" : "text",
              "fields" : {
                "keyword" : {
                  "type" : "keyword",
                  "ignore_above" : 256
                }
              }
            }
          }
        }
      }
    }
  }


Sample Query
~~~~~~~~~~~~

.. code:: json

  {
    "size": 5,
    "_source": [
      "title"
    ],
    "query": {
      "bool": {
        "must": {
          "multi_match": {
            "query": "requests",
            "fields": [
              "content"
            ],
            "type": "best_fields"
          }
        },
        "filter": {
          "bool": {
            "must": [
              { "term": { "project.keyword": "requests-test" } },
              { "term": { "version.keyword": "latest" } }
            ]
          }
        }
      }
    },
    "highlight": {
      "number_of_fragments": 1,
      "tags_schema" : "styled",
      "fragment_size": 100,
      "fields": {
        "content": {}
      }
    }
  }


Result
~~~~~~

.. code::

  {
    "took" : 268,
    "timed_out" : false,
    "_shards" : {
      "total" : 5,
      "successful" : 5,
      "skipped" : 0,
      "failed" : 0
    },
    "hits" : {
      "total" : 29,
      "max_score" : 2.5039907,
      "hits" : [
        {
          "_index" : "map_test",
          "_type" : "doc",
          "_id" : "575",
          "_score" : 2.5039907,
          "_source" : {
            "title" : "requests.api"
          },
          "highlight" : {
            "content" : [
              """the <em class="hlt1">Requests</em> API."""
            ]
          }
        },
        {
          "_index" : "map_test",
          "_type" : "doc",
          "_id" : "591",
          "_score" : 2.5024748,
          "_source" : {
            "title" : "Frequently Asked Questions"
          },
          "highlight" : {
            "content" : [
              """
  Frequently Asked Questions
  This part of the documentation answers common questions about <em class="hlt1">Requests</em>.
  """
            ]
          }
        },
        {
          "_index" : "map_test",
          "_type" : "doc",
          "_id" : "590",
          "_score" : 2.4801605,
          "_source" : {
            "title" : "Support"
          },
          "highlight" : {
            "content" : [
              """
  IRC
  The official Freenode channel for <em class="hlt1">Requests</em> is #python-<em class="hlt1">requests</em>
  The core developers of <em class="hlt1">requests</em> are
  """
            ]
          }
        },
        {
          "_index" : "map_test",
          "_type" : "doc",
          "_id" : "588",
          "_score" : 2.4246087,
          "_source" : {
            "title" : "Release Process and Rules"
          },
          "highlight" : {
            "content" : [
              """The core developers of <em class="hlt1">Requests</em> are committed to providing a good user experience."""
            ]
          }
        },
        {
          "_index" : "map_test",
          "_type" : "doc",
          "_id" : "547",
          "_score" : 2.3895812,
          "_source" : {
            "title" : "Authentication"
          },
          "highlight" : {
            "content" : [
              """
  The <em class="hlt1">requests</em>-oauthlib library allows <em class="hlt1">Requests</em> users to easily make OAuth 1 authenticated <em class="hlt1">requests</em>:
  >>
  """
            ]
          }
        }
      ]
    }
  }

Conclusion
~~~~~~~~~~

After experimenting with many different sample queries,
it can be said that edge-ngrams are very effective when it comes to ``search as you type`` feature.

It comes with its own set of pros and cons which are described below:

* Pros:

  * More effective than `Completion Suggester`_ when it comes to autocompleting
    words that can appear in any order.
  * It is considerable fast because most of the work is being done at index time,
    hence the time taken for autocompletion is reduced.

* Cons:

  * Need to modify existing mapping to implement it.
  * Need to configure manually as default settings of ``edge-ngrams`` tokenizer
    are almost entirely useless.
  * Different tokenizers are to be used when indexing/reindexing and when searching,
    but it can be specified at the indexing time.


2. Completion Suggester
+++++++++++++++++++++++

.. _Completion Suggester: https://www.elastic.co/guide/en/elasticsearch/reference/current/search-suggesters-completion.html
.. _official docs: https://www.elastic.co/guide/en/elasticsearch/reference/current/analysis-edgengram-tokenizer.html
.. _multi-fields: https://www.elastic.co/guide/en/elasticsearch/reference/current/multi-fields.html
