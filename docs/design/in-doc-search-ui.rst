In Doc Search UI
================

Giving the user the ability to easily search the information
that they are looking for is important for us.
We have already upgraded to the latest version of `Elasticsearch`_ and
we plan to implement `search as you type` feature for all the documentations hosted by us.
It will be designed to provide instant results as soon as the user starts
typing in the search bar with a clean and minimal frontend.
This design document aims to provides the details of it.
This is a GSoC'19 project.
The final result may look something like this:

.. figure:: ../_static/images/in-doc-search-ui/in-doc-search-ui-demo.gif
    :align: center
    :target: ../_static/images/in-doc-search-ui/in-doc-search-ui-demo.gif

    Short demo


Goals And Non-Goals
-------------------

Project Goals
++++++++++++++

* Support a search-as-you-type/autocomplete interface.
* Support across all (or virtually all) Sphinx themes.
* Support for the JavaScript user experience down to IE11 or graceful degradation where we can't support it.
* Project maintainers should have a way to opt-in/opt-out of this feature.
* (Optional) They should have the flexibility to change some of the styles using custom CSS and JS files.

Non-Goals
++++++++++

* For the initial release, we are targeting only Sphinx documentations
  as we don't index MkDocs documentations to our Elasticsearch index.


Existing Search Implementation
------------------------------

We have a detailed documentation explaing the underlying architecture of our search backend
and how we index documents to our Elasticsearch index.
You can read about it :doc:`here <../development/search>`.


Proposed Architecture for In-Doc Search UI
------------------------------------------

Frontend
++++++++

Technologies
~~~~~~~~~~~~

Frontend is to designed in a theme agnostics way. For that,
we explored various libraries which may be of use but none of them fits our needs.
So, we might be using vanilla JavaScript for this purpose.
This will provide us some advantages over using any third party library:

* Better control over the DOM.
* Performance benefits.


Proposed Architecture
~~~~~~~~~~~~~~~~~~~~~

We plan to select the search bar, which is present in every documentation,
using the `querySelector()`_ method of JavaScript.
Then add an event listener to it to listen for the changes and
fire a search query to our backend as soon as there is any change.
Our backend will then return the suggestions,
which will be shown to the user in a clean and minimal UI.
We will be using `document.createElement()`_ and `node.removeChild()`_ method
provided by JavaScript as we don't want empty `<div>` hanging out in the DOM.

We have a few ways to include the required JavaScript and CSS files in all the projects:

* Add CSS into `readthedocs-doc-embed.css` and JS into `readthedocs-doc-embed.js`
  and it will get included.
* Package the in-doc search into it's own self-contained CSS and JS files
  and include them in a similar manner to `readthedocs-doc-embed.*`.
* It might be possible to package up the in-doc CSS/JS as a sphinx extension.
  This might be nice because then it's easy to enable it on a per-project basis.
  When we are ready to roll it out to a wider audience,
  we can make a decision to just turn it on for everybody (put it in `here`_)
  or we could enable it as an opt-in feature like the `404 extension`_.


UI/UX
~~~~~

We have two ways which can be used to show suggestions to the user.

* Show suggestions below the search bar.
* Open a full page search interface when the user click on search field.


Backend
+++++++

We have a few options to support `search as you type` feature,
but we need to decide that which option would be best for our use-case.

Edge NGram Tokenizer
~~~~~~~~~~~~~~~~~~~~

* Pros

  * More effective than Completion Suggester when it comes to autocompleting
    words that can appear in any order.
  * It is considerable fast because most of the work is being done at index time,
    hence the time taken for autocompletion is reduced.
  * Supports highlighting of the matching terms.

* Cons

  * Requires greater disk space.


Completion Suggester
~~~~~~~~~~~~~~~~~~~~

* Pros

  * Really fast as it is optimized for speed.
  * Does not require large disk space.

* Cons

  * Matching always starts at the beginning of the text. So, for example,
    "Hel" will match "Hello, World" but not "World Hello".
  * Highlighting of the matching words is not supported.
  * According to the official docs for Completion Suggester,
    fast lookups are costly to build and are stored in-memory.


Milestones
----------

+-----------------------------------------------------------------------------------+------------------+
| Milestone                                                                         | Due Date         |
+===================================================================================+==================+
| A local implementation of the project.                                            | 12th June, 2019  |
+-----------------------------------------------------------------------------------+------------------+
| In-doc search on a test project hosted on Read the Docs using the RTD Search API. | 20th June, 2019  |
+-----------------------------------------------------------------------------------+------------------+
| In-doc search on docs.readthedocs.io.                                             | 20th June, 2019  |
+-----------------------------------------------------------------------------------+------------------+
| Friendly user trial where users can add this on their own docs.                   | 5th July, 2019   |
+-----------------------------------------------------------------------------------+------------------+
| Additional UX testing on the top-10 Sphinx themes.                                | 15th July, 2019  |
+-----------------------------------------------------------------------------------+------------------+
| Finalize the UI.                                                                  | 25th July, 2019  |
+-----------------------------------------------------------------------------------+------------------+
| Improve the search backend for efficient and fast search results.                 | 10th August, 2019|
+-----------------------------------------------------------------------------------+------------------+


Open Questions
++++++++++++++

* Should we rely on jQuery, any third party library or pure vanilla JavaScript?
* Are the subprojects to be searched?
* Is our existing Search API is sufficient?
* Should we go for edge ngrams or completion suggester?


.. _Elasticsearch: https://www.elastic.co/products/elasticsearch
.. _querySelector(): https://developer.mozilla.org/en-US/docs/Web/API/Document/querySelector
.. _document.createElement(): https://developer.mozilla.org/en-US/docs/Web/API/Document/createElement
.. _node.removeChild(): https://developer.mozilla.org/en-US/docs/Web/API/Node/removeChild
.. _here: https://github.com/rtfd/readthedocs.org/blob/9ca5858e859dea0759d913e8db70a623d62d6a16/readthedocs/doc_builder/templates/doc_builder/conf.py.tmpl#L135-L142
.. _404 extension : https://github.com/rtfd/sphinx-notfound-page
