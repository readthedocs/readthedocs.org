Embed APIv3
===========

The Embed API allows to embed content from documentation pages in other sites.
It has been treated as an *experimental* feature without public documentation or real applications,
but recently it started to be used widely (mainly because we created a Sphinx extension).

The main goal of this document is to design a new version of the Embed API to be more user friendly,
make it more stable over time, support documentation pages not hosted at Read the Docs,
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

Considering the problems mentioned in the previous section,
the inclusion of new features and the definition of a contract that works the same for all,
this document set the following goals for the new version of this endpoint:

* Support external documents hosted outside Read the Docs
* Do not depend on Sphinx ``.fjson`` files
* Query and parse the ``.html`` file directly (from our storage or from an external request)
* Rewrite all links returned in the content to make them absolute
* Always return valid HTML structure
* Delete HTML tags from the original document if needed
* Support ``?nwords=`` and ``?nparagraphs=`` to return chunked content
* Require a valid HTML ``id`` selector
* Handle special cases for particular doctools (e.g. Sphinx requires to return the ``.parent()`` element for ``dl``)
* Make explicit the client is asking to handle the special cases (e.g. send ``?doctool=sphinx&version=4.0.1``)
* Accept only ``?url=`` request GET argument to query the endpoint
* Add HTTP cache headers to cache responses
* Allow :abbr:`CORS` from everywhere


Embed endpoint
--------------

Returns the exact HTML content for a specific identifier.
If no anchor identifier is specified the content of the whole page is returned.

.. http:get:: /api/v3/embed/?url=https://docs.readthedocs.io/en/latest/development/install.html#set-up-your-environment

   :query url (required): Full URL for the documentation page with optional anchor identifier.
   :query expand (optional): Allows to return extra data about the page. Currently, only ``?expand=identifiers`` is supported
      to return all the identifiers that page accepts.

   .. sourcecode:: json

      {
         "project": "docs",
         "version": "latest",
         "language": "en",
         "path": "development/install.html",
         "title": "Development Installation",
         "url": "https://docs.readthedocs.io/en/latest/install.html#set-up-your-environment",
         "id": "set-up-your-environment",
         "content": "<div class=\"section\" id=\"development-installation\">\n<h1>Development Installation<a class=\"headerlink\" href=\"https://docs.readthedocs.io/en/stable/development/install.html#development-installation#development-installation\" title=\"Permalink to this headline\">¶</a></h1>\n ..."
      }


   When used together with ``?expand=identifiers`` the follwing field is also returned:

   .. sourcecode:: json

      {
         "identifiers": [
            {
               "title": "Set up your environment",
               "id": "set-up-your-environment",
               "url": "https://docs.readthedocs.io/en/latest/development/install.html#set-up-your-environment"
            },
            {
               "title": "Check that everything works",
               "id": "check-that-everything-works",
               "url": "https://docs.readthedocs.io/en/latest/development/install.html#check-that-everything-works"
            },
            ...
         ]
      }


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
This will be done by appending a request GET argument to the Embed API endpoint: ``?doctool=sphinx&version=4.0.1``.
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

   We should be carefull with the URL received from the user because those may be internal URLs and we could be leaking some data.
   Example: ``?url=http://localhost/some-weird-endpoint`` or ``?url=http://169.254.169.254/latest/meta-data/``
   (see https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/instancedata-data-retrieval.html).

   This is related to SSRF (https://en.wikipedia.org/wiki/Server-side_request_forgery).
   It doesn't seem to be a huge problem, but something to consider.

   Also, the endpoint may need to limit the requests per-external domain to avoid using our servers to take down another site.


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
* What happen if a project changes its custom domain? Do we support redirects in this case?
