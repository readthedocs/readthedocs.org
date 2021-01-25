Supported Tools and Dependencies
================================

Read the Docs supports two tools to build your documentation: Sphinx_ and MkDocs_.
In order to provide :doc:`several features </features>`,
Read the Docs needs to inject or modify some content while building your docs.

When an incompatible change happens in one of these tools or dependencies,
we need to change our code as well to keep our features working,
this is done with backwards compatibility in mind.

But sometimes is hard to keep compatibility with old and new versions at the same time,
so in order to continue moving forward on future development and features we need to drop support for some versions.

.. note::

   Your existent documentation will always be kept online and working,
   But **when support for a tool or dependency ends, new builds may fail**.

.. _Sphinx: https://www.sphinx-doc.org/
.. _MkDocs: https://www.mkdocs.org/

.. contents:: Contents
   :local:
   :depth: 3

End of support policy
---------------------

Our policy defines how long a given tool or dependency is considered supported.
After it reaches its end of support date,
we don't offer support for builds/docs using these tools or dependencies,
you'll need to upgrade in order to receive support.
For :doc:`/commercial/index` we provide an extended support of six after the official end of support date.

For tools that define an EOL date, we try to follow that date for our policy.
For tools that release their versions incrementally without an EOL date,
we choose a date based on the release of mayor versions (versions with breaking changes),
the date since it was last updated, and its usage on our platform.

.. note::

   Some recent versions may be supported, but aren't listed on these tables
   (specially minor updates from supported versions),
   contact us if you have doubts.

Default dependencies
--------------------

We install some dependencies by default in order to build your project.
In the past we used to pin these dependencies to a specific version and update them after some time,
but when doing so, some builds could break.
For this reason we are now installing their latest version (or latest supported version) by default.

External dependencies (Python)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Sphinx:
  Projects created before Oct 20, 2020 will use ``1.8.x``.
  New projects use the latest version.

Mkdocs:
  Projects created before April 3, 2019 will use ``0.17.3``.
  New projects use the latest version.

sphinx-rtd-theme:
  Projects created before Oct 20, 2020 will use ``0.4.3``.
  New projects use the latest version.

pip:
  Latest version by default.

setuptools:
  Latest version by default.

six:
  Latest version by default (could be removed in the future).

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

.. note::

   In order to keep your builds reproducible,
   we highly recommend pinning all of your dependencies.

   .. TODO: link to this guide once it's written https://github.com/readthedocs/readthedocs.org/issues/7852.

External dependencies (Conda)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Conda:
   Miniconda2 ``4.6.14``
   (could be updated to use the latest version by default).

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

six:
  Latest version by default installed via ``conda`` (could be removed in the future).


Internal dependencies
~~~~~~~~~~~~~~~~~~~~~

Internal dependencies are needed to integrate your docs with Read the Docs.
We guarantee that these dependencies will work with all current supported versions of our tools,
you don't need to specify or pinning them.

readthedocs-sphinx-ext:
   ``2.1.x`` for Python projects, latest version for Conda projects.

Table of supported versions
---------------------------

Sphinx
~~~~~~

Sphinx releases its versions incrementally.

.. list-table::
   :header-rows: 1

   * - Version
     - Released / Latest Update
     - Supported Until

   * - ``3.x``
     - Apr 5, 2020 / ???
     - 5.0 is released or early

   * - ``2.x``
     - Mar 28, 2019 / Mar 5, 2020
     - 4.0 is released or early

   * - ``1.8.x``
     - Sep 12, 2018 / Mar 10, 2019
     - Nov 31, 2021

   * - ``1.7.x``
     - Feb 12, 2018 / Sep 5, 2018
     - Nov 31, 2021

   * - ``1.6.x``
     - May 16, 2017 / Feb 4, 2017
     - Nov 31, 2021

   * - ``<= 1.5.x``
     - Mar 21, 2008 / May 14, 2017
     - Unsupported

Mkdocs
~~~~~~

MkDocs releases its versions incrementally.

.. list-table::
   :header-rows: 1

   * - Version
     - Released / Latest Update
     - Supported Until

   * - ``1.1.x``
     - Feb 22, 2020 / ???
     - 3.0 released or early

   * - ``1.0.x``
     - Aug 3, 2018 / Sep 17, 2018
     - 2.0 released or early

   * - ``0.17.x``
     - Oct 19, 2017 / Jul 6, 2018
     - Nov 31, 2021

   * - ``<= 0.16.x``
     - Jan 11, 2014 / Apr 4, 2017
     - Unsupported

Python
~~~~~~

Python_ defines an EOL (End Of Life) date for all its versions.

.. _Python: https://www.python.org/

.. list-table::
   :header-rows: 1

   * - Version
     - EOL Date
     - Supported Until

   * - ``3.9.x`` (not available yet)
     - Oct 05, 2025
     - Dec 31, 2025

   * - ``3.8.x``
     - Oct 14, 2024
     - Dec 31, 2024

   * - ``3.7.x``
     - Jun 27, 2023
     - Sep 31, 2023

   * - ``3.6.x``
     - Dec 23, 2021
     - Jan 31, 2022

   * - ``3.5.x``
     - Sep 13, 2020
     - Nov 31, 2021

   * - ``2.7.x``
     - Jan 01, 2020
     - Nov 31, 2021
