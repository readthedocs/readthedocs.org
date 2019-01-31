Use custom 404 page on my project
=================================

If you want your project to use a custom page for not found pages instead of the "Maze Found" default one,
you can put a ``404.html`` on the root of your project's output.

When a 404 is returned, Read the Docs checks if there is a ``404.html`` in the root of your project's output and uses it if it exists.

As the ``404.html`` will be returned for all the URLs where the real page was not found,
all its resources URLs and links must be absolute (start with a `/`),
otherwise they will not work when a user clicks on them.

In case you want to follow the same style for the 404 page than your theme, you can use the `sphinx-notfound-page`_ extension.


Using ``sphinx-notfound-page`` extension
----------------------------------------

The ``sphinx-notfound-page`` extension helps you to create and automatically arrange all the URLs and file location without worry about them.
You can define ``notfound_body`` setting in your Sphinx's ``conf.py`` with the content of the page.
See it's documentation_ for more customization.


.. _sphinx-notfound-page: https://github.com/humitos/sphinx-notfound-page
.. _documentation: https://github.com/humitos/sphinx-notfound-page
.. _html_extra_path: http://www.sphinx-doc.org/en/stable/usage/configuration.html#confval-html_extra_path
