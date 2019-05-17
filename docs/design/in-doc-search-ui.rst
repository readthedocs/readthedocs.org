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
            "query": "this part of docu",
            "fields": [
              "content.autocomplete"
            ],
            "type": "best_fields"
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
    "took" : 28,
    "timed_out" : false,
    "_shards" : {
      "total" : 5,
      "successful" : 5,
      "skipped" : 0,
      "failed" : 0
    },
    "hits" : {
      "total" : 29,
      "max_score" : 2.935819,
      "hits" : [
        {
          "_index" : "test-edge-ngram",
          "_type" : "doc",
          "_id" : "591",
          "_score" : 2.935819,
          "_source" : {
            "title" : "Frequently Asked Questions"
          },
          "highlight" : {
            "content.autocomplete" : [
              """
  Frequently Asked Questions
  <em class="hlt1">This</em> <em class="hlt1">part</em> <em class="hlt1">of</em> the <em class="hlt1">docu</em>mentation answers common questions about Requests.
  """
            ]
          }
        },
        {
          "_index" : "test-edge-ngram",
          "_type" : "doc",
          "_id" : "509",
          "_score" : 2.7667096,
          "_source" : {
            "title" : "Requests: HTTP for Humans™"
          },
          "highlight" : {
            "content.autocomplete" : [
              """<em class="hlt1">part</em> <em class="hlt1">of</em> the <em class="hlt1">docu</em>mentation is for you."""
            ]
          }
        },
        {
          "_index" : "test-edge-ngram",
          "_type" : "doc",
          "_id" : "546",
          "_score" : 2.4082716,
          "_source" : {
            "title" : "Installation of Requests"
          },
          "highlight" : {
            "content.autocomplete" : [
              """
  Installation <em class="hlt1">of</em> Requests
  <em class="hlt1">This</em> <em class="hlt1">part</em> <em class="hlt1">of</em> the <em class="hlt1">docu</em>mentation covers the installation <em class="hlt1">of</em> Requests.
  """
            ]
          }
        },
        {
          "_index" : "test-edge-ngram",
          "_type" : "doc",
          "_id" : "548",
          "_score" : 2.0368419,
          "_source" : {
            "title" : "Advanced Usage"
          },
          "highlight" : {
            "content.autocomplete" : [
              """
  Advanced Usage
  <em class="hlt1">This</em> <em class="hlt1">docu</em>ment covers some <em class="hlt1">of</em> Requests more advanced features.
  """
            ]
          }
        },
        {
          "_index" : "test-edge-ngram",
          "_type" : "doc",
          "_id" : "578",
          "_score" : 1.9563103,
          "_source" : {
            "title" : "requests.utils"
          },
          "highlight" : {
            "content.autocomplete" : [
              """[i] = c + <em class="hlt1">part</em>s[i][2:] else: <em class="hlt1">part</em>s[i] = '%' + <em class="hlt1">part</em>s[i] else: <em class="hlt1">part</em>s[i] = '%' + <em class="hlt1">part</em>s[i] return ''.join"""
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
