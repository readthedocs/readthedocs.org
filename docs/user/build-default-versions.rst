:orphan:


.. This page contains good detailed content about the exact versions Read the
   Docs is install by default, but I don't think it's good content as a
   user-facing documentation page. However, I'm keeping it around and linking it
   from the "Build process" page when mentioning there are some dependencies
   installed by default.

Default versions of dependencies
================================

Read the Docs supports any documentation tool to build your documentation.
However, we provide pre-defined builders for
`Sphinx <https://www.sphinx-doc.org/>`__ and `MkDocs <https://www.mkdocs.org/>`__.

In the past we used to install several dependencies to a specific version and update them after some time,
but doing so would break some builds and make it more difficult for new projects to use new versions.
For this reason, we are now installing just the minimal required dependencies using their latest version by default.
You can see the full list of historical dependencies and advice for migrating in our `blog post <https://blog.readthedocs.com/defaulting-latest-build-tools/>`__ announcing this change.

.. note::

   In order to keep your builds reproducible,
   it's highly recommended declaring its dependencies and versions explicitly.
   See :doc:`/guides/reproducible-builds`.

External dependencies
---------------------

Python
~~~~~~

These are the dependencies that are installed by default when using a Python environment:

Sphinx:
  Latest version by default.

Mkdocs:
  Latest version by default.

pip:
  Latest version by default.

setuptools:
  Latest version by default.

Conda
~~~~~

These are the dependencies that are installed by default when using a Conda environment:

Conda:
   Miniconda2 ``4.6.14``
   (could be updated in the future to use the latest version by default).

Mkdocs:
  Latest version by default installed via ``conda``.

Sphinx:
  Latest version by default installed via ``conda``.

sphinx-rtd-theme:
  Latest version by default installed via ``conda``.
  Projects created after August 7, 2023 won't install this dependency by default.

mock:
  Latest version by default installed via ``pip``.
  Projects created after August 7, 2023 won't install this dependency by default.

pillow:
  Latest version by default installed via ``pip``.
  Projects created after August 7, 2023 won't install this dependency by default.

recommonmark:
  Latest version by default installed via ``conda``.
  Projects created after August 7, 2023 won't install this dependency by default.
