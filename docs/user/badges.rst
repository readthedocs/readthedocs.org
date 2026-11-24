Status badges
=============

Status badges let you show the state of your documentation to your users.
They will show if the latest build has passed, failed, or is in an unknown state.
They are great for embedding in your README,
or putting inside your actual doc pages.

You can see a badge in action in the `Read the Docs README`_.

Display states
--------------

Badges have the following states which can be shown to users:

* **Green**: ``passing`` - the last build was successful.
* **Red**: ``failing`` - the last build failed.
* **Yellow**: ``unknown`` - we couldn't figure out the status of your last build.

An example of each is shown here:

|green| |nbsp| |red| |nbsp| |yellow|

Automatically generated
-----------------------

Badges are generated on-demand for all Read the Docs projects, using the following URL syntax:

.. code-block:: text

   https://app.readthedocs.org/projects/<project-slug>/badge/?version=<version>&style=<style>

Style
-----

You can pass the ``style`` GET argument to get custom styled badges.
This allows you to match the look and feel of your website.
By default, the ``flat`` style is used.

+---------------+---------------------+
| Style         | Badge               |
+===============+=====================+
| flat - default| |Flat Badge|        |
+---------------+---------------------+
| flat-square   | |Flat-Square Badge| |
+---------------+---------------------+
| for-the-badge | |Badge|             |
+---------------+---------------------+
| plastic       | |Plastic Badge|     |
+---------------+---------------------+
| social        | |Social Badge|      |
+---------------+---------------------+

.. |Flat Badge| image:: https://app.readthedocs.org/projects/pip/badge/?version=latest&style=flat
.. |Flat-Square Badge| image:: https://app.readthedocs.org/projects/pip/badge/?version=latest&style=flat-square
.. |Badge| image:: https://app.readthedocs.org/projects/pip/badge/?version=latest&style=for-the-badge
.. |Plastic Badge| image:: https://app.readthedocs.org/projects/pip/badge/?version=latest&style=plastic
.. |Social Badge| image:: https://app.readthedocs.org/projects/pip/badge/?version=latest&style=social


Version-specific badges
-----------------------

You can change the version of the documentation your badge points to.
To do this, you can pass the ``version`` GET argument to the badge URL.
By default, it will point at the *default version* you have specified for your project.

The badge URL looks like this:

.. code-block:: text

    https://app.readthedocs.org/projects/<project-slug>/badge/?version=latest


Embedding a badge
-----------------

Use one of the following snippets to embed a badge in your README or documentation pages.
Replace ``<project-slug>`` with your project's slug,
and ``<project-url>`` with the URL of your documentation.

.. tabs::

   .. tab:: reStructuredText

      .. code-block:: rst

         .. image:: https://app.readthedocs.org/projects/<project-slug>/badge/?version=latest
            :target: <project-url>
            :alt: Documentation Status

   .. tab:: Markdown

      .. code-block:: markdown

         [![Documentation Status](https://app.readthedocs.org/projects/<project-slug>/badge/?version=latest)](<project-url>)

   .. tab:: HTML

      .. code-block:: html

         <a href="<project-url>">
           <img src="https://app.readthedocs.org/projects/<project-slug>/badge/?version=latest" alt="Documentation Status" />
         </a>

.. _Read the Docs README: https://github.com/readthedocs/readthedocs.org/blob/main/README.rst
.. |green| image:: https://assets.readthedocs.org/static/projects/badges/passing-flat.svg
.. |red| image:: https://assets.readthedocs.org/static/projects/badges/failing-flat.svg
.. |yellow| image:: https://assets.readthedocs.org/static/projects/badges/unknown-flat.svg
.. |nbsp| unicode:: 0xA0
   :trim:


Badges for private projects
---------------------------

.. include:: /shared/admonition-rtd-business.rst

For private projects, a badge URL cannot be guessed.
A token is needed to display it.
Please :doc:`contact support </support>` to get the badge URL for your private project.
