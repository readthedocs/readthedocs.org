Use custom ``404 Not Found`` page on my project
===============================================

If you want your project to use a custom page for not found pages instead of the "Maze Found" default one,
you can put a ``404.html`` at the top level of your project's HTML output.

When a 404 is returned, Read the Docs checks if there is a ``404.html`` in the root of your project's output and uses it if it exists.

As the ``404.html`` will be returned for all the URLs where the real page was not found,
all its resources URLs and links must be absolute (starting with a ``/``),
otherwise they will not work when a user clicks on them.

In case you don't want to deal with these links manually,
or you want to use the same style as your theme,
you can use the `sphinx-notfound-page`_ extension.


Using ``sphinx-notfound-page`` extension
----------------------------------------

The ``sphinx-notfound-page`` extension automatically creates the proper URLs for your 404 page.
Once the extension is installed, it will generate the default 404 page for your project.
See its documentation_ for how to install and custom it.


.. _sphinx-notfound-page: https://pypi.org/project/sphinx-notfound-page
.. _documentation: https://sphinx-notfound-page.readthedocs.io/
