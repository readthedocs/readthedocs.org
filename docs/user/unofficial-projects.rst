Unofficial and unmaintained projects policy
===========================================

This policy describes a process where we take actions against unmaintained_ and unofficial_ forks of project documentation.

.. tip:: If you want to free up a project's :term:`slug` and gain access over it, please see :doc:`/abandoned-projects`.

Rationale
---------

Documentation projects may be kept online indefinitely, even though a newer version of the same project exists elsewhere.
There are many reasons this can happen,
including forks, old official docs that are unmaintained, and many other situations.

The problem with old, outdated docs is that users will find them in search results,
and get confused to the validity of them.
Projects will then get support requests from people who are using an old and incorrect documentation version.

We have this policy to allow a reporter to request the *delisting* of forks that are old and outdated.


High level overview
~~~~~~~~~~~~~~~~~~~

The process at a high level looks like:

* A reporter contacts us about a project they think is outdated and unofficial
* A Read the Docs team member evaluates it to make sure it's outdated and unofficial, according to this policy
* We delist this project from search results and send an email to owners of the Read the Docs project
* If a project owner objects, we evaluate their evidence and make a final decision


Definitions
-----------


Unofficial projects
~~~~~~~~~~~~~~~~~~~

A project is considered *unofficial* when it is not linked to or mentioned in **any** of these places:

* Websites and domains associated with the project
* The project's primary repository -- README files, repository description, or source code


Unmaintained projects
~~~~~~~~~~~~~~~~~~~~~

A project is considered *unmaintained* when **any** of the following are met:

* The configured version control repository is unreadable. This can happen if the repository is deleted, credentials are broken or the Git host is permanently unresponsive.
* The project is only serving content from releases and commits 6 months or older.
* All builds have failed for more than 6 months.


Implementation
--------------


Requesting a project be delisted
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can request that we delist an outdated, unmaintained documentation by contacting our :doc:`/support`.

Please include the following information:

.. code-block:: text

  URL of unofficial and unmaintained documentation project: ...
  URL of official documentation (if any): ...
  URL of official project website (if any): ...
  URL of official project repository (if any): ...

  Describe attempts of reaching the owner(s) of the documentation project:
  ...


Delisting
~~~~~~~~~

Projects that are determined to be unmaintained_ and unofficial_ will have a ``robots.txt`` file added that removes them from all search results:

.. code-block:: text

  # robots.txt
  User-agent: *
  # This project is delisted according to the Unofficial and Unmaintanied Project Policy
  # https://docs.readthedocs.io/en/stable/unofficial-projects.html
  Disallow: /


Projects will be delisted if they meet **all** of the following criteria:

* The person who submits the report of the unmaintained_ and unofficial_ project also demonstrates failed attempts to contact the existing owners.
* The project has been determined unmaintained_ and unofficial_ by the rules described above.
* The core team does not have any additional reservations.

The Read the Docs team will do the following actions when a project is delisted:

* Notify the Read the Docs project owners via email about the delisting.
* Add the ``robots.txt`` file to be served on the project domain.

If any of the project owners respond, their response will be taken into account, and the delisting might be reversed.


Thinking behind the policy
--------------------------

The main idea behind this policy is that Read the Docs serves the community.
Every user is invited to upload content under `terms of service <https://about.readthedocs.com/terms-of-service/>`_
understanding that it is at the sole risk of the user.

While Read the Docs is not a backup service, the core team of Read the Docs does their best to keep content accessible indefinitely in its published form. However, in certain edge cases,
the greater community's needs might outweigh the individual's expectation of continued publishing.


Prior art
---------

This policy is inspired by our :doc:`abandoned-projects`.
The Python Package Index (PyPI) policy for claiming abandoned packages
(`PEP-0541 <https://www.python.org/dev/peps/pep-0541>`_) heavily influenced this policy.

.. _unmaintained: #unmaintained-projects
.. _unofficial: #unofficial-projects
