How to use
==========

Single Server
-------------

Yes, this could be better, but it's workable for now.

::

fab -H root@166.78.178.218 all fix_perms:docs
# As docs user
fab -H 166.78.178.218 setup_db

Build
-----

::

fab -H bigbuild.readthedocs.com build

Web
---

::

fab -H bigbuild.readthedocs.com users:docs web

DB
--

::

fab -H root@$SERVER db users:root


Full setup
----------

::

fab -H root@newbuild build
fab -H root@newchimera web
fab -H root@newasgard web
fab -H root@newdb db
fab -H root@newbackup backup

You might also need to fix_perms, host_files, and a few other 1 time runs.
