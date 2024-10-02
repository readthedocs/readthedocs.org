.. TODO: Update the images to the new flyout design, and update to include Addons

Flyout menu
===========

When you are using a Read the Docs site,
you will likely notice that we embed a menu on all the documentation pages we serve.
This is a way to expose the functionality of Read the Docs on the page,
without having to have the documentation theme integrate it directly.

There are two versions of the flyout menu:

- :ref:`flyout-menu:Addons flyout menu`
- :ref:`flyout-menu:Original flyout menu`

Addons flyout menu
------------------

The updated :doc:`addons` flyout menu lists available documentation versions and translations, as well as useful links,
offline formats, and a search bar.

.. figure:: /_static/images/flyout-addons.png
   :align: center

   The opened flyout menu

Customizing the flyout menu
~~~~~~~~~~~~~~~~~~~~~~~~~~~

In your dashboard, you can configure flyout menu options in :guilabel:`Settings`, under :guilabel:`Addons`.

Sort your versions :guilabel:`Alphabetically`, by :guilabel:`SemVer`, by :guilabel:`Python Packaging`,
by :guilabel:`CalVer`, or define your own pattern.

Choose whether to list stable versions first or not.

Customizing the look of the addons flyout menu
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The addons flyout exposes all the required data to build the flyout menu via a JavaScript ``CustomEvent``.
Take a look at an example of this approach at https://github.com/readthedocs/sphinx_rtd_theme/pull/1526.

Original flyout menu
--------------------

The flyout menu provides access to the following bits of Read the Docs functionality:

* A :doc:`version switcher </versions>` that shows users all of the active, unhidden versions they have access to.
* :doc:`Offline formats </downloadable-documentation>` for the current version, including HTML & PDF downloads that are enabled by the project.
* Links to the Read the Docs dashboard for the project.
* Links to your :doc:`Git provider </reference/git-integration>` that allow the user to quickly find the exact file that the documentation was rendered from.
* A search bar that gives users access to our :doc:`/server-side-search/index` of the current version.

.. figure:: /_static/images/flyout-open.png
   :align: center

   The opened flyout
