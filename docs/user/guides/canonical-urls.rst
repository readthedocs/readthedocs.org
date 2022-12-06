How to enable Canonical URLs
============================

Sphinx
~~~~~~

If you are using :doc:`Sphinx </intro/getting-started-with-sphinx>`,
Read the Docs will set the value of the html_baseurl_ setting (if isn't already set) to your canonical domain.
If you already have ``html_baseurl`` set, you need to ensure that the value is correct.

.. _html_baseurl: https://www.sphinx-doc.org/page/usage/configuration.html#confval-html_baseurl

MkDocs
~~~~~~

For :doc:`MkDocs </intro/getting-started-with-mkdocs>` this isn't done automatically,
but you can use the site_url_ setting to set a similar value.

.. _site_url: https://www.mkdocs.org/user-guide/configuration/#site_url

.. warning::

   If you change your default version or canonical domain,
   you'll need to re-build all your versions in order to update their
   canonical URL to the new one.
