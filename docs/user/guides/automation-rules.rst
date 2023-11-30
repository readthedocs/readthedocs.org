How to manage versions automatically
====================================

In this guide,
we show you how to define rules to automate creation of new versions on Read the Docs,
using your Git repository's version logic.
Automating your versioning on Read the Docs means you only have to handle your versioning logic in Git.

.. seealso::

   :doc:`/versions`
     Learn more about versioning of documentation in general.

   :doc:`/automation-rules`
     Reference for all different rules and actions possible with automation.

Adding a new automation rule
----------------------------

First you need to go to the automation rule creation page:

#. Navigate to :menuselection:`Admin --> Automation Rules`.
#. Click on :guilabel:`Add Rule` and you will see the following form.

.. image:: /img/screenshot_automation_rules_add.png
   :alt: Screenshot of the "Add Rule" form

In the :guilabel:`Automation Rule` form, you need to fill in 4 fields:

#. Enter a :guilabel:`Description` that you can refer to later.
   For example, entering "Create new stable version" is a good title,
   as it explains the intention of the rule.

#. Choose a :guilabel:`Match`,
   which is the pattern you wish to detect in either a Git branch or tag.

   * :ref:`Any version <automation-rules:Predefined matches>` matches all values.
   * :ref:`SemVer versions <automation-rules:Predefined matches>` matches only values that have the `SemVer`_ format.
   * :ref:`Custom match <automation-rules:Custom matches>` matches your own pattern (entered below).
     If you choose this option,
     a field :guilabel:`Custom match` will automatically appear below the drop-down where you can add a regular expression in `Python regex format`_.

#. Choose a :guilabel:`Version type`.
   You can choose between *Tag* or *Branch*,
   denoting *Git tag* or *Git branch*.

#. Finally, choose the :guilabel:`Action`:

   * :ref:`Activate version <automation-rules:Actions for versions>`
   * :ref:`Hide version <automation-rules:Actions for versions>`
   * :ref:`Set version as default <automation-rules:Actions for versions>`
   * :ref:`Delete version (on branch/tag deletion) <automation-rules:Actions for versions>`


Now your rule is ready and you can press :guilabel:`Save`.
The rule takes effect immediately when a new version is created,
but does not apply to old versions.

.. tip::

   Examples of common usage
     See :ref:`the list of examples <automation-rules:Examples>` for rules that are commonly used.

   Want to test if your rule works?
     If you are using Git in order to create new versions,
     create a Git tag or branch that matches the rule and check if your automation action is triggered.
     After the experiment,
     you can delete both from Git and Read the Docs.

.. _Python regex format: https://docs.python.org/3/library/re.html
.. _SemVer: https://semver.org/

Ordering your rules
-------------------

The order your rules are listed in  :menuselection:`Admin --> Automation Rules` matters.
Each action will be performed in that order,
so earlier rules have a higher priority.

You can change the order using the up and down arrow buttons.

.. note::

   New rules are added at the start of the list
   (i.e. they have the highest priority).
