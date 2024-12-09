Link previews
=============

Link previews allows you to see the content of the link you are about to click when you hover over it.
This gives you the ability to quickly preview where a link points,
so you can keep your context while reading but learn more from other resources.

.. figure:: /_static/images/addons-link-previews.png
   :width: 80%

   Example of link previews addon



Enabling link previews
----------------------

In your dashboard, you can go to the links preview tag in :guilabel:`Settings > Addons > Link previews` and enable it.

Troubleshooting link previews
-----------------------------

We perform some heuristic to detect the documentation tool used to generate the page based on its HTML structure.
This auto-detection may fail, resulting in the content rendered inside the popup being incorrect.
If you are experimenting this, you can specify the CSS selector for the main content in :guilabel:`Settings > Addons > Advanced`,
or you can `open an issue in the addons repository <https://github.com/readthedocs/addons>`_ so we improve our heuristic.
