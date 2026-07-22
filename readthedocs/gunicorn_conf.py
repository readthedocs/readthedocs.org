# """
# Gunicorn configuration shared by production and local development.

# Enables ``preload_app`` so the Django application is imported once in the master
# process and then inherited by each worker through ``fork()``. Combined with
# ``gc.freeze()`` in ``post_fork``, this keeps the interpreter + Django baseline in
# copy-on-write pages shared across workers instead of being duplicated per
# worker, which lowers per-host memory as the worker count grows.

# Load it explicitly with ``gunicorn -c python:readthedocs.gunicorn_conf`` so it is
# picked up regardless of the working directory gunicorn is launched from.
# """

import gc


# Import the application in the master process before forking workers so the
# baseline memory is shared copy-on-write instead of duplicated per worker.
preload_app = True


def post_fork(server, worker):
    # Close any database connection opened while loading the app in the master.
    # Django opens connections lazily, but a connection inherited across fork()
    # would be shared (unsafely) by every worker, so make each worker open its
    # own on first use.
    from django.db import connections

    connections.close_all()

    # Move everything that survived startup into the permanent GC generation so
    # the collector never scans it again. Otherwise the first collection in each
    # worker walks those objects and writes to their GC headers, dirtying the
    # copy-on-write pages and undoing the sharing that preload_app buys us.
    # freeze() is a cheap linked-list splice; new cyclic garbage is still
    # collected normally.
    gc.freeze()
