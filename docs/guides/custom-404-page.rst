Use custom 404 page on my project
=================================

If you want your project to use a custom page for not found pages instead of the "Maze Found" default one,
you can put a ``404.html`` on the root of your project's output.

When a 404 is returned, Read the Docs checks if there is a ``404.html`` in the root of your project's output and uses it if it exists.

As the ``404.html`` will be returned for all the URLs where the real page was not found,
all its resources URLs and links must be absolute (including internals),
otherwise they won't be found by the client for all the 404 URLs producing errors while displaying the page (styles and/or images not found).

In case you want to follow the same style for the 404 page than your theme, you can either:

1. manually copy the source of any already rendered pages or,
1. use the `sphinx-notfound-page`_ extension


Manually creation
-----------------

Once your docs are built, you can open any of the page already built and copy its source code,
make all the links absolute and replace the content of the body with the one you like.

.. warning::

   This method requires knowledge of HTML and some knowledge of how to build the URLs properly to work under Read the Docs,
   considering that the docs are usually served under ``/{language}/{version}/``.

After that, you have to define `html_extra_path`_ setting in your Sphinx's ``conf.py`` to include the ``404.html`` file created in the output.


Using ``sphinx-notfound-page`` extension
----------------------------------------

The ``sphinx-notfound-page`` extension helps you to create and automatically arrange all the URLs and file location without worry about them.
You can define ``notfound_body`` setting in your Sphinx's ``conf.py`` with the content of the page.


.. _sphinx-notfound-page: https://github.com/humitos/sphinx-notfound-page
.. _html_extra_path: http://www.sphinx-doc.org/en/stable/usage/configuration.html#confval-html_extra_path
