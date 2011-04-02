Interesting Settings
====================

VARNISH_SERVERS
--------------

Default: `undefined`

This is a list of the varnish servers that you are using. It is used to perform cache invalidation. If this settings is not defined, no invalidation will be done.


MULTIPLE_APP_SERVERS
--------------------

Default: `undefined`

This is a list of application servers that built documentation is copied to. This allows you to run an independent build server, and then have it rsync your built documentation across multiple front end documentation/app servers.
