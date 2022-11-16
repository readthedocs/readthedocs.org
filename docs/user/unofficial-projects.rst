Policy for Unofficial and Outdated Projects
===========================================

This policy describes a process where we take actions against unmaintained_ and unofficial_ forks of project documentation.

.. _unmaintained: #unmaintained-projects
.. _unofficial: #unofficial-projects

Rationale
---------

Documentation projects may be kept online indefinitely, even though a newer version of the same project exists elsewhere.
There are many reasons this can happen,
including forks, old official docs that are unmaintained, and many other situations.

The problem with old, outdated docs is that users will find them in search results,
and get confused to the validity of them.
Projects will then get support requests from people who are using an old and incorrect documentation version.

We have this policy to allow project maintainers to request the *delisting* of forks that are old and outdated.

Specification
-------------
The use cases covered by this policy are:

Outdated docs
    Documentation that is not being actively maintained or updated.

Unofficial forks
    Forks of a project documentation that are not linked to from the project in any way.

Implementation
--------------

Unofficial projects
~~~~~~~~~~~~~~~~~~~

A project is considered *unofficial* when it is not linked to or mentioned in *any* of the following places:

* Websites and domains associated with the project
* Social media accounts associated with the project
* The project's primary repository -- README files, repository description, or source code

Unmaintained projects
~~~~~~~~~~~~~~~~~~~~~

A project is considered *unmaintained* when ANY of the following are met:

* The configured VCS repository is unreadable. This can happen if the repository is deleted, credentials are broken or the git host permanently unresponsive.
* The project is only serving content from releases and commits >6 months older than its source project (this happens with unmaintained forks).
* All builds have failed for >6 months.


Reachability
~~~~~~~~~~~~

for matters concerning projects that the user owns.
In every case where contacting the user is necessary,
the core team will reach out using one of the following means of contact:

* E-mail address on file in the user's profile
* E-mail address on the GitHub user account where the project is pointed

The core team will stop trying to reach the user after 2 weeks and the user
will be considered *unreachable*.

Delisting of an abandoned project
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Projects that are determined to be *Unofficial* and *Unmaintained* will have a ``robots.txt`` file added that removes them from all search results.

Projects will be delisted when ALL of the following:

* The project has been determined *unmaintained* and *unofficial* by the rules described above
* The candidate is able to demonstrate their own failed attempts to contact the
  existing owner
* The project owner is *unreachable* by the Read the Docs team
* The core team does not have any additional reservations.

Requesting a project be delisted
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you are the maintainer of a project,
you can request that we delist an outdated, unmaintained set of docs with our :doc:`/support`.

Thinking behind the policy
--------------------------

The main idea behind this policy is that Read the Docs serves the community. Every
user is invited to upload content under the Terms of Use, understanding that it
is at the sole risk of the user.

While Read the Docs is not a backup service, the core team of Read the Docs does their best to keep that
content accessible indefinitely in its published form. However, in certain
edge cases the greater community's needs might outweigh the individual's
expectation of continued publishing.

Prior art
---------

This policy is inspired by our :doc:`abandoned-projects`.
The Python Package Index (PyPI) policy for claiming abandoned packages
(`PEP-0541 <https://www.python.org/dev/peps/pep-0541>`_) heavily
influenced this policy.
