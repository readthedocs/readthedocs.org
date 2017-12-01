Abstract
========

This document describes the process by which a RTD project name may be changed.


Rationale
=========

Conflict between the current use of the name and a different suggested use of
the same name occasionally arise.  This document aims to provide general
guidelines for solving the most typical cases of such conflicts.


Specification
=============

The main idea behind this document is that RTD serves the community.  Every
user is invited to upload content under the Terms of Use, understanding that it
is at the sole risk of the user.

While RTD is not a backup service, the maintainers do their best to keep that
content accessible indefinitely in its published form.  However, in certain
edge cases the greater community's needs might outweigh the individual's
expectation of ownership of a project name.

The use cases covered by this document are:

* Abandoned projects:

    * renaming a project so that the original project name can be used by a
      different project.

* Active projects:

    * resolving disputes over a name.


Implementation
==============

Reachability
------------

The user of RTD is solely responsible for being reachable by the maintainers
for matters concerning projects that the user owns.  In every case where
contacting the user is necessary, the maintainers will try to do so at least
three times, using the following means of contact:

* e-mail address on file in the user's profile;
* e-mail addresses found in the given project's documentation; and
* e-mail address on the project's home page.

The maintainers will stop trying to reach the user after six weeks and the user
will be considered *unreachable*.


Abandoned projects
------------------

A project is considered *abandoned* when ALL of the following are met:

* owner is unreachable (see Reachability above);
* no releases within the past twelve months; and
* no activity from the owner on the project's home page (or no home page
  found).

All other projects are considered *active*.


Renaming of an abandoned project
--------------------------------

Projects are never renamed solely on the basis of abandonment.

An *abandoned* project can be renamed (by appending "-abandoned" and a
uniquifying integer if needed) for purposes of reusing the name when ALL of the
following are met:

* the project has been determined *abandoned* by the rules described above;
* the candidate is able to demonstrate their own failed attempts to contact the
  existing owner;
* the candidate is able to demonstrate that the project suggested to reuse the
  name already exists and meets notability requirements;
* the candidate is able to demonstrate why a fork under a different name is not
  an acceptable workaround;
* access statistics for the existing package indicate the project is not being
  heavily used; and
* the maintainers do not have any additional reservations.


Name conflict resolution for active projects
--------------------------------------------

The maintainers of RTD are not arbiters in disputes around *active* projects.
The maintainers recommend users to get in touch with each other and solve the
issue by respectful communication.


Prior art
=========

The Python Package Index (PyPI) policy for claiming abandoned packages
(`PEP-0541 <https://www.python.org/dev/peps/pep-0541>`_) heavily
influenced this document.


Copyright
=========

This document has been placed in the public domain.
