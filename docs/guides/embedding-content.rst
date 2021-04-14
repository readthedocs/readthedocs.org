Embedding Content From Your Documentation
=========================================

In this guide you'll learn how to use the :doc:`/embed-api` to embed content from projects hosted on Read the Docs.
There are a number of uses cases for embedding content,
so we've built our integration in a way that enables users to build on top of it.
This guide will show you some of our favorite integrations:

.. contents::
   :local:

Contextualized tooltips on documentation pages
----------------------------------------------

Tooltips on your own documentation are really useful to add more context to the current page the user is reading.
You can embed any content that is available via reference in Sphinx, including:

* Python object references
* Full documentation pages
* Sphinx references
* Term definitions

We built a Sphinx extension called ``sphinx-hoverxref`` on top of our Embed API
you can install in your project with minimal configuration.

Here is an example showing a tooltip when you hover with the mouse a reference:

.. figure:: /_static/images/guides/sphinx-hoverxref-example.png
   :width: 80%
   :align: center

   Tooltip shown when hovering on a reference using ``sphinx-hoverxref``.

You can find more information about this extension, how to install and configure it in the `hoverxref documentation`_.

.. _hoverxref documentation: https://sphinx-hoverxref.readthedocs.io/

Inline help on application website
----------------------------------

This allows us to keep the official documentation as the single source of truth,
while having great inline help in our application website as well.
On the "Automation Rules" admin page we could embed the content of our :doc:`/automation-rules` documentation
page and be sure it will be always up to date using the :doc:`/embed-api`.

.. note::

   We recommend you point at tagged releases instead of latest.
   Tags don't change over time, so you don't have to worry about the content you are embedding disappearing.

The following example will fetch the "Creating an automation rule" section from the ``automation-rules.html`` page of our own docs,
and will populate the content of it into the ``#help-container`` div element.

.. code-block:: html

    <script type="text/javascript">
    var params = {
      'project': 'docs',
      'version': 'stable',
      'path': 'automation-rules.html',
      'section': 'creating-an-automation-rule',
    };
    var url = 'https://readthedocs.org/api/v2/embed/?' + $.param(params);
    $.get(url, function(data) {
      $('#help-container').content(data['content']);
    });
    </script>

    <div id="help-container"></div>

You can modify this example to subscribe to ``.onclick`` JavaScript event,
and show a modal when the user clicks in a "Help" link.

.. tip::

    Take into account that if the title changes, your ``section`` argument will break.
    To avoid that, you can manually define Sphinx references above the sections you don't want to break.
    For example,

    .. code-block:: rst
       :emphasize-lines: 3

       .. in your .rst document file

       .. _unbreakable-section-reference:

       Creating an automation rule
       ---------------------------

       This is the text of the section.

    To link to the section "Creating an automation rule" you can send ``section=unbreakable-section-reference``.
    If you change the title it won't break the embedded content because the label for that title will still be ``unbreakable-section-reference``.

    Please, take a look at the Sphinx `:ref:` `role documentation`_ for more information about how to create references.

    .. _role documentation: https://www.sphinx-doc.org/en/stable/usage/restructuredtext/roles.html#role-ref
