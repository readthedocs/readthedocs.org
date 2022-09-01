Status Badges
=============

Status badges let you show the state of your documentation to your users.
They are great for embedding in your README,
or putting inside your actual doc pages.

Display states
--------------

Badges have the following stats:

* green for passing
* red for failing
* yellow for unknown states

By default,
badges link back to your project's documentation page on Read the Docs.

Here are a few examples:

|green| |nbsp| |red| |nbsp| |yellow|

You can see it in action in the `Read the Docs README`_.

Style
-----

You can pass the ``style`` GET argument to get custom styled badges.
This allows you to match the look and feel of your website.
By default, the ``flat`` style is used.

+---------------+---------------------+
| Style         | Badge               |
+===============+=====================+
| flat - default| |Flat Badge|        |
+---------------+---------------------+
| flat-square   | |Flat-Square Badge| |
+---------------+---------------------+
| for-the-badge | |Badge|             |
+---------------+---------------------+
| plastic       | |Plastic Badge|     |
+---------------+---------------------+
| social        | |Social Badge|      |
+---------------+---------------------+

.. |Flat Badge| image:: https://readthedocs.org/projects/pip/badge/?version=latest&style=flat
.. |Flat-Square Badge| image:: https://readthedocs.org/projects/pip/badge/?version=latest&style=flat-square
.. |Badge| image:: https://readthedocs.org/projects/pip/badge/?version=latest&style=for-the-badge
.. |Plastic Badge| image:: https://readthedocs.org/projects/pip/badge/?version=latest&style=plastic
.. |Social Badge| image:: https://readthedocs.org/projects/pip/badge/?version=latest&style=social


Version-specific badges
-----------------------

You can change the version of the documentation your badge points to.
To do this, you can pass the ``version`` GET argument to the badge URL.
By default, it will point at the *default version* you have specified for your project.

The badge URL looks like this::

    https://readthedocs.org/projects/docs/badge/?version=latest


Badges on dashboard pages
-------------------------

On each :term:`project home` page there is a badge that communicates the status of the default version.
If you click on the badge icon,
you will be given snippets for reStructuredText, Markdown, and HTML
to make embedding it easier.

.. _Read the Docs README: https://github.com/readthedocs/readthedocs.org/blob/main/README.rst
.. |green| image:: https://assets.readthedocs.org/static/projects/badges/passing-flat.svg
.. |red| image:: https://assets.readthedocs.org/static/projects/badges/failing-flat.svg
.. |yellow| image:: https://assets.readthedocs.org/static/projects/badges/unknown-flat.svg
.. |nbsp| unicode:: 0xA0
   :trim:
