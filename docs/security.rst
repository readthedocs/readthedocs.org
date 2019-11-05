.. This document is linked from:
..    https://readthedocs.org/.well-known/security.txt
..    https://readthedocs.org/security/

Security
========

Security is very important to us at Read the Docs.
We follow generally accepted industry standards to protect the personal information
submitted to us, both during transmission and once we receive it.
In the spirit of transparency,
we are committed to responsible reporting and disclosure of security issues.

.. contents:: Contents
   :local:
   :backlinks: none
   :depth: 1


Account security
----------------

* All traffic is encrypted in transit so your login is protected.
* Read the Docs stores only one-way hashes of all passwords.
  Nobody at Read the Docs has access to your passwords.
* Account login is protected from brute force attacks with rate limiting.
* While most projects and docs on Read the Docs are public,
  we treat your private repositories and private documentation as confidential
  and Read the Docs employees may only view them
  with your explicit permission in response to your support requests,
  or when required for security purposes.
* You can read more about account privacy in our :doc:`privacy-policy`.


Reporting a security issue
--------------------------

If you believe you've discovered a security issue at Read the Docs,
please contact us at **security@readthedocs.org** (optionally using our :ref:`security:PGP key`).
We request that you please not publicly disclose the issue until it has been addressed by us.

You can expect:

* We will respond acknowledging your email typically within one business day.
* We will follow up if and when we have confirmed the issue with a timetable for the fix.
* We will notify you when the issue is fixed.
* We will add the issue to our :ref:`security issue archive <security:Security issue archive>`.


PGP key
-------

You may use this :download:`PGP key </_static/security/pgpkey.txt>`
to securely communicate with us and to verify signed messages you receive from us.


Security issue archive
----------------------

Version 3.5.1
~~~~~~~~~~~~~

:ref:`changelog:Version 3.5.1` fixed an issue that affected projects with "prefix" or "sphinx" user-defined redirects.
The issue allowed the creation of hyperlinks that looked like they would go to a documentation domain
on Read the Docs (either ``*.readthedocs.io`` or a custom docs domain) but instead went to a different domain.

This issue was reported by Peter Thomassen and the desec.io DNS security project
and was funded by `SSE <https://www.securesystems.de>`_.


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
