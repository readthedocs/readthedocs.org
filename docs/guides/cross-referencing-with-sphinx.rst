Cross-referencing with Sphinx
=============================

When writing documentation you often need to link to other pages of your documentation,
or other sections of the current page, or sections from other pages.

.. _target to paragraph:

An easy way is just to use the final link of the page/section.
This works, but it has some disadvantages:

- Links can change, so they are hard to maintain.
- Links can be verbose, not easy to know the page/section they are linking to.
- Not easy way to link to specific sections like paragraphs, figures, or code blocks.
- It only works for the html version of your documentation.

ReStructuredText has a built-in way to linking to elements,
and Sphinx extends this to make it even more powerful!
Some advantages of using reStructuredText's references:

- Use a name instead of the final link.
- Portable between formats: html, PDF, ePub.
- Sphinx will warn you of invalid references.
- Cross reference to more than just pages and sections.

.. contents:: Table of contents
   :local:
   :backlinks: none
   :depth: 3

.. _My target:

Explicit targets
----------------

If you are not familiar with reStructuredText,
check :doc:`sphinx:usage/restructuredtext/basics` for a quick introduction.

In reStructuredText we have targets and references,
where the target is the place where a reference links to.

We can reference to any part of a document by adding a target
in the line before the element we want to link to.
For example, one way of creating a target to a section is:

.. code-block:: rst

   .. _My target:

   Explicit targets
   ----------------

Then we can reference the section using ```My target`_``,
that will be rendered as `My target`_.

Another example, a target to a paragraph:

.. code-block:: rst

   .. _target to paragraph:

   An easy way is just to use the final link of the page/section.
   This works, but it has some disadvantages:

Then we can reference it using ```target to paragraph`_``,
that will be rendered as: `target to paragraph`_.

The reference displays the name of the target by default,
but we can change that with any text
```my custom text <target to paragraph>`_``,
that will be rendered as: `my custom text <target to paragraph>`_.

We can also reference to a place *inside* an element,
this can be done with an _`inline target`.
For example, a target inside a paragraph:

.. code-block:: rst

   We can also reference to a place *inside* an element,
   this can be done with an _`inline target`.

Then we can reference it using ```inline target`_``,
that will be rendered as: `inline target`_.

Implicit targets
----------------

When we create a section,
reStructuredText will create a target with the title as the name.
For example, to reference to the previous section we can use ```Explicit targets`_``,
that will be rendered as: `Explicit targets`_.

.. note::

   `Footnotes <https://docutils.sourceforge.io/docs/user/rst/quickref.html#footnotes>`_ and
   `citations <https://docutils.sourceforge.io/docs/user/rst/quickref.html#citations>`_
   also create implicit targets.

Cross-referencing using roles
-----------------------------

All targets that we have seen so far can be referenced only from the same page.
Sphinx provides some roles that allows us to reference any explicit target from any page.

.. note::

   Since Sphinx will make all explicit targets available globally,
   all targets must be unique.

You can see the complete list of cross-referencing roles at :ref:`sphinx:xref-syntax`.
Next we will explore the most common ones.

The ref role
~~~~~~~~~~~~

The ``ref`` role can be used to reference any explicit target.

.. code-block:: rst

   - :ref:`my target`.
   - :ref:`Target to paragraph <target to paragraph>`.
   - :ref:`Target inside a paragraph <inline target>`.

That will be rendered as:

- :ref:`my target`.
- :ref:`Target to paragraph <target to paragraph>`.
- :ref:`Target inside a paragraph <inline target>`.

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

The `doc` role allow us to link to a page instead of just a section.
The target name can be a relative or absolute path (without the extension),
for example to link to a page in the same directory as this one we can use:

.. code-block:: rst

   - :doc:`intersphinx`
   - :doc:`/guides/intersphinx`
   - :doc:`Custom title </guides/intersphinx>`

That will be rendered as:

- :doc:`intersphinx`
- :doc:`/guides/intersphinx`
- :doc:`Custom title </guides/intersphinx>`

.. tip::

   Using an absolute path is recommend,
   so we avoid changing the target when the section or page are moved.

The numref role
~~~~~~~~~~~~~~~

The ``numref`` role is used to reference tables and images.
Add this to your ``conf.py`` file:

.. code-block:: python

   # Enable numref
   numfig = True

In order to use this role we need to create an explicit target to the element.
For example, we can create a target for the next image:

.. _target to image:

.. figure:: /img/logo.png
   :alt: Logo
   :align: center
   :width: 240px

   Link me!

.. code-block:: rst

   .. _target to image:

   .. figure:: /img/logo.png
      :alt: Logo
      :align: center
      :width: 240px

      Link me!

Then we can reference it using ``:numref:`target to image```,
that will be rendered as :numref:`target to image`.
Sphinx will enumerate the image automatically.

Auto section label
------------------

Adding an explicit target on each section and making sure is unique is a big task!
But Sphinx includes an extension to help us with that problem,
:doc:`autosectionlabel <sphinx:usage/extensions/autosectionlabel>`.

Add this to your ``conf.py`` file:

.. _target to code:

.. code-block:: python

   # Add the extension
   extensions = [
      'sphinx.ext.autosectionlabel',
   ]

   # Make sure the target is unique
   autosectionlabel_prefix_document = True

Sphinx will create explicit targets for all your sections,
the name of target is the path of the file (without extension) plus the title of the section.

For example, we can reference the previous section using:

.. code-block:: rst

   - :ref:`guides/cross-referencing-with-sphinx:explicit targets`.
   - :ref:`Custom title <guides/cross-referencing-with-sphinx:explicit targets>`.

That will be rendered as:

- :ref:`guides/cross-referencing-with-sphinx:explicit targets`.
- :ref:`Custom title <guides/cross-referencing-with-sphinx:explicit targets>`.

Invalid targets
---------------

If we reference an invalid or undefined target Sphinx will warn us.
You can use the :option:`-W <sphinx:sphinx-build.-W>` option when building your docs
to fail the build if there are any invalid references.
On Read the Docs you can use the :ref:`config-file/v2:sphinx.fail_on_warning` option.

Finding the reference name
--------------------------

Using names is more descriptive than using a raw link,
but is still hard to find the correct reference name of an element.

Sphinx allows you to explore all targets with:

.. prompt:: bash

   python -m sphinx.ext.intersphinx <link>

Where the link is the link or local path to your inventory file
(``usually in _build/html/objects.inv``).
For example, to see all target from the Read the Docs documentation:

.. prompt:: bash

   python -m sphinx.ext.intersphinx https://docs.readthedocs.io/en/stable/objects.inv

More
----

You can reference to docs outside your project too! See :doc:`/guides/intersphinx`.
