Embed API
=========

The embedded API allows to embed content from docs pages in other sites.
For a while it has been as an *experimental* feature without public documentation or real applications,
but recently it has been used widely (mainly because we created a Sphinx extension).

Due to this we need to have more friendly to use API,
and general and stable enough to support it for a long time.

.. contents::
   :local:
   :depth: 3

Current implementation
----------------------

The current implementation of the API is partially documented in :doc:`/guides/embedding-content`.
Some characteristics/problems are:

- There are three ways of querying the API, and some rely on Sphinx's concepts like ``doc``.
- Doesn't cache responses or doesn't purge the cache on build.
- Doesn't support MkDocs.
- It returns all sections from the current page.
- Lookups are slow (~500 ms).
- IDs returned aren't well formed (like empty IDs `#`).
- The content is always an array of one element.
- The section can be an identifier or any other four variants or the title of the section.
- It doesn't return valid HTML for definition lists (``dd`` tags without a ``dt`` tag).
- The client doesn't know if the page requires extra JS or CSS in order to make it work or look nice.

Improvements
------------

These improvements aren't breaking changes, so we can implement them in the old and new API.

- Support for MkDocs.
- Always return a valid/well formed HTML block.

New API
-------

The API would be split into two endpoints, and only have one way of querying the API.

Get page
--------

Allow us to query information about a page, like its list of sections.

.. http:get:: /_/api/v3/embed/pages?project=docs&version=latest&path=install.html

   :query project: (required)
   :query version: (required)
   :query path: (required)

   .. sourcecode:: json

      {
         "project": "docs",
         "version": "latest",
         "path": "install.html",
         "title": "Installation Guide",
         "url": "https://docs.readthedocs.io/en/latest/install.html",
         "sections": [
            {
               "title": "Installation",
               "id": "installation"
            },
            {
               "title": "Examples",
               "id": "examples"
            }
         ],
         "extras": {
            "js": ["https://docs.readthedocs.io/en/latest/index.js"],
            "css": ["https://docs.readthedocs.io/en/latest/index.css"],
         }
      }

Get section
-----------

Allow us to query the content of the section, with all links re-written as absolute.

.. http:get:: /_/api/v3/embed/sections?project=docs&version=latest&path=install.html#examples

   :query project: (required)
   :query version: (required)
   :query path: Path with or without fragment (required)

   .. sourcecode:: json

      {
         "project": "docs",
         "version": "latest",
         "path": "install.html",
         "url": "https://docs.readthedocs.io/en/latest/install.html#examples",
         "id": "examples",
         "title": "Examples",
         "content": "<div>I'm a html block!<div>",
         "extras": {
            "js": ["https://docs.readthedocs.io/en/latest/index.js"],
            "css": ["https://docs.readthedocs.io/en/latest/index.css"],
         }
      }

Notes
-----

- If a section or page doesn't exist, we return 404.
- All links are re-written to be absolute (this is already done).
- All sections listed are from html tags that are linkeable, this is, they have an ``id``
  (we don't rely on the toctree from the fjson file anymore).
- The IDs returned don't contain the redundant ``#`` symbol.
- The content is an string with a well formed HTML block.
- We could also support only ``url`` as argument for ``/sections`` and ``/pages``,
  but this introduces another way of querying the API.
  Having two ways of querying the API makes it *less-cacheable*.
- Returning the extra js and css requires parsing the HTML page itself,
  rather than only the content extracted from the fjson files (this is for sphinx).
  We can use both, the html file and the json file, but we could also just start parsing the full html page
  (we can re-use code from the search parsing to detect the main content).
- ``extras`` could be returned only on ``/pages``, or only on ``/sections``.
  It makes more sense to be only on ``/pages``,
  but them querying a section would require to query a page to get the extra js/css files.
- We could not return the ``title`` of the page/section as it would require more parsing to do
  (but we can re-use the code from search).
  Titles can be useful to build an UI like https://readthedocs.org/projects/docs/tools/embed/.
- MkDocs support can be added easily as we make our parsing code more general.

.. note::

   We should probably make a distinction between our general API that handles Read the Docs resources,
   vs our APIs that expose features (like server side search, footer, and embed, all of them proxied).
   This way we can version each endpoint separately.

Deprecation
-----------

We should have a section in our docs instead of guide where the embed API is documented.
There we can list v2 as deprecated.
We would need to migrate our extension as well.
Most of the parsing code could be shared between the two APIs, so it shouldn't be a burden to maintain.

API Client
----------

Do we really need a JS client?
The API client is a js script to allow users to use our API in any page.
Using the fetch and DOM API should be easy enough to make this work.
Having a guide on how to use it would be better than having to maintain and publish a JS package.

Most users would use the embed API in their docs in form of an extension (like sphinx-hoverxref).
Users using the API in other pages would probably have the sufficient knowledge to use the fetch and DOM API.
