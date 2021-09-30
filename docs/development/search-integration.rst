Server Side Search Integration
==============================

Read the Docs provides :doc:`server side search (SSS) </server-side-search>`
in replace of the default search engine of your site.
To accomplish this, Read the Docs parses the content directly from your HTML pages [*]_.

If you are the author of a theme or a static site generator you can read this document,
and follow some conventions in order to improve the integration of SSS with your theme/site.

Indexing
--------

The content of the page is parsed into sections,
in general, the indexing process happens in three steps:

#. Identify the main content node.
#. Remove any irrelevant content from the main node.
#. Parse all sections inside the main node.

Read the Docs makes use of ARIA_ roles and other heuristics in order to process the content.

.. tip::

   Following the ARIA_ conventions will also improve the accessibility of your site.
   See also https://webaim.org/techniques/semanticstructure/.

.. _ARIA: https://www.w3.org/TR/wai-aria/

Main content node
~~~~~~~~~~~~~~~~~

The main content node should have a main role (or a ``main`` tag), and there should only be one per page.
This node is the one that contains all the page content. Example:

.. code-block:: html
   :emphasize-lines: 10-12

   <html>
      <head>
         ...
      </head>
      <body>
         <div>
            This content isn't processed
         </div>

         <div role="main">
            All content inside the main node is processed
         </div>

         <footer>
            This content isn't processed
         </footer>
      </body>
   </html>

Irrelevant content
~~~~~~~~~~~~~~~~~~

If you have content inside the main node that isn't relevant to the page
(like navigation items, menus, or search box),
make sure to use the correct role or tag for it.

Roles to be ignored:

- ``navigation``
- ``search``

Tags to be ignored:

- ``nav``

Example:

.. code-block:: html
   :emphasize-lines: 3-5

   <div role="main">
      ...
      <nav role="navigation">
         ...
      </nav>
      ...
   </div>

Sections
~~~~~~~~

Sections are ``h`` tags, and sections of the same level should be neighbors.
Additionally, sections should have an unique ``id`` attribute per page (this is used to link to the section).
All content below the section, till the new section will be indexed as part of the section. Example:

.. code-block:: html
   :emphasize-lines: 2-10

   <div role="main">
      <h1 id="section-title">
         Section title
      </h1>
      <p>
         Content to be indexed
      </p>
      <ul>
         <li>This is also part of the section and will be indexed as well</li>
      </ul>

      <h2 id="2">
         This is the start of a new section
      </h2>
      <p>
         ...
      </p>

      ...

      <h1 id="neigbor-section">
         This section is neighbor of "section-title"
      </h1>
      <p>
         ...
      </p>
   </div>

Sections can be inside till two nested tags (and have nested sections),
and its immediate parent can contain the ``id`` attribute.
Note that the section content still needs to be below the ``h`` tag. Example:

.. code-block:: html
   :emphasize-lines: 3-11,14-21

   <div role="main">
      <div class="section">
         <h1 id="section-title">
            Section title
         </h1>
         <p>
            Content to be indexed
         </p>
         <ul>
            <li>This is also part of the section</li>
         </ul>

         <div class="section">
            <div id="nested-section">
               <h2>
                  This is the start of a sub-section
               </h2>
               <p>
                  With the h tag within two levels
               </p>
            </div>
         </div>
      </div>
   </div>

.. note::

   The title of the first section will be the title of the page,
   falling back to the ``title`` tag.

Other special nodes
~~~~~~~~~~~~~~~~~~~

- **Anchors**: If the title of your section contains an anchor, wrap it in a ``headerlink`` class,
  so it won't be indexed as part of the title.

.. code-block:: html
   :emphasize-lines: 3

   <h2>
      Section title
      <a class="headerlink" title="Permalink to this headline">¶</a>
   </h2>

- **Code blocks**: If a code block contains line numbers,
  wrap them in a ``linenos`` or ``lineno`` class,
  so they won't be indexed as part of the code.

.. code-block:: html
   :emphasize-lines: 3-7

   <table class="highlighttable">
      <tr>
         <td class="linenos">
            <div class="linenodiv">
               <pre>1 2 3</pre>
            </div>
         </td>

         <td class="code">
            <div class="highlight">
               <pre>First line
   Second line
   Third line</pre>
            </div>
         </td>
      </tr>
   </table>

Overriding the default search
-----------------------------

Static sites usually have their own static index,
and search results are retrieved via JavaScript.
In order for Read the Docs to override the default search as expected,
themes from the supported generators must follow these conventions.

.. note::

   Read the Docs will fallback to the original search in case of an error or no results.

Sphinx
~~~~~~

Sphinx's basic theme provides the `static/searchtools.js`_ file,
which initializes search with the ``Search.init()`` method.
Read the Docs overrides the ``Search.query`` method and makes use of ``Search.output.append`` to add the results.
A simplified example looks like this:

.. code-block:: js

   var original_search = Search.query;

   function search_override(query) {
      var results = fetch_resuls(query);
      if (results) {
         for (var i = 0; i < results.length; i += 1) {
            var result = process_result(results[i]);
            Search.output.append(result);
         }
      } else {
         original_search(query);
      }
   }

   Search.query = search_override;

   $(document).ready(function() {
      Search.init();
   });

Highlights from results will be in a ``span`` tag with the ``highlighted`` class
(``This is a <span class="highlighted">result</span>``).
If your theme works with the search from the basic theme, it will work with Read the Docs' SSS.

.. _`static/searchtools.js`: https://github.com/sphinx-doc/sphinx/blob/275d9/sphinx/themes/basic/static/searchtools.js

MkDocs
~~~~~~

Search on MkDocs is provided by the `search plugin`_, which is included (and activated) by default in MkDocs.
The js part of this plugin is included in the `templates/search/main.js`_ file,
which subscribes to the ``keyup`` event of the ``#mkdocs-search-query`` element
to call the ``doSearch`` function (available on MkDocs >= 1.x) on every key press.

Read the Docs overrides the ``initSearch`` and ``doSearch`` functions
to subscribe to the ``keyup`` event of the ``#mkdocs-search-query`` element,
and puts the results into the ``#mkdocs-search-results`` element.
A simplified example looks like this:

.. code-block:: js

   var original_search = doSearch;

   function search_override() {
      var query = document.getElementById('mkdocs-search-query').value;
      var search_results = document.getElementById('mkdocs-search-results');

      var results = fetch_resuls(query);
      if (results) {
         empty_results(search_results)
         for (var i = 0; i < results.length; i += 1) {
            var result = process_result(results[i]);
            append_result(result, search_results);
         }
      } else {
         original_search();
      }
   }

   var init_override = function () {
      var search_input = document.getElementById('mkdocs-search-query');
      search_input.addEventListener('keyup', doSearch);
   };

   window.doSearch = search_override;
   window.initSearch = init_override;

   initSearch();

Highlights from results will be in a ``mark`` tag (``This is a <mark>result</mark>``).
If your theme works with the search plugin of MkDocs,
and defines the ``#mkdocs-search-query`` and ``#mkdocs-search-results`` elements,
it will work with Read the Docs' SSS.

.. note::

   Since the ``templates/search/main.js`` file is included after our custom search,
   it will subscribe to the ``keyup`` event too, triggering both functions when a key is pressed
   (but ours should have more precedence).
   This can be fixed by not including the ``search`` plugin (you won't be able to fallback to the original search),
   or by creating a custom plugin to include our search at the end (this should be done by Read the Docs).

.. _`search plugin`: https://www.mkdocs.org/user-guide/configuration/#search
.. _`templates/search/main.js`: https://github.com/mkdocs/mkdocs/blob/ff0b72/mkdocs/contrib/search/templates/search/main.js

Supporting more themes and static site generators
-------------------------------------------------

Currently, Read the Docs supports building documentation from
:doc:`Sphinx </intro/getting-started-with-sphinx>` and :doc:`MkDocs </intro/getting-started-with-mkdocs>`.
All themes that follow these conventions should work as expected.
If you think other generators or other conventions should be supported,
or content that should be ignored or have an especial treatment,
or if you found an error with our indexing,
let us know in `our issue tracker`_.

.. _our issue tracker: https://github.com/readthedocs/readthedocs.org/issues/

.. [*] For Sphinx projects, the content of the main node is provided by an intermediate step in the build process,
       but the HTML components from the node are preserved.
