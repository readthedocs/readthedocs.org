Links preview
=============

Links previews allows you to see the content of the link you are about to click when you hover it.
This content will be rendered inside a popup that disappears after moving the mouse outside of it.

.. figure:: /_static/images/addons-links-preview.png
   :width: 80%

   Example of links preview addon



Enabling links previews
-----------------------

In your dashboard, you can go to the links preview tag in :guilabel:`Settings > Addons > Links preview` and enable it.

Troubleshooting links previews
------------------------------

We perform some heuristic to detect the documentation tool used to generate the page based on its HTML structure.
This auto-detection may fail, resulting in the content rendered inside the popup being incorrect.
If you are experimenting this, you can specify the CSS selector for the main content in :guilabel:`Settings > Addons > Advanced`,
or you can `open an issue in the addons repository <https://github.com/readthedocs/addons>`_ so we improve our heuristic.
