Design of APIv3
===============

APIv3 will be designed to be easy to use and useful to perform read and write operations as the main two goals.

It will be based on Resources as APIv2 but considering the ``Project`` resource as the main one,
from where most of the endpoint will be based on it.


Problems with APIv2
-------------------


* No authentication
* It's read-only
* Not designed for slugs
* Useful APIs not exposed (only for internal usage currently)
* Error reporting is a mess
* Relationships between API resources is not obvious
* Footer API endpoint returns HTML


Proposed improves
+++++++++++++++++


Use authentication
~~~~~~~~~~~~~~~~~~

* Pros:

  * queries can be personalized depending on the user
  * allows us to perform write actions

* Cons:

  * harder to implement
  * requires a lot of time for good testing and QA


Questions:

#. Do we want make auth a requirement?
#. Should we expose some endpoints as Read Only if not authenticated?
#. How we do communicate users about deprecation if they are Anonymous? Is it enough to add a note in the docs saying that "Auth is preferred for communication"?
#. How are we going to expose the ``Token`` required for Auth when building if auth is mandatory?


Read and Write
~~~~~~~~~~~~~~

* Pros:

  * most of the actions can be performed by a script instead of by
    accessing readthedocs.org with a browser

* Cons:

  * we have to deal with authorization
  * open the door to possibilities of security holes


Questions:

#. Do we want to allow the user to perform **all the write actions**
   that are possible to do from the dashboard via the API?


Design it for slugs
~~~~~~~~~~~~~~~~~~~

* Pros:

  * knowing the slug of your project (which is presented to the user)
    you can perform all the actions or retrieve all the data

* Cons:

  * it will be a mixture between most of the endpoint using ``slug``
    and to retrieve details of a Build it will be an ``id``


Expose internal endpoints
~~~~~~~~~~~~~~~~~~~~~~~~~

There are some endpoints that we are using internally like
``/api/v2/search/``, ``/api/v2/footer/`` and
``/api/v2/sustainability/``.


* Pros:

  * allow to build custom footer
  * allow to build custom search autocomplete widget

* Cons:

  * n/a

Questions:

#. Do we want to add ``/api/v2/sustainability/`` to APIv3 or that
   should be part of the new Ad Server that we are building?


Proper status codes for error reporting
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* Pros:

  * user knows what it's happening and can take decisions about it

* Cons:

  * n/a


Relationship between API resources
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* Pros:

  * browse-able API by accessing to the default resource (Project)
  * knowing the project's slug you can perform all the actions related to it

* Cons:

  * more data is returned with all the links to the endpoints


Make footer API returns JSON
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* Pros:

  * users can build their own version menu flyout
  * cleaner than returning a HTML and injecting it

* Cons:

  * we need to adapt our theme for this


Questions:

#. Do we want an specific endpoint for the footer?
#. The flyout could be built by querying 2 or 3 of the regular
   endpoint. Would this add too much overhead to the page loading
   time?


Use cases
---------

We want to cover
++++++++++++++++


* Return all **my** projects
* Access all the resources by knowing the project's slug
* Ability to filter by fields

  * all the active versions of specific project

* Data about builds

  * latest build for project
  * latest build for a particular version of a project
  * status of a particular build

* Perform write actions like

  * add a Domain,
  * add User as mantainer,
  * import a new Project under my username,
  * set the language of the Project,
  * trigger a Build,
  * activate/deactivate a Version to be built,
  * and all the actions you can perform from the Admin tab.

* Retrieve all the information needed to create a custom version menu flyout


Considering some useful cases for the corporate site:

* Give access to a doc page (``objects.inv``, ``/design/core.html``)


We do NOT want to cover
+++++++++++++++++++++++

* Random filtering over a whole and not useful Resource

  * "All the ``stable`` versions"
  * "Builds with ``exit_code`` equal to 257"


Technical aspects that would be good to have
--------------------------------------------

* Rate limit
* ``Request-ID`` header
* `JSON minified by default`_ (maybe with ``?pretty=true``)
* `JSON schema and validation`_ with docs_


.. _JSON minified by default: https://geemus.gitbooks.io/http-api-design/content/en/responses/keep-json-minified-in-all-responses.html
.. _JSON schema and validation: https://geemus.gitbooks.io/http-api-design/content/en/responses/keep-json-minified-in-all-responses.html
.. _docs: https://geemus.gitbooks.io/http-api-design/content/en/artifacts/provide-human-readable-docs.html
