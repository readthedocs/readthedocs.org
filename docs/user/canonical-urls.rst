Canonical URLs
==============

Canonical URLs allow you to have consistent page URLs across all your domains.
This is mainly useful for search engines,
so that they can send users to the correct version and domain of your documentation.

The canonical URL is generated based on:

* The default version of your project (usually "latest" or "stable").
* The canonical :doc:`custom domain </custom-domains>` if you have one,
  otherwise the default :ref:`subdomain <hosting:subdomain support>` will be used.

.. contents::
    :local:

Example
-------

Fabric hosts their docs on Read the Docs,
but they use their own domain ``http://docs.fabfile.org``.
This means that Google will index both ``http://fabric-docs.readthedocs.io`` and
``http://docs.fabfile.org`` for their documentation.

Fabric will want to set ``http://docs.fabfile.org`` as their canonical domain,
this means that when Google indexes ``http://fabric-docs.readthedocs.io``,
it will know that it should really point at ``http://docs.fabfile.org``.

Implementation
--------------

If you are using :doc:`Sphinx </intro/getting-started-with-sphinx>`,
Read the Docs will set the value of the html_baseurl_ setting (if isn't already set) to your canonical domain.

.. _html_baseurl: https://www.sphinx-doc.org/page/usage/configuration.html#confval-html_baseurl

For :doc:`MkDocs </intro/getting-started-with-mkdocs>` this isn't done automatically,
but you can use the site_url_ setting.

.. _site_url: https://www.mkdocs.org/user-guide/configuration/#site_url

If you look at the source code for the documentation built after you set your canonical URL,
you should see a bit of HTML like this:

.. code-block:: html

   <link rel="canonical" href="http://docs.fabfile.org/en/2.4/" />

.. note::

   If you change your default version or canonical domain,
   you'll need to re-build all your versions in order to update their
   canonical URL to the new one.
