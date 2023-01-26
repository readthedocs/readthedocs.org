How to create new versions automatically
========================================

Versioning documentation to align with the project that it documents does not have to be a manual chore.
If you are already versioning your Git repository,
you may define your own rules that can publish your documentation with the same version that you have already specified in Git.


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

Adding a new rule
-----------------

#. Go to your project dashboard
#. Click :guilabel:`Admin` > :guilabel:`Automation Rules`
#. Click on :guilabel:`Add Rule`
#. Fill in the fields
#. Click :guilabel:`Save`


Ordering your rules
-------------------

The order your rules are listed in  :guilabel:`Admin` > :guilabel:`Automation Rules` matters.
Each action will be performed in that order,
so first rules have a higher priority.

You can change the order using the up and down arrow buttons.

.. note::

   New rules are added at the end (lower priority).
