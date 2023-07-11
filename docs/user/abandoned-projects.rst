Abandoned projects policy
=========================

This policy describes the process by which a Read the Docs project :term:`slug` may be changed.

.. tip:: If you want to de-list a project's fork from search results, please see :doc:`/unofficial-projects`.

Rationale
---------

Conflict between the current use of the name and a different suggested use of
the same name occasionally arise.  This document aims to provide general
guidelines for solving the most typical cases of such conflicts.

Specification
-------------

The main idea behind this policy is that Read the Docs serves the community.  Every
user is invited to upload content under the Terms of Use, understanding that it
is at the sole risk of the user.

While Read the Docs is not a backup service, the core team of Read the Docs does their best to keep that
content accessible indefinitely in its published form. However, in certain
edge cases the greater community's needs might outweigh the individual's
expectation of ownership of a project name.

The use cases covered by this policy are:

Abandoned projects
    Renaming a project so that the original project name can be used by a
    different project

Active projects
    Resolving disputes over a name

Implementation
--------------

Reachability
~~~~~~~~~~~~

The user of Read the Docs is solely responsible for being reachable by the core team
for matters concerning projects that the user owns. In every case where
contacting the user is necessary, the core team will try to do so,
using the following means of contact:

* E-mail address on file in the user's profile
* E-mail addresses found in the given project's documentation
* E-mail address on the project's home page

The core team will stop trying to reach the user after six weeks and the user
will be considered *unreachable*.

Abandoned projects
~~~~~~~~~~~~~~~~~~

A project is considered *abandoned* when ALL of the following are met:

* Owner is unreachable (see `Reachability`_)
* The project has no proper documentation being served (no successful builds) or
  does not have any releases within the past twelve months
* No activity from the owner on the project's home page (or no home page
  found).

All other projects are considered *active*.

Renaming of an abandoned project
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Projects are never renamed solely on the basis of abandonment.

An *abandoned* project can be renamed (by appending ``-abandoned`` and a
uniquifying integer if needed) for purposes of reusing the name when ALL of the
following are met:

* The project has been determined *abandoned* by the rules described above
* The candidate is able to demonstrate their own failed attempts to contact the
  existing owner
* The candidate is able to demonstrate that the project suggested to reuse the
  name already exists and meets notability requirements
* The candidate is able to demonstrate why a fork under a different name is not
  an acceptable workaround
* The project has fewer than 100 monthly pageviews
* The core team does not have any additional reservations.


Reporting an abandoned project
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can report an abandoned project according to this policy by contacting our :doc:`/support`.

Please include the following information:

.. code-block:: text

  URL of abandoned documentation project: ...
  URL of abandoned project's repository (if any): ...
  URL of abandoned project's website (if any): ...

  Are you suggesting that an alternative project should take over the
  name (slug) abandoned project? (y/n)

  URL of alternative documentation (if any): ...
  URL of alternative website (if any): ...
  URL of alternative repository (if any): ...

  Describe attempts of reaching the owner(s) of the abandoned project:
  ...


Name conflict resolution for active projects
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The core team of Read the Docs are not arbiters in disputes around *active* projects.
The core team recommends users to get in touch with each other and solve the
issue by respectful communication.

Prior art
---------

The Python Package Index (PyPI) policy for claiming abandoned packages
(`PEP-0541 <https://www.python.org/dev/peps/pep-0541>`_) heavily
influenced this policy.
