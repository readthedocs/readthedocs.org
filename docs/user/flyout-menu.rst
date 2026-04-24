.. TODO: Update the images to the new flyout design, and update to include Addons

Flyout menu
===========

When you use a Read the Docs site,
there is a flyout menu embedded on all the documentation pages.
The flyout menu is a way to expose the functionality of Read the Docs on the page,
without having to have the documentation theme integrate it directly.

.. tip::
   The flyout menu is a default implementation that works for every site.
   You can access the full data used to construct the flyout,
   and use that to integrate the data directly into your documentation theme for a nicer user experience.
   See the :ref:`flyout-menu:Custom event integration` for more information.

Addons flyout menu
------------------

The :doc:`addons` flyout provides a place for a number of Read the Docs features:

* A :doc:`version switcher </versions>` that shows users all of the active versions they have access to.
* A :doc:`translation switcher </localization>` that shows all the documentation languages provided.
* A list of :doc:`offline formats </downloadable-documentation>` for the current version, including HTML & PDF downloads.
* Links to the Read the Docs dashboard for the project.
* A search bar that gives users access to the :doc:`/server-side-search/index` of the current version.

.. figure:: /_static/images/flyout-addons.png
   :align: center

   The opened flyout menu

Customizing the flyout menu
~~~~~~~~~~~~~~~~~~~~~~~~~~~

In your dashboard, you can configure flyout menu options in :guilabel:`Settings > Addons > Flyout Menu`.

Version sorting
^^^^^^^^^^^^^^^

The primary customization currently is the ability to sort versions.
You can sort by:

.. TODO: Define how these work better..

* :guilabel:`SemVer (Read the Docs)` - **Default**. Read the Docs custom implementation of semver.org.
* :guilabel:`Python Packaging` - Sort by Python packaging sorting.
* :guilabel:`CalVer` - Sort by calendar date.
* :guilabel:`Alphabetically` - Only useful if you aren't using numeric versions.
* Or you can define a custom pattern

You can also choose whether ``latest`` and ``stable`` should be sorted first,
as those are special versions that Read the Docs uses.

Position
^^^^^^^^

The flyout can be configured in the :term:`dashboard` with the following positions:

- :guilabel:`Default (from theme or Read the Docs)` - **Default**. If the theme author defines a specific position for the flyout, that position will be used.
  Otherwise, the default position from Read the Docs will be used: ``Bottom right``.
- :guilabel:`Bottom left` - Show the flyout at the bottom left.
- :guilabel:`Bottom right` - Show the flyout at the bottom right.
- :guilabel:`Top left` - Show the flyout at the top left.
- :guilabel:`Top right` - Show the flyout at the top right.

.. note::

   If you are a theme author and want to define a default flyout position for your theme,
   you can explicitly define the flyout web component with the ``position`` attribute in your HTML:

   .. code:: html

     <readthedocs-flyout position="bottom-left"></readthedocs-flyout>


   Available positions: ``bottom-left``, ``bottom-right``, ``top-left`` and ``top-right``.

Custom event integration
------------------------

Read the Docs Addons exposes all the data used to construct the flyout menu via a JavaScript ``CustomEvent``.
If you'd like to integrate the data,
you can use the :ref:`intro/mkdocs:Integrate the Read the Docs version menu into your site navigation` example as a starting point.

.. warning::
   We have not formally documented the API response returned from the Addons API,
   but you can view the JSON data returned there as a starting point.
   Once we document it,
   we will commit to supporting that version of the API response going forward.
