Supported Tools and Dependencies
================================

Currently, Read the Docs supports two tools to build your documentation: Sphinx and MkDocs.
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

End of support policy
---------------------

Our policy defines how long a given tool or dependency is considered supported.
After it reaches its end of support date,
we don't offer support for builds/docs using these tools or dependencies,
you'll need to upgrade in order to receive support.
For :doc:`/commercial/index` we provide an extended support of 6 months after the end of support date.

.. note::

   Some recent versions may be supported, but aren't listed on this table
   (specially minor updates from supported versions),
   contact us if you have doubts.

Sphinx
------

.. list-table::
   :header-rows: 1

   * - Version
     - Released
     - Supported Until

   * - 3.0.0 - 3.4.x
     - Apr 5, 2020 - Jan 7, 2021
     - 5.0 is released or early

   * - 2.0.0 - 2.4.4
     - Mar 28, 2019 - Mar 5 , 2020
     - 4.0 is released or early

   * - 1.8.0 - 1.8.x
     - Sep 12, 2018 - Mar 10, 2019
     - Nov 31, 2021

   * - 1.6.0 - 1.7.9
     - May 28, 2017 - Sep 5, 2018
     - Nov 31, 2021

   * - 0.1 - 1.5.6
     - Mar 21, 2008 - May 14, 2017
     - Unsupported


Sphinx_ releases its versions incrementally.

.. _Sphinx: https://www.sphinx-doc.org/

Mkdocs
------

.. list-table::
   :header-rows: 1

   * - Version
     - Released
     - Supported Until

   * - 1.0 - 1.1.2
     - Aug 3, 2018 - May 14, 2020
     - 3.0 released or early

   * - 0.17.4 - 0.17.5
     - Jun 8, 2018 - Jul 6, 2018
     - Mar 31, 2022

   * - 0.17.0 - 0.17.3
     - Oct 19, 2017 - Mar 7, 2018
     - Nov 31, 2021

   * - 0.1 - 0.16.3
     - Jan 11, 2014 - Apr 4, 2017
     - Unsupported
   
MkDocs_ releases its versions incrementally.

.. _MkDocs: https://www.mkdocs.org/

Python
------

Python_ defines an EOL (End Of Life) date for all its versions.

.. _Python: https://www.python.org/

.. list-table::
   :header-rows: 1

   * - Version
     - EOL Date
     - Supported Until

   * - 3.10 (not available yet)
     - ?
     - ?

   * - 3.9 (not available yet)
     - Oct 05, 2025
     - Dec 31, 2025

   * - 3.8
     - Oct 14, 2024
     - Dec 31, 2024
   
   * - 3.7
     - Jun 27, 2023
     - Sep 31, 2023

   * - 3.6
     - Dec 23, 2021
     - Jan 31, 2022

   * - 3.5
     - Sep 13, 2020
     - Nov 31, 2021

   * - 2.7
     - Jan 01, 2020
     - Nov 31, 2021
