Badges
======

Badges let you show the state of your documentation to your users.
They are great for embedding in your README,
or putting inside your actual doc pages.

Status badges
-------------

They will display in green for passing,
red for failing,
and yellow for unknown states.
They will link back to your project's documentation page on Read the Docs.

Here are a few examples:

|green| |nbsp| |red| |nbsp| |yellow|

You can see it in action in the `Read the Docs README`_.

Style
-----

You can pass the ``style`` GET argument to get custom styled badges same as you would for `shields.io <https://shields.io/>`_.
By default, ``flat`` style is used.

+---------------+---------------------+
| Style         | Badge               |
+===============+=====================+
| flat          | |Flat Badge|        |
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


Version
-------

You can change the version of the documentation your badge points to.
To do this, you can pass the ``version`` GET argmento to the badge URL.
By default, it will point at the *default version* you have specified for your project.

The badge URL looks like this::

    https://readthedocs.org/projects/pip/badge/?version=v3.x


Project pages
-------------

On each :term:`project home`'s page there is a badge that communicates the status of the default version.
If you click on the badge icon,
you will be given snippets for reStructuredText, Markdown, and HTML
to make embedding it easier.


.. _Read the Docs README: https://github.com/readthedocs/readthedocs.org/blob/main/README.rst
.. |green| image:: https://assets.readthedocs.org/static/projects/badges/passing-flat.svg
.. |red| image:: https://assets.readthedocs.org/static/projects/badges/failing-flat.svg
.. |yellow| image:: https://assets.readthedocs.org/static/projects/badges/unknown-flat.svg
.. |nbsp| unicode:: 0xA0
   :trim:
