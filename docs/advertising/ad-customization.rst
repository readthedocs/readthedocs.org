:orphan:

Customizing Advertising
=======================

.. warning::

    This document details features that are a **work in progress**.
    To discuss this document, please get in touch in the `issue tracker`_.

    .. _issue tracker: https://github.com/readthedocs/readthedocs.org/issues

In addition to allowing users and documentation authors to
:ref:`opt out <advertising/ethical-advertising:Opting out>` of advertising,
we allow some additional controls for documentation authors to control
the positioning and styling of advertising.
This can improve the performance of advertising or make sure the ad
is in a place where it fits well with the documentation.


Controlling the placement of an ad
----------------------------------

It is possible for a documentation author to instruct Read the Docs
to position advertising in a specific location.
This is done by adding a specific element to the generated body.
The ad will be inserted into this container wherever this element is in the document body.

.. code-block:: html

    <div data-ea-publisher="readthedocs"></div>

For additional options, see the `EthicalAds client documentation`_.

.. _EthicalAds client documentation: https://ethical-ad-client.readthedocs.io/


In Sphinx
~~~~~~~~~

In Sphinx, this is typically done by
adding a new template (under `templates_path`_)
for inclusion in the `HTML sidebar`_ in your ``conf.py``.

.. _HTML sidebar: https://www.sphinx-doc.org/page/usage/configuration.html#confval-html_sidebars
.. _templates_path: https://www.sphinx-doc.org/page/usage/configuration.html#confval-templates_path


.. Note: this does not work on the RTD sphinx theme because it doesn't use ``html_sidebars``.
.. code-block:: python

    ## In conf.py

    # This order is defined in the basic theme
    # but other themes could be different
    html_sidebars = {'**':[
        'localtoc.html',
        'ethicalads.html',  # Put the ad below the navigation but above previous/next
        'relations.html',
        'sourcelink.html',
        'searchbox.html',
    ]}

.. code-block:: html

    <!-- In _templates/ethicalads.html -->
    <div data-ea-publisher="readthedocs"></div>
