Running Read the Docs via Supervisord
=====================================

This is the easiest way to start all of the commands you'll need for development
in an environment relatively close to the production evironment. All you need is
``supervisord`` and ``redis-server``. Installation of ``redis-server`` is
outside the scope of this documentation, but once installed, all you need to run
from ``supervisord`` is::

    pip install supervisord
    cd contrib/
    supervisord

This will bring up a web instance for the dashboard, a web instance for
documentation serving, two celery instances, and redis-server.

Debugging
---------

Because supervisord doesn't redirect stdin to the various processes, ``ipdb``
and ``pdb`` will hang. You can still use ``pdb`` through telnet though!:

    def method_you_want_to_test(self):
        ...
        from celery.contrib import rdb; rdb.set_trace()
        ...

This will pause and give you a telnet port to connect to. Then simply::

    % telnet 127.0.0.1 6900
