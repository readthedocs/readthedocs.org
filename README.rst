Welcome to Read the Docs
========================

|build-status| |docs| |coverage|

Purpose
-------

`Read the Docs`_ hosts documentation for the open source community.
It supports many documentation tools
(e.g. Sphinx_ docs written with reStructuredText_, MkDocs_ docs written with markdown_, among others),
and can pull Git_ repositories.
Then we build documentation and host it for you.
Think of it as *Continuous Documentation*, or Docs as Code.

.. _Read the docs: https://app.readthedocs.org/
.. _Sphinx: http://www.sphinx-doc.org/
.. _reStructuredText: http://www.sphinx-doc.org/en/master/usage/restructuredtext/basics.html
.. _Git: http://git-scm.com/
.. _MkDocs: https://www.mkdocs.org/
.. _markdown: https://daringfireball.net/projects/markdown/

Documentation for Read the Docs
-------------------------------

Using a custom .readthedocs.yaml path
-------------------------------------

The `.readthedocs.yaml` file is the main configuration file for Read the Docs projects. By default, it is recognized at the root of your repository.

For monorepos containing multiple documentation projects in the same repository, it is possible to place a `.readthedocs.yaml` file in each project's subfolder. This allows each project to have its own build configuration.

.. warning::
   Changing the configuration file path will apply to all versions of your documentation. Different versions may not build correctly if the path is changed.

After adding a custom configuration file in a subfolder, make sure the relevant versions of your documentation are rebuilt.

For more details and step-by-step instructions, see the official Read the Docs guide:
https://docs.readthedocs.com/platform/stable/guides/setup/monorepo.html

Get in touch
------------

You can find information about getting in touch with Read the Docs at our
`Contribution page <https://docs.readthedocs.com/dev/latest/contribute.html#get-in-touch>`_.

Contributing
------------

You can find information about contributing to Read the Docs at our
`Contribution page <https://docs.readthedocs.com/dev/latest/contribute.html>`_.

Quickstart for GitHub hosted projects
-------------------------------------

By the end of this quickstart, you will have a new project automatically updated when you push to GitHub.

#. Create an account on `Read the Docs`_ by signing up with GitHub.

#. When prompted on GitHub, give access to your account.

#. Log in and click on "Add project".

#. Start typing the name of your repository and select it from the list,
   and click "Continue".

#. Change any information if desired and click "Next".

#. All done.  Commit away and your project will auto-update.


.. |build-status| image:: https://circleci.com/gh/readthedocs/readthedocs.org.svg?style=svg
    :alt: build status
    :target: https://circleci.com/gh/readthedocs/readthedocs.org

.. |docs| image:: https://app.readthedocs.org/projects/docs/badge/?version=latest
    :alt: Documentation Status
    :scale: 100%
    :target: https://docs.readthedocs.io/en/latest/?badge=latest

.. |coverage| image:: https://codecov.io/gh/readthedocs/readthedocs.org/branch/main/graph/badge.svg
    :alt: Test coverage
    :scale: 100%
    :target: https://codecov.io/gh/readthedocs/readthedocs.org

License
-------

`MIT`_ © 2025 Read the Docs, Inc. & contributors

.. _MIT: LICENSE
