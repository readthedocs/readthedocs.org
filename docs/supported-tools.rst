Supported Tools and Dependencies
================================

Read the Docs supports two tools to build your documentation:
`Sphinx <https://www.sphinx-doc.org/>`__ and `MkDocs <https://www.mkdocs.org/>`__.
In order to provide :doc:`several features </features>`,
Read the Docs needs to inject or modify some content while building your docs.

When an incompatible change happens in one of these tools or dependencies,
we need to change our code as well to keep our features working.
This is done with backwards compatibility in mind,
but sometimes is hard to keep compatibility with old and new versions at the same time.
In order to continue moving forward on future development and features,
we need to drop support for some versions.

.. note::

   Your existent documentation will always be kept online and working,
   but **when support for a tool or dependency ends, new builds may fail**.

.. contents:: Contents
   :local:
   :depth: 3

End of support policy
---------------------

Our policy defines how long a given tool or dependency is considered supported.
Read the Docs will contact all users when an end of support date is close,
after that date your builds may start failing and you will need to upgrade in order to receive support.
For :doc:`/commercial/index` we provide an extended support of six months after the official end of support date.

This is how we choose an end of support date:

- For tools that define an :abbr:`EOL (End Of Life)` date, we try to follow that date for our policy.
- For tools that release their versions incrementally without an EOL date,
  we choose a date based on:

  - The release versions with breaking changes (mayor versions).
  - The date since it was last updated.
  - And its usage on our platform.

.. note::

   Some recent versions may be supported, but aren't listed on these tables
   (specially minor updates from supported versions).
   Contact us if you have doubts.

Default dependencies
--------------------

We install some dependencies in order to build your project without specifying their dependencies.
In the past we used to set these dependencies to a specific version and update them after some time,
but by doing so would break some builds and new projects wouldn't be able to use a new version by default.
For this reason we are now installing their latest version (or latest supported version) by default.

.. note::

   In order to keep your builds reproducible,
   it's highly recommended declaring its dependencies and versions explicitly.

   .. TODO: link to this guide once it's written https://github.com/readthedocs/readthedocs.org/issues/7852.

External dependencies (Python)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

These are the dependencies that are installed by default when using a Python environment:

Sphinx:
  Projects created before Oct 20, 2020 use ``1.8.x``.
  New projects use the latest version.

Mkdocs:
  Projects created before April 3, 2019 (April 23, 2019 for :doc:`/commercial/index`) use ``0.17.3``.
  New projects use the latest version.

sphinx-rtd-theme:
  Projects created before October 20, 2020 (January 21, 2021 for :doc:`/commercial/index`) use ``0.4.3``.
  New projects use the latest version.

pip:
  Latest version by default.

setuptools:
  Latest version by default.

mock:
  ``1.0.1`` (could be removed in the future).

pillow:
  ``5.4.1`` (could be removed in the future).

alabaster:
  ``0.7.x`` (could be removed in the future).

commonmark:
  ``0.8.1`` (could be removed in the future).

recommonmark:
  ``0.5.0`` (could be removed in the future).

External dependencies (Conda)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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

mock:
  Latest version by default installed via ``pip`` (could be removed in the future).

pillow:
  Latest version by default installed via ``pip`` (could be removed in the future).

recommonmark:
  Latest version by default installed via ``conda`` (could be removed in the future).

Internal dependencies
~~~~~~~~~~~~~~~~~~~~~

Internal dependencies are needed to integrate your docs with Read the Docs.
We guarantee that these dependencies will work with all current supported versions of our tools,
you don't need to specify them in your requirements.

- readthedocs-sphinx-ext

Table of supported versions
---------------------------

Sphinx
~~~~~~

.. list-table::
   :header-rows: 1

   * - Version
     - Released
     - Latest Update
     - Supported Until

   * - ``3.x``
     - Apr 5, 2020
     - \???
     - 5.0 is released or later/early

   * - ``2.x``
     - Mar 28, 2019
     - Mar 5, 2020
     - 4.0 is released or later/early

   * - ``1.8.x``
     - Sep 12, 2018
     - Mar 10, 2019
     - Nov 31, 2022

   * - ``1.7.x``
     - Feb 12, 2018
     - Sep 5, 2018
     - Nov 31, 2022

   * - ``1.6.x``
     - May 16, 2017
     - Feb 4, 2017
     - Nov 31, 2021

   * - ``1.5.x``
     - Dec 5, 2016
     - May 4, 2017
     - Nov 31, 2021

   * - ``<= 1.4.x``
     - Mar 21, 2008
     - Nov 23, 2016
     - Unsupported

Mkdocs
~~~~~~

.. list-table::
   :header-rows: 1

   * - Version
     - Released
     - Latest Update
     - Supported Until

   * - ``1.1.x``
     - Feb 22, 2020
     - \???
     - 3.0 released or later/early

   * - ``1.0.x``
     - Aug 3, 2018
     - Sep 17, 2018
     - 2.0 released or later/early

   * - ``0.17.x``
     - Oct 19, 2017
     - Jul 6, 2018
     - Nov 31, 2021

   * - ``0.16.x``
     - Nov 4, 2017
     - Apr 4, 2017
     - Nov 31, 2021

   * - ``0.15.x``
     - Jan 21 2016
     - Feb 18, 2016
     - Nov 31, 2021

   * - ``<= 0.14.x``
     - Jan 11, 2014
     - Jun 9, 2015
     - Unsupported

Python
~~~~~~

.. list-table::
   :header-rows: 1

   * - Version
     - EOL Date
     - Supported Until

   * - ``3.9.x`` (not available yet)
     - Oct 05, 2025
     - Jan 31, 2026

   * - ``3.8.x``
     - Oct 14, 2024
     - Jan 31, 2025

   * - ``3.7.x``
     - Jun 27, 2023
     - Sep 31, 2023

   * - ``3.6.x``
     - Dec 23, 2021
     - Mar 31, 2022

   * - ``3.5.x``
     - Sep 13, 2020
     - Nov 31, 2021

   * - ``2.7.x``
     - Jan 01, 2020
     - Nov 31, 2021
