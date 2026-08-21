.. This document is linked from:
..    https://app.readthedocs.org/.well-known/security.txt
..    https://app.readthedocs.org/security/

Security reports
================

Security is extremely important to us at Read the Docs.
We follow generally accepted industry standards to protect the personal information
submitted to us, both during transmission and once we receive it.
In the spirit of transparency,
we are committed to responsible reporting and disclosure of security issues.

.. contents:: Contents
   :local:
   :backlinks: none
   :depth: 1

.. seealso::

   :doc:`/legal/security-policy`
      Read our policy for security, which we base our security handling and reporting on.

Supported versions
------------------

Only the latest version of Read the Docs will receive security updates.
We don't support security updates for :doc:`custom installations </open-source-philosophy>` of Read the Docs.

Reporting a security issue
--------------------------

If you believe you've discovered a security issue at Read the Docs,
please contact us at **security@readthedocs.org** (optionally using our :ref:`security:PGP key`).
We request that you please not publicly disclose the issue until it has been addressed by us.

You can expect:

* We will respond acknowledging your email typically within one business day.
* We will follow up if and when we have confirmed the issue with a timetable for the fix.
* We will notify you when the issue is fixed.
* We will create a `GitHub advisory`_ and publish it when the issue has been fixed
  and deployed in our platforms.

.. _GitHub advisory: https://github.com/readthedocs/readthedocs.org/security/advisories

PGP key
-------

You may use this :download:`PGP key </_static/security/pgpkey.txt>`
to securely communicate with us and to verify signed messages you receive from us.

Bug bounties
------------

While we sincerely appreciate and encourage reports of suspected security problems,
please note that the Read the Docs is an open source project, and **does not run any bug bounty programs**.
But we will gladly give credit to you and/or your organization for responsibly reporting security issues.

Security issue archive
----------------------

You can see all past reports at https://github.com/readthedocs/readthedocs.org/security/advisories.

Version 3.2.0
~~~~~~~~~~~~~

:ref:`changelog:Version 3.2.0` resolved an issue where a specially crafted request
could result in a DNS query to an arbitrary domain.

This issue was found by `Cyber Smart Defence <https://www.cybersmartdefence.com/>`_
who reported it as part of a security audit to a firm running a local installation
of Read the Docs.


Release 2.3.0
~~~~~~~~~~~~~

:ref:`changelog:Version 2.3.0` resolves a security issue with translations on our community
hosting site that allowed users to modify the hosted path of a target project by
adding it as a translation project of their own project. A check was added to
ensure project ownership before adding the project as a translation.

In order to add a project as a translation now, users must now first be granted
ownership in the translation project.
