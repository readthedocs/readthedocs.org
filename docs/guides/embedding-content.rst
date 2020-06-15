Embedding Content From Your Documentation
=========================================

Read the Docs allows you to embed content from any of the projects we host.
This allows reuse of content across sites, making sure the content is always up to date.

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
page and be sure it will be always up to date.

.. note::

   We recommend you point at tagged releases instead of latest.
   Tags don't change over time, so you don't have to worry about the content you are embedding disappearing.

The following example will fetch the section "Creating an automation rule" in page ``automation-rules.html``
from our own docs and will populate the content of it into the ``#help-container`` div element.

.. code-block:: html

    <script type="text/javascript">
    var params = {
      'project': 'docs',
      'version': 'stable',
      'doc': 'automation-rules',
      'section': 'creating-an-automation-rule',
    };
    var url = 'https://readthedocs.org/api/v2/embed/?' + $.param(params);
    $.get(url, function(data) {
      $('#help-container').content(data['content']);
    });
    </script>

    <div id="help-container"></div>

You can modify this example to subscribe to ``.onclick`` Javascript event,
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


Calling the Embed API directly
------------------------------

Embed API lives under ``https://readthedocs.org/api/v2/embed/`` URL and accept two different ways of using it:

* passing the exact URL of the section you want to embed
* sending all the attributes required as GET arguments

The following links return exactly the same response, however the first one passes the ``url`` attribute
and the second example sends ``project``, ``version``, ``doc``, ``section`` and ``path`` as different attributes.
You can use the one that works best for your use case.

* https://readthedocs.org/api/v2/embed/?url=https://docs.readthedocs.io/en/latest/features.html%23automatic-documentation-deployment
* https://readthedocs.org/api/v2/embed/?project=docs&version=latest&doc=features&section=automatic-documentation-deployment&path=features.html

You can click on these links and check the response directly in the browser.

.. note::

   All relative links to pages contained in the remote content will continue to point at the remote page.
