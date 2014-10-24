Badges
======

Badges let you show the state of your documentation to your users.
They are great for embedding in your README,
or putting inside your actual doc pages.

Status Badges
-------------

They will display in green for passing,
red for failing,
and yellow for unknown states.

Here are a few examples:

|green| |nbsp| |red| |nbsp| |yellow|

You can see it in action in the `Read the Docs README`_.
They will link back to your project's documentation page on Read the Docs.

Project Pages
-------------

You will now see badges embedded in your `project page`_.
The default badge will be pointed at the *default version* you have specified for your project.
The badge URLs look like this::

    https://readthedocs.org/projects/pip/badge/?version=latest

You can replace the version argument with any version that you want to show a badge for.
If you click on the badge icon,
you will be given snippets for RST, Markdown, and HTML;
to make embedding it easier.

If you leave the version argument off,
it will default to your latest version.
This is probably best to include in your README,
since it will stay up to date with your Read the Docs project::

    https://readthedocs.org/projects/pip/badge/

Style
-----

If you pass the ``style`` GET argument,
we will pass it along to shields.io as is.
This will allow you to have custom style badges.


.. _Read the Docs README: https://github.com/rtfd/readthedocs.org/blob/master/README.rst
.. _project page: https://readthedocs.org/projects/pip/
.. |green| image:: https://img.shields.io/badge/Docs-latest-brightgreen.svg?style=flat
.. |red| image:: https://img.shields.io/badge/Docs-release--1.6-red.svg?style=flat
.. |yellow| image:: https://img.shields.io/badge/Docs-No%20Builds-yellow.svg?style=flat
.. |nbsp| unicode:: 0xA0 
   :trim:

