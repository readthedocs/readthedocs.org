Embedding content from your docs online
=======================================

Using the `Read the Docs JavaScript Client`_, or with basic calls to our REST
API, you can retrieve embeddable content for use on your own site. Content is
embedded in an iframe element, primarily for isolation. 

Inside your documentation
-------------------------

This is the best supported use of embedding content.
We have built the `sphinx-hoverxref`_ package to allow you to automatically add hover references inside your Sphinx documentation.

You can see a few examples on this page,
including :ref:`here <guides/embedding-content:Example usage of the client library>`.

.. _sphinx-hoverxref: https://sphinx-hoverxref.readthedocs.io/

Using the API
-------------

You can hit the Embed API at https://readthedocs.org/api/v2/embed/. This query browser will let you play around with the embed tooling.

A simple example using curl looks like this::

    curl -s "https://readthedocs.org/api/v1/embed/?project=docs&version=latest&doc=features&section=Auto-updating"  | python3 -m json.tool

This will pull the content fron the :ref:`features:Auto-updating` page and embed it into your terminal.

Browsing available file
-----------------------

If you need a bit of help you can use the Embed API browser located on each project.
Currently the URL is not exposed on the website,
but you can see an example on the docs repo: https://readthedocs.org/projects/docs/tools/embed/

Example usage of the client library
-----------------------------------

.. code-block:: javascript

    var embed = Embed();
    embed.section(
        'read-the-docs', 'latest', 'features', 'Read the Docs features',
        function (section) {
            section.insertContent($('#help'));
        }
    );

.. _`Read the Docs JavaScript Client`: https://github.com/agjohnson/readthedocs-client-js
