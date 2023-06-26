How to enable canonical URLs
============================

In this guide, we introduce relevant settings for enabling canonical URLs in popular documentation frameworks.

If you need to customize the domain from which your documentation project is served,
please refer to :doc:`/guides/custom-domains`.

Sphinx
~~~~~~

If you are using :doc:`Sphinx </intro/getting-started-with-sphinx>`,
Read the Docs will automatically add a default value of the html_baseurl_ setting matching your canonical domain.

If you are using a custom ``html_baseurl`` in your ``conf.py``,
you have to ensure that the value is correct.
This can be complex,
supporting pull request builds (which are published on a separate domain),
special branches
or if you are using :term:`subproject` s or :ref:`translations <localization:Localization of Documentation>`.
We recommend not including a ``html_baseurl`` in your ``conf.py``,
and letting Read the Docs define it.

.. _html_baseurl: https://www.sphinx-doc.org/page/usage/configuration.html#confval-html_baseurl

MkDocs
~~~~~~

For :doc:`MkDocs </intro/getting-started-with-mkdocs>` we do not define your canonical domain automatically,
but you can use the site_url_ setting to set a similar value.

In your ``mkdocs.yml``, define the following:

.. code-block:: yaml

   # Canonical URL, adjust as need with respect to your slug, language,
   # default branch and if you use a custom domain.
   site_url: https://<slug>.readthedocs.io/en/stable/

Note that this will define the same canonical URL for all your branches and versions.
According to MkDocs, defining site_url_ will only define the canonical URL of a website and does not affect the base URL of generated links, CSS, or Javascript files.

.. note::

   2 known issues are currently making it impossible to use `environment variables in MkDocs configuration`_.
   Once these issues are solved, it will be easier.

   - Support for ``!ENV``: :rtd-issue:`8529`
   - Add environment variable for canonical URL: :rtd-issue:`9781`

.. _site_url: https://www.mkdocs.org/user-guide/configuration/#site_url
.. _environment variables in MkDocs configuration: https://www.mkdocs.org/user-guide/configuration/#environment-variables

.. warning::

   If you change your default version or canonical domain,
   you'll need to re-build all your versions in order to update their
   canonical URL to the new one.
