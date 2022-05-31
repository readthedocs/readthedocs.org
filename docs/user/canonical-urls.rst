Canonical URLs
==============

`Canonical URLs`_ allow you to specify the preferred version of a web page to prevent duplicated content.
They are mainly used by search engines to link users to the correct
version and domain of your documentation.

.. _Canonical URLs: https://datatracker.ietf.org/doc/html/rfc6596

.. contents:: Contents
    :local:

Example
-------

The canonical URL is generated based on:

* The default version of your project (usually "latest" or "stable").
* The canonical :doc:`custom domain </custom-domains>` if you have one,
  otherwise the default :ref:`subdomain <hosting:subdomain support>` will be used.

For example, if you have a project named ``docs``
with a custom domain ``https://docs.example.com``.
A search engine like Google will index both domains, ``http://docs.readthedocs.io`` and
``https://docs.example.com``.

But you'll want to use ``https://docs.example.com`` as your canonical domain,
this means that when Google indexes a page like ``https://docs.readthedocs.io/en/9.0/``,
it will know that it should really point at ``https://docs.example.com/en/latest/``.

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

.. warning::

   If you change your default version or canonical domain,
   you'll need to re-build all your versions in order to update their
   canonical URL to the new one.
