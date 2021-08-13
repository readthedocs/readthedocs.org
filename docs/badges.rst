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

Style
-----

Now you can pass the ``style`` GET argument,
to get custom styled badges same as you would for shields.io. 
If no argument is passed, ``flat`` is used as default.

+---------------+---------------------+
| STYLE         | BADGE               |
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


Project Pages
-------------

You will now see badges embedded in your `project page`_.
The default badge will be pointed at the *default version* you have specified for your project.
The badge URLs look like this::

    https://readthedocs.org/projects/pip/badge/?version=latest&style=plastic

You can replace the version argument with any version that you want to show a badge for.
If you click on the badge icon,
you will be given snippets for RST, Markdown, and HTML;
to make embedding it easier.

If you leave the version argument off,
it will default to your latest version.
This is probably best to include in your README,
since it will stay up to date with your Read the Docs project::

    https://readthedocs.org/projects/pip/badge/


.. _Read the Docs README: https://github.com/readthedocs/readthedocs.org/blob/master/README.rst
.. _project page: https://readthedocs.org/projects/pip/
.. |green| image:: https://assets.readthedocs.org/static/projects/badges/passing-flat.svg
.. |red| image:: https://assets.readthedocs.org/static/projects/badges/failing-flat.svg
.. |yellow| image:: https://assets.readthedocs.org/static/projects/badges/unknown-flat.svg
.. |nbsp| unicode:: 0xA0
   :trim:
