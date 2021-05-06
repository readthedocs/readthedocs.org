Embed API
=========

Read the Docs allows you to embed content from any of the projects we host.
This allows reuse of content across sites, making sure the content is always up to date.

.. contents::
   :local:

Usage
-----

Check our :doc:`/guides/embedding-content` guide to learn how to use the embed API in your projects.
Additionally, you can use the API with:

- `sphinx-hoverxref`_: Sphinx extension

.. _sphinx-hoverxref: https://sphinx-hoverxref.readthedocs.io

API
---

The embed API is exposed from the domain where your docs are being served.
This is ``https://docs.readthedocs.io/_/api/v2/embed`` for the ``docs`` project, for example.

.. warning::

   This API isn't stable yet, feel free to `open an issue`_ if you find any problems.
   Only Sphinx projects are supported at the moment,
   a new version of this API with more general support is on the way!

   .. _open an issue: https://github.com/readthedocs/readthedocs.org/issues/new

.. http:get:: /_/api/v2/embed/

   Return the content of a section with all links rewritten to be absolute.
   There are two ways of using the API

   Using the project and version slug.

   .. Request

   :query project: Project slug
   :query version: Version slug
   :query path: Path of file
   :query section: Section ID

   Using the URL.

   :query url: Full URL with fragment

   .. Response

   :>json array content: A single element array with the HTML content of the section
   :>json array headers: A list of mappings of titles to IDs (with leading ``#``)
   :>json string url: Full URL to the section
   :>json object meta: Metadata about the section:

    - project: project slug
    - version: version slug
    - doc: Sphinx document name
    - section: ID of the section (without leading ``#``)

   **Example request**:

   .. tabs::

      .. code-tab:: bash

         $ curl "https://docs.readthedocs.io/_/api/v2/embed/?project=docs&version=latest&path=badges.html&section=style"

      .. code-tab:: python

         import requests
         URL = 'https://docs.readthedocs.io/_/api/v2/embed/'
         params = {
            'project': 'docs',
            'version': 'latest',
            'path': 'badges.html',
            'section': 'style',
         }
         response = requests.get(URL, params=params)
         print(response.json())

   **Example response**:

   .. sourcecode:: json

      {
         "content": [
            "<div class=\"section\" id=\"style\">\n<h2>Style<a class=\"headerlink\" href=\"https://docs.readthedocs.io/en/latest/badges.html#style\" title=\"Permalink to this headline\">¶</a></h2>\n<p>Now you can pass the <code class=\"docutils literal notranslate\"><span class=\"pre\">style</span></code> GET argument,\nto get custom styled badges same as you would for shields.io.\nIf no argument is passed, <code class=\"docutils literal notranslate\"><span class=\"pre\">flat</span></code> is used as default.</p>\n<table class=\"docutils align-default\">\n<colgrouisp>\n<col style=\"width: 42%\">\n<col style=\"width: 58%\">\n</colgroup>\n<thead>\n<tr class=\"row-odd\"><th class=\"head\"><p>STYLE</p></th>\n<th class=\"head\"><p>BADGE</p></th>\n</tr>\n</thead>\n<tbody>\n<tr class=\"row-even\"><td><p>flat</p></td>\n<td><p><img alt=\"Flat Badge\" src=\"https://readthedocs.org/projects/pip/badge/?version=latest&amp;style=flat\"></p></td>\n</tr>\n<tr class=\"row-odd\"><td><p>flat-square</p></td>\n<td><p><img alt=\"Flat-Square Badge\" src=\"https://readthedocs.org/projects/pip/badge/?version=latest&amp;style=flat-square\"></p></td>\n</tr>\n<tr class=\"row-even\"><td><p>for-the-badge</p></td>\n<td><p><img alt=\"Badge\" src=\"https://readthedocs.org/projects/pip/badge/?version=latest&amp;style=for-the-badge\"></p></td>\n</tr>\n<tr class=\"row-odd\"><td><p>plastic</p></td>\n<td><p><img alt=\"Plastic Badge\" src=\"https://readthedocs.org/projects/pip/badge/?version=latest&amp;style=plastic\"></p></td>\n</tr>\n<tr class=\"row-even\"><td><p>social</p></td>\n<td><p><img alt=\"Social Badge\" src=\"https://readthedocs.org/projects/pip/badge/?version=latest&amp;style=social\"></p></td>\n</tr>\n</tbody>\n</table>\n</div>"
         ],
         "headers": [
            {
                  "Badges": "#"
            },
            {
                  "Status Badges": "#status-badges"
            },
            {
                  "Style": "#style"
            },
            {
                  "Project Pages": "#project-pages"
            }
         ],
         "url": "https://docs.readthedocs.io/en/latest/badges.html",
         "meta": {
            "project": "docs",
            "version": "latest",
            "doc": "badges",
            "section": "style"
         }
      }

Authentication and authorization
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you are using :ref:`private versions <versions:privacy levels>`,
users will only be allowed to get the embed content from projects they have permissions over.
Authentication and authorization is done using the current session,
or any of the valid :doc:`sharing methods </commercial/sharing>`.
