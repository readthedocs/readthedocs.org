Content Embedding
=================

Using the `Read the Docs JavaScript Client`_, or with basic calls to our REST
API, you can retrieve embeddable content for use on your own site. Content is
embedded in an iframe element, primarily for isolation. To get example usage of
the API, see the tools tab under an active project and select the page and
section that you would like to test.

.. note::

    The client library is still alpha quality. This guide is still lacking
    advanced usage of the library, and information on styling the iframe
    content. We plan to have more usage outlined as the library matures.

Example usage of the client library:

.. code-block:: javascript

    var embed = Embed();
    embed.section(
        'read-the-docs', 'latest', 'features', 'Read the Docs features',
        function (section) {
            section.insertContent($('#help'));
        }
    );

.. _`Read the Docs JavaScript Client`: https://github.com/agjohnson/readthedocs-client-js
