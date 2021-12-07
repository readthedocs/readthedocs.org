Embed APIv3
===========

The Embed API allows users to embed content from documentation pages in other sites.
It has been treated as an *experimental* feature without public documentation or real applications,
but recently it started to be used widely (mainly because we created the ``hoverxref`` Sphinx extension).

The main goal of this document is to design a new version of the Embed API to be more user friendly,
make it more stable over time, support embedding content from pages not hosted at Read the Docs,
and remove some quirkiness that makes it hard to maintain and difficult to use.

.. note::

   This work is part of the `CZI grant`_ that Read the Docs received.

.. _CZI grant: https://blog.readthedocs.com/czi-grant-announcement/

.. contents::
   :local:
   :depth: 2


Current implementation
----------------------

The current implementation of the API is partially documented in :doc:`/guides/embedding-content`.
It has some known problems:

* There are different ways of querying the API: ``?url=`` (generic) and ``?doc=`` (relies on Sphinx's specific concept)
* Doesn't support MkDocs
* Lookups are slow (~500 ms)
* IDs returned aren't well formed (like empty IDs ``"headers": [{"title": "#"}]``)
* The content is always an array of one element
* It tries different variations of the original ID
* It doesn't return valid HTML for definition lists (``dd`` tags without a ``dt`` tag)


Goals
-----

We plan to add new features and define a contract that works the same for all HTML.
This project has the following goals:

* Support embedding content from pages hosted outside Read the Docs
* Do not depend on Sphinx ``.fjson`` files
* Query and parse the ``.html`` file directly (from our storage or from an external request)
* Rewrite all links returned in the content to make them absolute
* Require a valid HTML ``id`` selector
* Accept only ``?url=`` request GET argument to query the endpoint
* Support ``?nwords=`` and ``?nparagraphs=`` to return chunked content
* Handle special cases for particular doctools (e.g. Sphinx requires to return the ``.parent()`` element for ``dl``)
* Make explicit the client is asking to handle the special cases (e.g. send ``?doctool=sphinx&version=4.0.1&writer=html4``)
* Delete HTML tags from the original document (for well-defined special cases)
* Add HTTP cache headers to cache responses
* Allow :abbr:`CORS` from everywhere *only* for public projects


The contract
------------

Return the HTML tag (and its children) with the ``id`` selector requested
and replace all the relative links from its content making them absolute.

.. note::

   Any other case outside this contract will be considered *special* and will be implemented
   only under ``?doctool=``, ``?version=`` and ``?writer=`` arguments.

If no ``id`` selector is sent to the request, the content of the first meaningful HTML tag
(``<main>``, ``<div role="main">`` or other well-defined standard tags) identifier found is returned.


Embed endpoints
---------------

This is the list of endpoints to be implemented in APIv3:

.. http:get:: /api/v3/embed/

   Returns the exact HTML content for a specific identifier (``id``).
   If no anchor identifier is specified the content of the first one returned.

   **Example request**:

   .. code:: bash

      $ curl https://readthedocs.org/api/v3/embed/?url=https://docs.readthedocs.io/en/latest/development/install.html#set-up-your-environment

   **Example response**:

   .. sourcecode:: json

      {
         "project": "docs",
         "version": "latest",
         "language": "en",
         "path": "development/install.html",
         "title": "Development Installation",
         "url": "https://docs.readthedocs.io/en/latest/install.html#set-up-your-environment",
         "id": "set-up-your-environment",
         "content": "<div class=\"section\" id=\"development-installation\">\n<h1>Development Installation<a class=\"headerlink\" href=\"https://docs.readthedocs.io/en/stable/development/install.html#development-installation\" title=\"Permalink to this headline\">¶</a></h1>\n ..."
      }

   :query url (required): Full URL for the documentation page with optional anchor identifier.


.. http:get:: /api/v3/embed/metadata/

   Returns all the available metadata for an specific page.

   .. note::

      As it's not trivial to get the ``title`` associated with a particular ``id`` and it's not easy to get a nested list of identifiers,
      we may not implement this endpoint in initial version.

      The endpoint as-is, is mainly useful to explore/discover what are the identifiers available for a particular page
      --which is handy in the development process of a new tool that consumes the API.
      Because of this, we don't have too much traction to add it in the initial version.

   **Example request**:

   .. code:: bash

      $ curl https://readthedocs.org/api/v3/embed/metadata/?url=https://docs.readthedocs.io/en/latest/development/install.html

   **Example response**:

   .. sourcecode:: json

      {
        "identifiers": {
            "id": "set-up-your-environment",
            "url": "https://docs.readthedocs.io/en/latest/development/install.html#set-up-your-environment"
            "_links": {
                "embed": "https://docs.readthedocs.io/_/api/v3/embed/?url=https://docs.readthedocs.io/en/latest/development/install.html#set-up-your-environment"
            }
        },
        {
            "id": "check-that-everything-works",
            "url": "https://docs.readthedocs.io/en/latest/development/install.html#check-that-everything-works"
            "_links": {
                "embed": "https://docs.readthedocs.io/_/api/v3/embed/?url=https://docs.readthedocs.io/en/latest/development/install.html#check-that-everything-works"
            }
         },
      }

   :query url (required): Full URL for the documentation page


Handle specific Sphinx cases
----------------------------

.. https://github.com/readthedocs/readthedocs.org/pull/8039#discussion_r640670085

We are currently handling some special cases for Sphinx due how it writes the HTML output structure.
In some cases, we look for the HTML tag with the identifier requested but we return
the ``.next()`` HTML tag or the ``.parent()`` tag instead of the *requested one*.

Currently, we have identified that this happens for definition tags (``dl``, ``dt``, ``dd``)
--but may be other cases we don't know yet.
Sphinx adds the ``id=`` attribute to the ``dt`` tag, which contains only the title of the definition,
but as a user, we are expecting the description of it.

In the following example we will return the whole ``dl`` HTML tag instead of
the HTML tag with the identifier ``id="term-name"`` as requested by the client,
because otherwise the "Term definition for Term Name" content won't be included and the response would be useless.

.. code:: html

   <dl class="glossary docutils">
     <dt id="term-name">Term Name</dt>
     <dd>Term definition for Term Name</dd>
   </dl>

If the definition list (``dl``) has more than *one definition* it will return **only the term requested**.
Considering the following example, with the request ``?url=glossary.html#term-name``

.. code:: html

   <dl class="glossary docutils">
     ...

     <dt id="term-name">Term Name</dt>
     <dd>Term definition for Term Name</dd>

     <dt id="term-unknown">Term Unknown</dt>
     <dd>Term definition for Term Unknown </dd>

     ...
   </dl>


It will return the whole ``dl`` with only the ``dt`` and ``dd`` for ``id`` requested:

.. code:: html

   <dl class="glossary docutils">
     <dt id="term-name">Term Name</dt>
     <dd>Term definition for Term Name</dd>
   </dl>


However, this assumptions may not apply to documentation pages built with a different doctool than Sphinx.
For this reason, we need to communicate to the API that we want to handle this special cases in the backend.
This will be done by appending a request GET argument to the Embed API endpoint: ``?doctool=sphinx&version=4.0.1&writer=html4``.
In this case, the backend will known that has to deal with these special cases.

.. note::

   This leaves the door open to be able to support more special cases (e.g. for other doctools) without breaking the actual behavior.


Support for external documents
------------------------------

When the ``?url=`` argument passed belongs to a documentation page not hosted on Read the Docs,
the endpoint will do an external request to download the HTML file,
parse it and return the content for the identifier requested.

The whole logic should be the same, the only difference would be where the source HTML comes from.

.. warning::

   We should be careful with the URL received from the user because those may be internal URLs and we could be leaking some data.
   Example: ``?url=http://localhost/some-weird-endpoint`` or ``?url=http://169.254.169.254/latest/meta-data/``
   (see https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/instancedata-data-retrieval.html).

   This is related to SSRF (https://en.wikipedia.org/wiki/Server-side_request_forgery).
   It doesn't seem to be a huge problem, but something to consider.

   Also, the endpoint may need to limit the requests per-external domain to avoid using our servers to take down another site.

.. note::

   Due to the potential security issues mentioned, we will start with an allowed list of domains for common Sphinx docs projects.
   Projects like Django and Python, where ``sphinx-hoverxref`` users might commonly want to embed from.
   We aren't planning to allow arbitrary HTML from any website.


Handle project's domain changes
-------------------------------

The proposed Embed APIv3 implementation only allows ``?url=`` argument to embed content from that page.
That URL can be:

* a URL for a project hosted under ``<project-slug>.readthedocs.io``
* a URL for a project with a custom domain

In the first case, we can easily get the project's slug directly from the URL.
However, in the second case we get the project's slug by querying our database for a ``Domain`` object
with the full domain from the URL.

Now, consider that all the links in the documentation page that uses Embed APIv3 are pointing to
``docs.example.com`` and the author decides to change the domain to be ``docs.newdomain.com``.
At this point there are different possible scenarios:

* The user creates a new ``Domain`` object with ``docs.newdomain.com`` as domain's name.
  In this case, old links will keep working because we still have the old ``Domain`` object in our database
  and we can use it to get the project's slug.
* The user *deletes* the old ``Domain`` besides creating the new one.
  In this scenario, our query for a ``Domain`` with name ``docs.example.com`` to our database will fail.
  We will need to do a request to ``docs.example.com`` and check for a 3xx response status code and in that case,
  we can read the ``Location:`` HTTP header to find the new domain's name for the documentation.
  Once we have the new domain from the redirect response, we can query our database again to find out the project's slug.

  .. note::

     We will follow up to 5 redirects to find out the project's domain.


Embed APIv2 deprecation
-----------------------

The v2 is currently widely used by projects using the ``sphinx-hoverxref`` extension.
Because of that, we need to keep supporting it as-is for a long time.

Next steps on this direction should be:

* Add a note in the documentation mentioning this endpoint is deprecated
* Promote the usage of the new Embed APIv3
* Migrate the ``sphinx-hoverxref`` extension to use the new endpoint

Once we have done them, we could check our NGINX logs to find out if there are people still using APIv2,
contact them and let them know that they have some months to migrate since the endpoint is deprecated and will be removed.


Unanswered questions
--------------------

* How do we distinguish between our APIv3 for resources (models in the database) from these "feature API endpoints"?
