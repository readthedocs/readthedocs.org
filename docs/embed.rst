Embed API
=========

Read the Docs allow you to embed content from any of the projects we host. 
This allows for content re-use across sites,
making sure the content is always up to date.

Workflow
--------

There are many uses of our Embed API.
One of our favorites is for inline help.
We have started using this on Read the Docs itself to provide inline help on our main site pages.
This allows us to keep the official documentation as the single source of truth,
while having great inline help in our application as well. 

We recommend you point at **tagged releases** instead of ``latest``. 
Tags don't change over time,
so you don't have to worry about the content you are embedding disappearing.

.. note:: All relative links to pages contained in the remote content will continue to point at the remote page.

How to use it
-------------


Sphinx Extension
~~~~~~~~~~~~~~~~

You can embed content directly in Sphinx with builds on Read the Docs.
We support default configuration variables for your ``conf.py``:

* readthedocs_embed_project
* readthedocs_embed_version
* readthedocs_embed_doc

These are overridable per-call as well.
Then you simply use the directive:

.. code-block:: restructuredtext

    # All arguments
    .. readthedocs-embed:: 
        :project: myproject
        :version: latest
        :doc: index
        :section: User Guide

    # Or with some defaults
    .. readthedocs-embed:: 
        :doc: index
        :section: User Guide


Javascript
~~~~~~~~~~

We provide a Javascript library that you can embed on any site.
An example:

.. code-block:: html

    <!-- In your <head> -->
    <link rel="stylesheet" href="http://localhost:5555/static/css/public.css">
    <script type="text/javascript" src="http://localhost:5555/static/javascript/bundle-public.js"></script>
    <script>
    embed = ReadTheDocs.Embed(project, version)
    rtd.into('page', 'section', function(content){
        $('#foobar').html(content)
    })

    </script>

    <!-- In your <body> -->
    <div id="help_container">
      <a href="#" class="readthedocs-help-embed" data-section="How we envision versions working">(Help)</a>
    </div>


This will provide a pop-out for a user with the ``How we envision versions working`` section of the ``versions`` page.
You can see this in action here:

.. raw:: html

    <script type="text/javascript" src="https://media.readthedocs.org/javascript/jquery/jquery-2.0.3.min.js"></script>
    <script type="text/javascript" src="https://media.readthedocs.org/javascript/jquery/jquery-migrate-1.2.1.min.js"></script>
    <link rel="stylesheet" href="http://localhost:5555/static/css/public.css">
    <script type="text/javascript" src="http://localhost:5555/static/javascript/bundle-public.js"></script>
    <script>
     var READTHEDOCS_EMBED = {
        'project': 'docs',
        'version': 'latest',
        'doc': 'versions',
        'section': 'Versions'
      }
    </script>
    <div id="help_container">
      <a href="#" class="readthedocs-help-embed" data-section="How we envision versions working">(Help)</a>
    </div>
    <br>
    <br>

.. note:: All Read the Docs pages already have the library loaded, so you can ignore the ``link`` and first ``script`` tags on all documentation.



.. warning:: We currently do not provide caching on this API. 
             If the remote source you are including changes their page structure or deletes the content,
             your embed will break.

             In Version 2 of this API we will provide a full-formed workflow that will stop this from happening.



Example API Response
--------------------

Pure API use will return JSON:

.. code-block:: javascript

    {
        "content": [
            "<div class=\"section\" id=\"encoded-data\">\n<h2>Encoded Data?<a class=\"headerlink\" href=\"/docs/requests/en/latest/community/faq.html#encoded-data\" title=\"Permalink to this headline\">\u00b6</a></h2>\n<p>Requests automatically decompresses gzip-encoded responses, and does\nits best to decode response content to unicode when possible.</p>\n<p>You can get direct access to the raw response (and even the socket),\nif needed as well.</p>\n</div>"
        ], 
        "wrapped": [
            "\n<div class=\"readthedocs-embed-wrapper\">\n    <div class=\"readthedocs-embed-content\">\n        <div class=\"section\" id=\"encoded-data\">\n<h2>Encoded Data?<a class=\"headerlink\" href=\"/docs/requests/en/latest/community/faq.html#encoded-data\" title=\"Permalink to this headline\">\u00b6</a></h2>\n<p>Requests automatically decompresses gzip-encoded responses, and does\nits best to decode response content to unicode when possible.</p>\n<p>You can get direct access to the raw response (and even the socket),\nif needed as well.</p>\n</div>\n    </div>\n    <div class=\"readthedocs-embed-badge\">\n        Embedded from <a href=\"/docs/requests/en/latest/community/faq.html\">Read the Docs</a>\n    </div>\n</div>\n    "
        ], 
        "meta": {
            "project": "requests", 
            "doc": "community/faq", 
            "section": "Encoded Data?", 
            "version": "latest", 
            "modified": "Wed, 04 Feb 2015 08:59:59 GMT"
        }, 
        "url": "/docs/requests/en/latest/community/faq.html", 
        "headers": [
            {
                "Frequently Asked Questions": "#"
            }, 
            {
                "Encoded Data?": "#encoded-data"
            }, 
            {
                "Custom User-Agents?": "#custom-user-agents"
            }, 
            {
                "Why not Httplib2?": "#why-not-httplib2"
            }, 
            {
                "Python 3 Support?": "#python-3-support"
            }, 
            {
                "What are \u201chostname doesn\u2019t match\u201d errors?": "#what-are-hostname-doesn-t-match-errors"
            }
        ]
    }