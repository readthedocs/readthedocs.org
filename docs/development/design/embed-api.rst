Embed API
=========

The Embed API allows to embed content from docs pages in other sites.
For a while it has been as an *experimental* feature without public documentation or real applications,
but recently it has been used widely (mainly because we created a Sphinx extension).

This improvement is part of the `CZI grant`_.
Due to this we need to have more friendly to use API,
and general and stable enough to support it for a long time and with external sites.

.. _CZI grant: https://blog.readthedocs.com/czi-grant-announcement/

.. contents::
   :local:
   :depth: 3

Current implementation
----------------------

The current implementation of the API is partially documented in :doc:`/guides/embedding-content`.
Some characteristics/problems are:

- There are three ways of querying the API, and some rely on Sphinx's concepts like ``doc``.
- Doesn't support MkDocs.
- It returns all sections from the current page on every request.
- Lookups are slow (~500 ms).
- IDs returned aren't well formed (like empty IDs `#`).
- The content is always an array of one element.
- The section can be an identifier or any other four variants or the title of the section.
- It doesn't return valid HTML for definition lists (``dd`` tags without a ``dt`` tag).
- The client doesn't know if the page requires extra JS or CSS in order to make it work or look nice.
- It doesn't support external sites.

New API
-------

The API would be split into two endpoints, and only have one way of querying the API.

Get page
--------

Allow us to query information about a page, like its list of sections and extra js/css scripts.

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

Implemention
------------

If a section or page doesn't exist, we return 404.
  This guarantees that the client requesting this resource has a way of knowing the response is correct.

All links are re-written to be absolute.
  Allow the content to be located in any page and in external sites
  (this is already done).

All sections listed are from html tags that are linkeable.
  This is, they have an ``id``
  (we don't rely on the toctree from the fjson file anymore).
  This way is more easy to parse and get the wanted section,
  instead of restricting to some types of contents.

The IDs returned don't contain the redundant ``#`` symbol.
  The fragment part could be used in external tools.

The content is an string with a well formed HTML block.
  Malformed HTML can cause the content to be rendered in unexpected ways.
  Some HTML tags are required to be be inside other tags or be surrounded by other tags,
  examples are ``li`` tags inside ``ul`` or ``dd`` tags inside ``dl`` and having a ``dt`` tag.

  For example extracting the ``title`` section from this snipped:

  .. code:: html

     <dl>
      ...

      <dt id="foo">Foo</dt>
      <dd>Some definition</dd>

      <dt id="title">Title<dt>
      <dd>Some definition</dd>

      ...
     </dl>

  Would result in

  .. code:: html

     <dl>
      <dt id="title">Title<dt>
      <dd>Some definition</dd>
     </dl>

  Instead of

  .. code:: html

     <dd>Some definition</dd>

  Note that we only try to keep the current structure,
  if the page contains malformed HTML, we don't try to *fix it*.
  This improvement can be shared with the current API (v2).

Parse the HTML page itself rather than the relying on the fjson files.
  This allow us to use the embed API in any page and tool, and outside Read the Docs.
  We can re-use code from the search parsing to detect the main content.
  This improvement can be shared with the current API (v2).

Return extra js and css that may be required to render the page correctly.
  We return a list of js and css files that are included in the page ``style`` and ``script`` tags.
  The returned js and css files aren't guaranteed to be required in order to render the content,
  but a decision for the client to make. Of course users can also anticipate the kind of content
  they want to embed and extract the correct css and js in order to make it work.
  We won't check for inline scripts.

``extras`` could be returned only on ``/pages``, or only on ``/sections``.
  It makes more sense to be only on ``/pages``,
  but them querying a section would require to query a page to get the extra js/css files.

.. note::

   We should probably make a distinction between our general API that handles Read the Docs resources,
   vs our APIs that expose features (like server side search, footer, and embed, all of them proxied).
   This way we can version each endpoint separately.

Support for external sites
--------------------------

Currently this document uses ``project``, ``version``, and ``path`` to query the API,
but since the CZI grant and intersphinx support requires this to work with external sites,
those arguments can be replaced with ``url``.

Considerations
``````````````

If a project changes its custom domain, current usage of the API would break.

We would need to check if the domain belongs to a project inside RTD and fetch the file from storage,
and if it's from an external site fetch it from the internet.

The API could be missused.
This is already true if we don't support external sites,
since we host arbitrary HTML already.
But it can be abussed to crawl external sites without the consent of the site admin.
We can integrate support for external sites in a later stage,
or have a list of allowed sites.

We would need to make our parsing code more generic.
This is already proposed in this document,
but testing is going to be done with Sphinx and MkDocs mainly.

If we want to support external site to use the API,
then we would need to expose it in a general public endpoint
instead of the proxied API.

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
