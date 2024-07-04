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

In your dashboard, you can configure flyout menu options in :guilabel:`Settings`, under :guilabel:`Addons (Beta)`.

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
* Links to your :doc:`VCS provider </integrations>` that allow the user to quickly find the exact file that the documentation was rendered from.
* A search bar that gives users access to our :doc:`/server-side-search/index` of the current version.

.. figure:: /_static/images/flyout-open.png
   :align: center

   The opened flyout

Information for theme authors
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. warning::

   The original flyout menu could be themed by injecting code with JavaScript.
   This approach is currently *deprecated* in favor of the new Read the Docs Addons approach.

People who are making custom documentation themes often want to specify where the flyout is injected,
and also what it looks like.
We support both of these use cases for themes.

[Deprecated] Defining where the flyout menu is injected
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The flyout menu injection looks for a specific selector (``#readthedocs-embed-flyout``),
in order to inject the flyout.
You can add ``<div id="readthedocs-embed-flyout">`` in your theme,
and our JavaScript code will inject the flyout there.
All other themes except for the ``sphinx_rtd_theme`` have the flyout appended to the ``<body>``.

[Deprecated] Styling the flyout
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

HTML themes can style the flyout to make it match the overall style of the HTML.
By default the flyout has it's `own CSS file <https://github.com/readthedocs/sphinx_rtd_theme/blob/master/src/sass/_theme_badge.sass>`_,
which you can look at to see the basic CSS class names.

The example HTML that the flyout uses is included here,
so that you can style it in your HTML theme:

.. code:: html

    <div class="injected">
       <div class="rst-versions rst-badge shift-up" data-toggle="rst-versions">
          <span class="rst-current-version" data-toggle="rst-current-version">
          <span class="fa fa-book">&nbsp;</span>
          v: 2.1.x
          <span class="fa fa-caret-down"></span>
          </span>
          <div class="rst-other-versions">
             <!-- "Languages" section (``dl`` tag) is not included if the project does not have translations -->
             <dl>
                <dt>Languages</dt>
                <dd class="rtd-current-item">
                   <a href="https://flask.palletsproject.com/en/2.1.x">en</a>
                </dd>
                <dd>
                   <a href="https://flask.palletsproject.com/es/2.1.x">es</a>
                </dd>
             </dl>

             <!-- "Versions" section (``dl`` tag) is not included if the project is single version -->
             <dl>
                <dt>Versions</dt>
                <dd>
                   <a href="https://flask.palletsprojects.com/en/latest/">latest</a>
                </dd>
                <dd class="rtd-current-item">
                   <a href="https://flask.palletsprojects.com/en/2.1.x/">2.1.x</a>
                </dd>
             </dl>

             <!-- "Downloads" section (``dl`` tag) is not included if the project does not have artifacts to download -->
             <dl>
                <dt>Downloads</dt>
                <dd>
                   <a href="//flask.palletsprojects.com/_/downloads/en/2.1.x/pdf/">PDF</a>
                 </dd>
                <dd>
                   <a href="//flask.palletsprojects.com/_/downloads/en/2.1.x/htmlzip/">HTML</a>
                 </dd>
             </dl>

             <dl>
                <dt>On Read the Docs</dt>
                <dd>
                   <a href="//readthedocs.org/projects/flask/">Project Home</a>
                </dd>
                <dd>
                   <a href="//readthedocs.org/projects/flask/builds/">Builds</a>
                </dd>
                <dd>
                   <a href="//readthedocs.org/projects/flask/downloads/">Downloads</a>
                </dd>
             </dl>

             <dl>
                <dt>On GitHub</dt>
                <dd>
                   <a href="https://github.com/pallets/flask/blob/2.1.x/docs/index.rst">View</a>
                </dd>
                <dd>
                   <a href="https://github.com/pallets/flask/edit/2.1.x/docs/index.rst">Edit</a>
                </dd>
             </dl>

             <dl>
                <dt>Search</dt>
                <dd>
                   <div style="padding: 6px;">
                      <form id="flyout-search-form" class="wy-form" target="_blank" action="//readthedocs.org/projects/flask/search/" method="get">
                         <input type="text" name="q" aria-label="Search docs" placeholder="Search docs">
                      </form>
                   </div>
                </dd>
             </dl>

             <hr>
             <small>
             <span>Hosted by <a href="https://readthedocs.org">Read the Docs</a></span>
             <span> &middot; </span>
             <a href="https://docs.readthedocs.io/page/privacy-policy.html">Privacy Policy</a>
             </small>
          </div>
       </div>
    </div>
