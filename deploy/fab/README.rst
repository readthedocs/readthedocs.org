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

