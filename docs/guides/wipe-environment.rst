Wiping a Build Environment
==========================

Sometimes it happen that your Builds start failing because the build
environment where the documentation is created is stale or
broken. This could happen for a couple of different reasons like `pip`
not upgrading a package properly or a corrupted cached Python package.

In any of these cases (and many others), the solution could be just
wiping out the existing build environment files and allow Read the
Docs to create a new fresh one.

Follow these steps to wipe the build environment:

* Go to :guilabel:`Versions`
* Click on the **Edit** button of the version you want to wipe on the
  right side of the page
* Go to the bottom of the page and click the **wipe** link, next to
  the "Save" button

.. note::

   By wiping the documentation build environment, all the `rst`, `md`,
   and code files associated with it will be removed but not the
   documentation already built (`HTML` and `PDF` files). Your
   documentation will still be online after wiping the build environment.

Now you can re-build the version with a fresh build environment!
