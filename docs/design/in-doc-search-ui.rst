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
            "type": "text"
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
      "title"
    ],
    "query": {
      "bool": {
        "must": {
          "multi_match": {
            "query": "this part of do",
            "fields": [
              "content.autocomplete"
            ],
            "type": "best_fields",
            "fuzziness": "AUTO"
          }
        },
        "filter": {
          "bool": {
            "must": [
              { "term": { "project": "requests-test" } },
              { "term": { "version": "latest" } }
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
        "content.autocomplete": {}
      }
    }
  }


Result
~~~~~~

.. code::

  {
    "took" : 131,
    "timed_out" : false,
    "_shards" : {
      "total" : 5,
      "successful" : 5,
      "skipped" : 0,
      "failed" : 0
    },
    "hits" : {
      "total" : 29,
      "max_score" : 9.276031,
      "hits" : [
        {
          "_index" : "test-edge-ngram",
          "_type" : "doc",
          "_id" : "574",
          "_score" : 9.276031,
          "_source" : {
            "title" : "http.cookiejar"
          },
          "highlight" : {
            "content.autocomplete" : [
              """to a <em class="hlt1">thi</em><em class="hlt1">r</em>d-<em class="hlt1">par</em><em class="hlt1">t</em><em class="hlt1">y</em> host if its request- host U <em class="hlt1">do</em>es not <em class="hlt1">do</em>main-match the reach R <em class="hlt1">of</em> the request-host O"""
            ]
          }
        },
        {
          "_index" : "test-edge-ngram",
          "_type" : "doc",
          "_id" : "578",
          "_score" : 7.7096343,
          "_source" : {
            "title" : "requests.utils"
          },
          "highlight" : {
            "content.autocomplete" : [
              """<em class="hlt1">pat</em>h, no need to <em class="hlt1">do</em> anything further return <em class="hlt1">pat</em>h # find the first valid <em class="hlt1">par</em><em class="hlt1">t</em> <em class="hlt1">of</em> the provided <em class="hlt1">pat</em>h and"""
            ]
          }
        },
        {
          "_index" : "test-edge-ngram",
          "_type" : "doc",
          "_id" : "548",
          "_score" : 6.7345414,
          "_source" : {
            "title" : "Advanced Usage"
          },
          "highlight" : {
            "content.autocomplete" : [
              """<em class="hlt1">Par</em><em class="hlt1">t</em> <em class="hlt1">of</em> the reason <em class="hlt1">thi</em><em class="hlt1">s</em> was <em class="hlt1">do</em>ne was to implement Transport Adapters, originally described here."""
            ]
          }
        },
        {
          "_index" : "test-edge-ngram",
          "_type" : "doc",
          "_id" : "509",
          "_score" : 6.1174235,
          "_source" : {
            "title" : "Requests: HTTP for Humans™"
          },
          "highlight" : {
            "content.autocomplete" : [
              """
  Authentication
  The Community Guide
  <em class="hlt1">Thi</em><em class="hlt1">s</em> <em class="hlt1">par</em><em class="hlt1">t</em> <em class="hlt1">of</em> the <em class="hlt1">do</em>cumentation, which is mostly prose, details the
  """
            ]
          }
        },
        {
          "_index" : "test-edge-ngram",
          "_type" : "doc",
          "_id" : "582",
          "_score" : 6.084148,
          "_source" : {
            "title" : "requests.models"
          },
          "highlight" : {
            "content.autocomplete" : [
              """:<em class="hlt1">par</em><em class="hlt1">a</em>m cookies: dictionary or CookieJar <em class="hlt1">of</em> cookies to attach to <em class="hlt1">thi</em><em class="hlt1">s</em> request."""
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
