How to Enable Canonical URLs
============================

In this guide, we introduce relevant settings for enabling canonical URLs in popular documentation frameworks.

.. seealso::

   If you want to customize the domain from which your documentation project is served, please refer to :doc:`/guides/custom-domains`.

Sphinx
~~~~~~

If you are using :doc:`Sphinx </intro/getting-started-with-sphinx>`,
Read the Docs will automatically add a default value of the html_baseurl_ setting matching your canonical domain.

If you have defined ``html_baseurl`` in your ``conf.py``, you need to ensure that the value is correct.

.. _html_baseurl: https://www.sphinx-doc.org/page/usage/configuration.html#confval-html_baseurl

MkDocs
~~~~~~

For :doc:`MkDocs </intro/getting-started-with-mkdocs>` we do not define your canonical domain automatically,
but you can use the site_url_ setting to set a similar value.

.. _site_url: https://www.mkdocs.org/user-guide/configuration/#site_url

.. warning::

   If you change your default version or canonical domain,
   you'll need to re-build all your versions in order to update their
   canonical URL to the new one.
