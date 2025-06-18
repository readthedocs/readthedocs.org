Visual diff
===========

Visual diff allows you to see a visual :term:`diff` on a documentation page,
showing what has changed between the ``latest`` version and the active :doc:`pull request </pull-requests>`.

Visual diff allows you to quickly review changes visually,
and focus your review on what has changed in the current page.

Using Visual diff
-----------------

Visual diff is enabled by default and is only available on pull request builds.
It works by comparing the current page with the default version of the documentation (e.g. where `/` redirects to).

When Visual diff is enabled,
a new UI element appears at the top right of the page showing a dropdown selector containing all the files that have changed in that pull request build.

.. figure:: /img/screenshot-viz-diff-ui.png
   :width: 80%

You can select any of those files from the dropdown to jump directly into that page.
Once there, you can toggle Visual Diff on and off by pressing the :guilabel:`Show diff` link from the UI element, or pressing the `d` key if you have hotkeys enabled.

Visual diff will show all the sections that have changed and their differences highlighted with red/green background colors.
Then you can jump between each of these chunks by clinking on the up/down arrows.

Configuring Visual Diff
-----------------------

All the available configuration for the visual diff addon can be found under :guilabel:`Settings > Addons > Visual diff` in the :term:`dashboard`.
You can choose to disable/enable the `Visual diff` feature on a per project basis.
Visual diff can also ignore files by specifying these files under `File tree diff`, regex supported.

Troubleshooting Visual diff
---------------------------

Visual diff only works when we detect changes on the page,
so ensure you are on a page that has changed in the current pull request.

There are also some known issues that currently don't display properly.
We are working to improve the UX, but so far we've found the following issues:

* **Tables** are shown to have changes when they may not have changed. This is due to subtle variations in how HTML tables are rendered, and will be fixed in a future version.
* **Invisible changes** sometimes are marked as diff due than the underlying HTML changing, but there is no visual change. This could happen if the URL of a link changed, for example.
* **Chunks background is incorrect** when we are unable to detect the correct main parent element for the chunk.
