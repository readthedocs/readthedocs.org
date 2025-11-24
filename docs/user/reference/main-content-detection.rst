Main content detection
======================

Read the Docs detects the main content area of HTML pages
to focus on the documentation content itself,
ignoring headers, footers, navigation, and other page elements.

This detection is used by features like :doc:`/visual-diff` and :doc:`/server-side-search/index`
to ensure accurate comparison and indexing of your documentation.

Detection logic
---------------

The main content node is detected using the following logic, in order of priority:

#. **Elements with** ``role="main"`` **attribute**: This ARIA role is used by many static site generators and themes to indicate the main content area.
#. **The** ``<main>`` **HTML tag**: The semantic HTML5 element for main content.
#. **Parent of the first** ``<h1>`` **tag**: If no explicit main content markers are found, the system assumes all sections are siblings under a common parent, and uses the parent of the first heading as the main content container.
#. **The** ``<body>`` **tag**: As a last resort, if none of the above are found, the entire body is used.

.. tip::

   Following the ARIA_ conventions will also improve the accessibility of your site.
   See also https://webaim.org/techniques/semanticstructure/.

.. _ARIA: https://www.w3.org/TR/wai-aria/

Improving detection
-------------------

If your documentation uses a non-standard structure,
Read the Docs may not correctly identify the main content area.

To improve detection, consider:

- Adding a ``role="main"`` attribute to your main content container
- Using a ``<main>`` HTML tag in your theme
- Ensuring your main content has at least one ``<h1>`` heading

Example structures
------------------

Using role="main" or <main> tag
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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

Inferring from first h1 tag
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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

Fallback to body tag
~~~~~~~~~~~~~~~~~~~~

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
