Automation Rules
================

Automation rules allow project maintainers to automate actions on new branches and tags on repositories.

When a version is created from a new branch or tag,
automation rules can perform actions like activating the new version,
or setting the new version as the default version.

Creating an automation rule
---------------------------

#. Go to your project dashboard
#. Click :guilabel:`Admin` > :guilabel:`Automation Rules`
#. Click on :guilabel:`Add Rule`
#. Fill in the fields
#. Click :guilabel:`Save`

How do they work?
-----------------

When a new tag or branch is pushed to your repository,
Read the Docs creates a new version.

All rules are evaluated for this version, in the order they are listed.
If the version matches the version type and the pattern in the rule,
the specified action is performed on that version.

.. note::
   
   Versions can match multiple rules,
   and all matching actions will be performed on the version.

Predefined matches
------------------

Automation rules support several predefined version matches:

- **Any version**: All new versions will match the rule.
- **SemVer versions**: All new versions that follow `semantic versioning <https://semver.org/>`__ will match the rule.

User defined matches
--------------------

If none of the above predefined matches meet your use case,
you can use a **Custom match**.

The custom match should be a valid `Python regular expression <https://docs.python.org/3/library/re.html>`__.
Each new version will be tested against this regular expression.

Actions
-------

When a rule matches a new version, the specified action is performed on that version.
Currently, the following actions are available:

- **Activate version**: Activates and builds the version.
- **Set version as default**: Sets the version as default,
  i.e. the version of your project that `/` redirects to.
  See more in :ref:`automatic-redirects:Root URL`.
  It also activates and builds the version.

.. note::
   
   If your versions follow :pep:`440`,
   Read the Docs activates and builds the version if it's greater than the current stable version.
   The stable version is also automatically updated at the same time.
   See more in :doc:`versions`.

Order
-----

The order your rules are listed in  :guilabel:`Admin` > :guilabel:`Automation Rules` matters.
Each action will be performed in that order,
so first rules have a higher priority.

You can change the order using the up and down arrow buttons.

.. note::

   New rules are added at the end (lower priority).

Examples
--------

Activate all new tags
~~~~~~~~~~~~~~~~~~~~~

- Match: ``Any version``
- Version type: ``Tag``
- Action: ``Activate version``

Activate only new branches that belong to the ``1.x`` release
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Custom match: ``^1\.\d+$``
- Version type: ``Branch``
- Action: ``Activate version``

Set as default new tags that have the ``-stable`` or ``-release`` suffix
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Custom match: ``-(stable|release)$``
- Version type: ``Tag``
- Action: ``Set version as default``

.. note::
   
   You can also create two rules:
   one to match ``-stable`` and other to match ``-release``.

Activate all new tags and branches that start with ``v`` or ``V``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Custom match: ``^[vV]``
- Version type: ``Tag``
- Action: ``Activate version``

.. Force new line

- Custom match: ``^[vV]``
- Version type: ``Branch``
- Action: ``Activate version``

Activate all new tags that don't contain the ``-nightly`` suffix
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. TODO: update example if https://github.com/readthedocs/readthedocs.org/issues/6354 is approved.


- Custom match: ``.*(?<!-nightly)$``
- Version type: ``Tag``
- Action: ``Activate version``
