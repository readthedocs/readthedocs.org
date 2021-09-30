Cross-referencing with Sphinx
=============================

When writing documentation you often need to link to other pages of your documentation,
other sections of the current page, or sections from other pages.

.. _target to paragraph:

An easy way is just to use the raw URL that Sphinx generates for each page/section.
This works, but it has some disadvantages:

- Links can change, so they are hard to maintain.
- Links can be verbose and hard to read, so it is unclear what page/section they are linking to.
- There is no easy way to link to specific sections like paragraphs, figures, or code blocks.
- URL links only work for the html version of your documentation.

Instead, Sphinx offers a powerful way to linking to the different elements of the document,
called *cross-references*.
Some advantages of using them:

- Use a human-readable name of your choice, instead of a URL.
- Portable between formats: html, PDF, ePub.
- Sphinx will warn you of invalid references.
- You can cross reference more than just pages and section headers.

This page describes some best-practices for cross-referencing with Sphinx
with two markup options: reStructuredText and MyST (Markdown).

- If you are not familiar with reStructuredText,
  check :doc:`sphinx:usage/restructuredtext/basics` for a quick introduction.
- If you want to learn more about the MyST Markdown dialect,
  check out :doc:`myst-parser:syntax/syntax`.

.. contents:: Table of contents
   :local:
   :backlinks: none
   :depth: 3

Getting started
---------------

.. _My target:

Explicit targets
~~~~~~~~~~~~~~~~

Cross referencing in Sphinx uses two components, **references** and **targets**.

- **references** are pointers in your documentation to other parts of your documentation.
- **targets** are where the references can point to.

You can manually create a *target* in any location of your documentation, allowing
you to *reference* it from other pages. These are called **explicit targets**.

For example, one way of creating an explicit target for a section is:

.. tabs::

   .. tab:: reStructuredText

      .. code-block:: rst

         .. _My target:

         Explicit targets
         ~~~~~~~~~~~~~~~~

         Reference `My target`_.

   .. tab:: MyST (Markdown)

      .. code-block:: md

         (My_target)=
         ## Explicit targets

         Reference [](My_target).

Then the reference will be rendered as `My target`_.

You can also add explicit targets before paragraphs (or any other part of a page).

Another example, add a target to a paragraph:

.. tabs::

   .. tab:: reStructuredText

      .. code-block:: rst

         .. _target to paragraph:

         An easy way is just to use the final link of the page/section.
         This works, but it has :ref:`some disadvantages <target to paragraph>`:

   .. tab:: MyST (Markdown)

      .. code-block:: md

         (target_to_paragraph)=

         An easy way is just to use the final link of the page/section.
         This works, but it has [some disadvantages](target_to_paragraph):

Then the reference will be rendered as: `target to paragraph`_.

You can also create _`in-line targets` within an element on your page,
allowing you to, for example, reference text *within* a paragraph.

For example, an in-line target inside a paragraph:

.. tabs::

   .. tab:: reStructuredText

      .. code-block:: rst

         You can also create _`in-line targets` within an element on your page,
         allowing you to, for example, reference text *within* a paragraph.

Then you can reference it using ```in-line targets`_``,
that will be rendered as: `in-line targets`_.

Implicit targets
~~~~~~~~~~~~~~~~

You may also reference some objects by name
without explicitly giving them one
by using *implicit targets*.

When you create a section, a footnote, or a citation,
Sphinx will create a target with the title as the name:

.. tabs::

   .. tab:: reStructuredText

      .. code-block:: rst

         For example, to reference the previous section
         you can use `Explicit targets`_.

   .. tab:: MyST (Markdown)

      .. code-block:: md

         For example, to reference the previous section
         you can use [](#explicit-targets).

      .. note::

         This requires setting ``myst_heading_anchors = 2`` in your ``conf.py``,
         see :ref:`myst-parser:syntax/header-anchors`.

The reference will be rendered as: `Explicit targets`_.

Cross-referencing using roles
-----------------------------

All targets seen so far can be referenced only from the same page.
Sphinx provides some roles that allow you to reference any explicit target from any page.

.. note::

   Since Sphinx will make all explicit targets available globally,
   all targets must be unique.

You can see the complete list of cross-referencing roles at :ref:`sphinx:xref-syntax`.
Next, you will explore the most common ones.

The ref role
~~~~~~~~~~~~

The ``ref`` role can be used to reference any explicit targets. For example:

.. tabs::

   .. tab:: reStructuredText

      .. code-block:: rst

         - :ref:`my target`.
         - :ref:`Target to paragraph <target to paragraph>`.
         - :ref:`Target inside a paragraph <in-line targets>`.

   .. tab:: MyST (Markdown)

      .. code-block:: md

         - {ref}`my target`.
         - {ref}`Target to paragraph <target_to_paragraph>`.

That will be rendered as:

- :ref:`my target`.
- :ref:`Target to paragraph <target to paragraph>`.
- :ref:`Target inside a paragraph <in-line targets>`.

The ``ref`` role also allow us to reference code blocks:

.. code-block:: rst

   .. _target to code:

   .. code-block:: python

      # Add the extension
      extensions = [
         'sphinx.ext.autosectionlabel',
      ]

      # Make sure the target is unique
      autosectionlabel_prefix_document = True

We can reference it using ``:ref:`code <target to code>```,
that will be rendered as: :ref:`code <target to code>`.

The doc role
~~~~~~~~~~~~

The ``doc`` role allows us to link to a page instead of just a section.
The target name can be relative to the page where the role exists, or relative
to your documentation's root folder (in both cases, you should omit the extension).

For example, to link to a page in the same directory as this one you can use:

.. tabs::

   .. tab:: reStructuredText

      .. code-block:: rst

         - :doc:`intersphinx`
         - :doc:`/guides/intersphinx`
         - :doc:`Custom title </guides/intersphinx>`

   .. tab:: MyST (Markdown)

      .. code-block:: md

         - {doc}`intersphinx`
         - {doc}`/guides/intersphinx`
         - {doc}`Custom title </guides/intersphinx>`

That will be rendered as:

- :doc:`intersphinx`
- :doc:`/guides/intersphinx`
- :doc:`Custom title </guides/intersphinx>`

.. tip::

   Using paths relative to your documentation root is recommended,
   so you avoid changing the target name if the page is moved.

The numref role
~~~~~~~~~~~~~~~

The ``numref`` role is used to reference **numbered** elements of your documentation.
For example, tables and images.

To activate numbered references, add this to your ``conf.py`` file:

.. code-block:: python

   # Enable numref
   numfig = True

Next, ensure that an object you would like to reference has an explicit target.

For example, you can create a target for the next image:

.. _target to image:

.. figure:: /img/logo.png
   :alt: Logo
   :align: center
   :width: 240px

   Link me!

.. tabs::

   .. tab:: reStructuredText

      .. code-block:: rst

         .. _target to image:

         .. figure:: /img/logo.png
            :alt: Logo
            :align: center
            :width: 240px

            Link me!

   .. tab:: MyST (Markdown)

      .. code-block:: md

         (target_to_image)=

         ```{figure} /img/logo.png
         :alt: Logo
         :align: center
         :width: 240px
         ```

Finally, reference it using ``:numref:`target to image```,
that will be rendered as ``Fig. N``.
Sphinx will enumerate the image automatically.

Automatically label sections
----------------------------

Manually adding an explicit target to each section and making sure is unique
is a big task! Fortunately, Sphinx includes an extension to help us with that problem,
:doc:`autosectionlabel <sphinx:usage/extensions/autosectionlabel>`.

To activate the ``autosectionlabel`` extension, add this to your ``conf.py`` file:

.. _target to code:

.. code-block:: python

   # Add the extension
   extensions = [
      'sphinx.ext.autosectionlabel',
   ]

   # Make sure the target is unique
   autosectionlabel_prefix_document = True

Sphinx will create explicit targets for all your sections,
the name of target has the form ``{path/to/page}:{title-of-section}``.

For example, you can reference the previous section using:

.. tabs::

   .. tab:: reStructuredText

      .. code-block:: rst

         - :ref:`guides/cross-referencing-with-sphinx:explicit targets`.
         - :ref:`Custom title <guides/cross-referencing-with-sphinx:explicit targets>`.

   .. tab:: MyST (Markdown)

      .. code-block:: md

         - {ref}`guides/cross-referencing-with-sphinx:explicit targets`.
         - {ref}`Custom title <guides/cross-referencing-with-sphinx:explicit targets>`.

That will be rendered as:

- :ref:`guides/cross-referencing-with-sphinx:explicit targets`.
- :ref:`Custom title <guides/cross-referencing-with-sphinx:explicit targets>`.

Invalid targets
---------------

If you reference an invalid or undefined target Sphinx will warn us.
You can use the :option:`-W <sphinx:sphinx-build.-W>` option when building your docs
to fail the build if there are any invalid references.
On Read the Docs you can use the :ref:`config-file/v2:sphinx.fail_on_warning` option.

Finding the reference name
--------------------------

When you build your documentation, Sphinx will generate an inventory of all
explicit and implicit links called ``objects.inv``. You can list all of these targets to
explore what is available for you to reference.

List all targets for built documentation with:

.. prompt:: bash

   python -m sphinx.ext.intersphinx <link>

Where ``<link>`` is either a URL or a local path that points to your inventory file
(usually in ``_build/html/objects.inv``).
For example, to see all targets from the Read the Docs documentation:

.. prompt:: bash

   python -m sphinx.ext.intersphinx https://docs.readthedocs.io/en/stable/objects.inv

Cross-referencing targets in other documentation sites
------------------------------------------------------

You can reference to docs outside your project too! See :doc:`/guides/intersphinx`.
