Server side search integration
==============================

Read the Docs provides :doc:`server side search (SSS) <rtd:server-side-search/index>`
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

The main content should be inside a ``<main>`` tag or an element with ``role=main``,
and there should only be one per page.
This node is the one that contains all the page content to be indexed. Example:

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

If a main node isn't found,
we try to infer the main node from the parent of the first section with a ``h1`` tag.
Example:

.. code-block:: html
   :emphasize-lines: 10-20

   <html>
      <head>
         ...
      </head>
      <body>
         <div>
            This content isn't processed
         </div>

         <div id="parent">
            <h1>First title</h1>
            <p>
               The parent of the h1 title will
               be taken as the main node,
               this is the div tag.
            </p>

            <h2>Second title</h2>
            <p>More content</p>
         </div>
      </body>
   </html>

If a section title isn't found, we default to the ``body`` tag.
Example:

.. code-block:: html
   :emphasize-lines: 5-7

   <html>
      <head>
         ...
      </head>
      <body>
         <p>Content</p>
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

Special rules that are derived from specific documentation tools applied in the generic parser:

.. https://squidfunk.github.io/mkdocs-material/reference/code-blocks/#adding-line-numbers

- ``.linenos``, ``.lineno`` (line numbers in code-blocks, comes from both MkDocs and Sphinx)
- ``.headerlink`` (added by Sphinx to links in headers)
- ``.toctree-wrapper`` (added by Sphinx to the table of contents generated from the ``toctree`` directive)

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

Sections are stored in a dictionary composed of an ``id``, ``title`` and ``content`` key.

Sections are defined as:

* ``h1-h7``, all content between one heading level and the next header on the same level is used as content for that section.
* ``dt`` elements with an ``id`` attribute, we map the ``title`` to the ``dt`` element and the content to the ``dd`` element.

All sections have to be identified by a DOM container's ``id`` attribute,
which will be used to link to the section.
How the id is detected varies with the type of element:

* ``h1-h7`` elements use the ``id`` attribute of the header itself if present, or
  its ``section`` parent (if exists).
* ``dt`` elements use the ``id`` attribute of the ``dt`` element.

To avoid duplication and ambiguous section references,
all indexed ``dl`` elements are removed from the DOM before indexing of other sections happen.

Here is an example of how all content below the title,
until a new section is found,
will be indexed as part of the section content:

.. code-block:: html
   :emphasize-lines: 2-10, 12-17, 21-26

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

      <header>
         <h1 id="3">This is also a valid section title</h1>
      </header>
      <p>
         This is the content of the third section.
      </p>
   </div>

Sections can be contained in up to two nested tags, and can contain other sections (nested sections).
Note that the section content still needs to be below the section title.
Example:

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

Static sites usually have their own static search index, and search results are retrieved via JavaScript.
Read the Docs overrides the default search for Sphinx projects only,
and provides a fallback to the original search in case of an error or no results.

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

Other static site generators
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

All projects that have HTML pages that follow the conventions described in this document
can make use of the server side search from the dashboard or by calling the API.

Supporting more themes and static site generators
-------------------------------------------------

All themes that follow these conventions should work as expected.
If you think other generators or other conventions should be supported,
or content that should be ignored or have an especial treatment,
or if you found an error with our indexing,
let us know in `our issue tracker`_.

.. _our issue tracker: https://github.com/readthedocs/readthedocs.org/issues/

.. [*] For Sphinx projects, the content of the main node is provided by an intermediate step in the build process,
       but the HTML components from the node are preserved.
