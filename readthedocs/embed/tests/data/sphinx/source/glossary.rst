Glossary
========

.. glossary::

   builder
      A class (inheriting from :class:`~sphinx.builders.Builder`) that takes
      parsed documents and performs an action on them.  Normally, builders
      translate the documents to an output format, but it is also possible to
      use builders that e.g. check for broken links in the documentation, or
      build coverage information.

      See :doc:`/usage` for an overview over Sphinx's built-in
      builders.

   configuration directory
      The directory containing :file:`conf.py`.  By default, this is the same as
      the :term:`builder`, but can be set differently with the **-c**
      command-line option.

   directive
      A reStructuredText markup element that allows marking a block of content
      with special meaning.  Directives are supplied not only by docutils, but
      Sphinx and custom extensions can add their own.  The basic directive
      syntax looks like this:

      .. sourcecode:: rst

         .. directivename:: argument ...
            :option: value

            Content of the directive.

      See :ref:`index:Another title` for more information.

   environment
      A structure where information about all documents under the root is saved,
      and used for cross-referencing.  The environment is pickled after the
      parsing stage, so that successive runs only need to read and parse new and
      changed documents.
