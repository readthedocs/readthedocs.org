Visual diff
===========

Visual diff allows you to see a visual :term:`diff` on a documentation page,
showing what has changed between the ``latest`` version and the active :doc:`pull request </pull-requests>`.

Visual diff allows you to quickly review changes visually,
and focus your review on what has changed in the current page.

.. figure:: /img/addons-docdiff.gif
   :width: 80%

   Example of Visual diff

Enabling Visual diff
--------------------

Visual diff is only enabled on pull request builds,
and can be toggled on and off with the ``d`` hotkey.

Troubleshooting Visual diff
---------------------------

Visual diff only works if there are changes on the page,
so ensure you are on a page that has changed in the current pull request.

There are also some known issues that currently don't display properly:

* **Tables** are shown to have changes when they may not have changed. This is due to do subtly in how HTML tables are rendered, and will be fixed in a future version.
