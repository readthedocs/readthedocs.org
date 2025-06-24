How to embed content from your documentation
============================================

Read the Docs allows you to embed content from any of the projects we host and specific allowed external domains
(currently, ``docs.python.org``, ``docs.scipy.org``, ``docs.sympy.org``, ``numpy.org``)
This allows reuse of content across sites, making sure the content is always up to date.

There are a number of use cases for embedding content,
so we've built our integration in a way that enables users to build on top of it.
This guide will show you some of our favorite integrations:

.. contents::
   :local:

Contextualized tooltips on documentation pages
----------------------------------------------

Tooltips on your own documentation are really useful to add more context to the current page the user is reading.
You can embed any content that is available via an HTML id.

We built an addon called :doc:`Link previews </link-previews>` on top of our Embed API
that you can enable from the addons settings of your project using the :term:`dashboard`.

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
      'url': 'https://docs.readthedocs.io/en/latest/automation-rules.html%23creating-an-automation-rule',
      // 'doctool': 'sphinx',
      // 'doctoolversion': '4.2.0',
      // 'maincontent': 'div#main',
    };
    var url = 'https://app.readthedocs.org/api/v3/embed/?' + $.param(params);
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

    .. tabs::

       .. tab:: reStructuredText

          .. code-block:: rst
             :emphasize-lines: 3

             .. in your .rst document file

             .. _unbreakable-section-reference:

             Creating an automation rule
             ---------------------------

             This is the text of the section.

       .. tab:: MyST (Markdown)

          .. code-block:: md
             :emphasize-lines: 3

             .. in your .md document file

             (unbreakable-section-reference)=
             ## Creating an automation rule

             This is the text of the section.

    To link to the section "Creating an automation rule" you can send ``section=unbreakable-section-reference``.
    If you change the title it won't break the embedded content because the label for that title will still be ``unbreakable-section-reference``.

    Please, take a look at the Sphinx `:ref:` `role documentation`_ for more information about how to create references.

    .. _role documentation: https://www.sphinx-doc.org/en/stable/usage/restructuredtext/roles.html#role-ref


Calling the Embed API directly
------------------------------

Embed API lives under ``https://app.readthedocs.org/api/v3/embed/`` URL and accept the URL of the content you want to embed.
Take a look at :ref:`its own documentation <api/v3:embed>` to find out more details.

You can click on the following links and check a live response directly in the browser as examples:

* https://app.readthedocs.org/api/v3/embed/?url=https://docs.readthedocs.io/en/stable/features.html%23automatic-documentation-deployment
* https://app.readthedocs.org/api/v3/embed/?url=https://sphinx-hoverxref.readthedocs.io/en/latest/configuration.html%23confval-hoverxref_role_types&doctool=sphinx&doctoolversion=4.2.0
* https://app.readthedocs.org/api/v3/embed/?url=https://docs.sympy.org/latest/tutorial/gotchas.html%23equals-signs

.. note::

   All relative links to pages contained in the remote content will continue to point at the remote page.
