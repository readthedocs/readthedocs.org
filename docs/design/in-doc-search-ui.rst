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

.. code::

  PUT test-edge-ngram
  {
    "settings": {
      "analysis": {
        "analyzer": {
          "autocomplete": {
            "tokenizer": "autocomplete",
            "filter": [
              "lowercase"
            ]
          },
          "autocomplete_search": {
            "tokenizer": "lowercase"
          }
        },
        "tokenizer": {
          "autocomplete": {
            "type": "edge_ngram",
            "min_gram": 1,
            "max_gram": 30,
            "token_chars": [
              "letter"
            ]
          }
        }
      }
    },
    "mappings": {
      "doc": {
        "properties": {
          "content": {
            "type": "text",
            "fields": {
              "autocomplete": {
                "type": "text",
                "analyzer": "autocomplete",
                "search_analyzer": "autocomplete_search"
              }
            }
          },
          "headers": {
            "type": "text"
          },
          "title": {
            "type": "text",
            "fields": {
              "autocomplete": {
                "type": "text",
                "analyzer": "autocomplete",
                "search_analyzer": "autocomplete_search"
              }
            }
          },
          "commit": {
            "type": "text"
          },
          "path": {
            "type": "text"
          },
          "project": {
            "type": "keyword"
          },
          "version": {
            "type": "keyword"
          }
        }
      }
    }
  }


Sample Query
~~~~~~~~~~~~

.. code::

  GET test-edge-ngram/_search
  {
    "size": 5,
    "_source": [
      "title",
      "path"
    ],
    "query": {
      "bool": {
        "must": {
          "multi_match": {
            "query": "this part of",
            "fields": [
              "title.autocomplete^20",
              "content.autocomplete"
            ],
            "type": "best_fields",
            "fuzziness": "AUTO"
          }
        },
        "filter": {
          "bool": {
            "must": [
              {
                "term": {
                  "project": "requests-test"
                }
              },
              {
                "term": {
                  "version": "latest"
                }
              }
            ]
          }
        }
      }
    },
    "highlight": {
      "number_of_fragments": 1,
      "tags_schema": "styled",
      "fragment_size": 50,
      "fields": {
        "title.autocomplete": {},
        "content.autocomplete": {}
      }
    }
  }


Result
~~~~~~

.. code::

  {
    "took" : 51,
    "timed_out" : false,
    "_shards" : {
      "total" : 5,
      "successful" : 5,
      "skipped" : 0,
      "failed" : 0
    },
    "hits" : {
      "total" : 29,
      "max_score" : 44.42056,
      "hits" : [
        {
          "_index" : "test-edge-ngram",
          "_type" : "doc",
          "_id" : "546",
          "_score" : 44.42056,
          "_source" : {
            "path" : "user/install",
            "title" : "Installation of Requests"
          },
          "highlight" : {
            "title.autocomplete" : [
              """Installation <em class="hlt1">of</em> Requests"""
            ],
            "content.autocomplete" : [
              """
  Installation <em class="hlt1">of</em> Requests
  <em class="hlt1">Thi</em><em class="hlt1">s</em> <em class="hlt1">par</em><em class="hlt1">t</em> <em class="hlt1">of</em> the documentation
  """
            ]
          }
        },
        {
          "_index" : "test-edge-ngram",
          "_type" : "doc",
          "_id" : "574",
          "_score" : 9.096828,
          "_source" : {
            "path" : "_modules/http/cookiejar",
            "title" : "http.cookiejar"
          },
          "highlight" : {
            "content.autocomplete" : [
              """An example <em class="hlt1">of</em> <em class="hlt1">thi</em><em class="hlt1">s</em> format is: 1994-11-24 08:49:37Z"""
            ]
          }
        },
        {
          "_index" : "test-edge-ngram",
          "_type" : "doc",
          "_id" : "578",
          "_score" : 7.5825796,
          "_source" : {
            "path" : "_modules/requests/utils",
            "title" : "requests.utils"
          },
          "highlight" : {
            "content.autocomplete" : [
              """(<em class="hlt1">pat</em>h): # <em class="hlt1">thi</em><em class="hlt1">s</em> is already a valid <em class="hlt1">pat</em>h, no need to"""
            ]
          }
        },
        {
          "_index" : "test-edge-ngram",
          "_type" : "doc",
          "_id" : "548",
          "_score" : 6.5911536,
          "_source" : {
            "path" : "user/advanced",
            "title" : "Advanced Usage"
          },
          "highlight" : {
            "content.autocomplete" : [
              """<em class="hlt1">Par</em><em class="hlt1">t</em> <em class="hlt1">of</em> the reason <em class="hlt1">thi</em><em class="hlt1">s</em> was done was to implement Transport"""
            ]
          }
        },
        {
          "_index" : "test-edge-ngram",
          "_type" : "doc",
          "_id" : "509",
          "_score" : 5.9727807,
          "_source" : {
            "path" : "index",
            "title" : "Requests: HTTP for Humans™"
          },
          "highlight" : {
            "content.autocomplete" : [
              """
  The User Guide
  <em class="hlt1">Thi</em><em class="hlt1">s</em> <em class="hlt1">par</em><em class="hlt1">t</em> <em class="hlt1">of</em> the documentation, which
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
it can be said that edge-ngrams are effective when it comes to ``search as you type`` feature.

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
  * Few results are not very good and lead to bad user experience.
  * Requires greater disk space. In development environment,
    `page_index` was of size 3.9 MB and `test-edge-ngram` index was of 9.9 MB,
    both containing the same number of documents. Size of the index depends on the
    number of fields `edge-ngram`-ed and also on the `min_gram` and `max_gram` parameters.
    Keeping everything same and setting the `max_gram` to 15 reduces the size of index
    to 9.6 MB and further reducing the `max_gram` to 5 reduces the size of index to 7.7 MB.


2. Completion Suggester
+++++++++++++++++++++++

The completion suggester considers all documents in the index,
but we want our search results to be filtered based on the project and version.
According to the official docs for `Context Suggester`_, to achieve suggestion filtering
and/or boosting, we can add context mappings while configuring a completion field.


Pros and Cons:
~~~~~~~~~~~~~~

* Pros:

  * Really fast as it is optimized for speed.
  * Does not require large disk space.

* Cons:

  * Need to modify existing mapping to implement it.
  * Matching always starts at the beginning of the text. So, for example,
    "Hel" will match "Hello, World" but not "World Hello".
  * Highlighting of the matching words is not supported.
  * According to the official docs for `Completion Suggester`_,
    fast lookups are costly to build and are stored in-memory.


.. _Completion Suggester: https://www.elastic.co/guide/en/elasticsearch/reference/current/search-suggesters-completion.html
.. _official docs: https://www.elastic.co/guide/en/elasticsearch/reference/current/analysis-edgengram-tokenizer.html
.. _multi-fields: https://www.elastic.co/guide/en/elasticsearch/reference/current/multi-fields.html
.. _Context Suggester: https://www.elastic.co/guide/en/elasticsearch/reference/current/suggester-context.html
