Building With Pre-1.0 Versions Of MkDocs
========================================

Recent changes to ``mkdocs`` forced us to `upgrade the default version installed`_ by Read the Docs
and this may be a breaking change for your documentation.

.. _upgrade the default version installed: https://github.com/readthedocs/readthedocs.org/pull/4041

You should check that your docs continue building in any of these cases:

* your project doesn't have a ``requirements.txt`` file pinning ``mkdocs`` to a specific version
* your project is using a custom theme
* your project is using Markdown extensions

In case your builds are failing because of a ``mkdocs`` issue,
you may want to follow one of the following solutions depending on the case.


Pin MkDocs to an older version
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Before Read the Docs upgraded its default version installed, ``mkdocs==0.15.0`` was used.
To make your project continue using this version you will need to create a ``requirements.txt`` file with this content::

     # requirements.txt
     mkdocs==0.15.0
     mkdocs-bootstrap==0.1.1
     mkdocs-bootswatch==0.1.0
     markdown>=2.3.1,<2.5


More detailed information about how to specify dependencies can be found :ref:`here <guides/troubleshooting/specifying-dependencies:Specifying Dependencies>`.


Upgrade your custom theme to be compatible with later MkDocs versions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

It is possible that your build passes but your documentation doesn't look correct.
This may be because newer MkDocs versions installed by Read the Docs introduced some breaking changes on the structure of the theme.

You should check the `mkdocs' Custom Theme documentation`_ to upgrade your custom theme and make it compatible with the new version.

.. _mkdocs' Custom Theme documentation: https://www.mkdocs.org/user-guide/custom-themes/


Upgrade how extension arguments are defined
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

MkDocs has changed the way that ``markdown_extensions`` are defined and you may need to upgrade it.
If you where passing arguments to the extension by defining them between brackets (``toc(permalink=true)``) in your ``mkdocs.yaml`` you may need to upgrade it to the new way.

For example, this definition:

.. code-block:: yaml

   markdown_extensions:
     - admonition
     - codehilite(guess_lang=false)
     - toc(permalink=true)
     - footnotes
     - meta

needs to be replaced by:

.. code-block:: yaml

   markdown_extensions:
     - admonition
     - codehilite
         guess_lang: false
     - toc
         permalink: true
     - footnotes
     - meta
