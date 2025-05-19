Link previews
=============

Link previews allows you to see the content of the link you are about to click when you hover over it.
This gives you the ability to quickly preview where a link points,
so you can keep your context while reading but learn more from other resources.

.. figure:: /_static/images/addons-link-previews.png
   :width: 80%

   Example of link previews addon

Link previews will only be generated for internal links--links that point to pages within your documentation site.
No link previews will be generated for links to external sites or links that appear in the :doc:`flyout menu </flyout_menu>`.

You can see an example of a link preview by hovering over the following link: :doc:`Addons </addons>`.

Enabling link previews
----------------------

1. In your :term:`dashboard`, navigate to a projects page. 
2. Go to the links preview tag in :guilabel:`Settings > Addons > Link previews` and enable it.
3. Save your settings and rebuild your project.

Troubleshooting link previews
-----------------------------

We perform some heuristic to detect the documentation tool used to generate the page based on its HTML structure.
This auto-detection may fail, resulting in the content rendered inside the popup being incorrect.
If you are experiencing this, you can specify the CSS selector for the main content in :guilabel:`Settings > Addons > Advanced`,
or you can `open an issue in the addons repository <https://github.com/readthedocs/addons>`_ so we improve our heuristic.

Link previews won't be generated if javascript is not enabled in your web browser or if all cookies are blocked.
