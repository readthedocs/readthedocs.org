How NGINX proxy works
=====================

Read the Docs uses 3 different NGINX configurations;

web
  This configuration is in charge of serving the dashboard application
  on ``$NGINX_WEB_SERVER_NAME`` domain.
  It listens at port 80 and proxies it to ``web`` container on port ``8000``,
  where is the Django application running.

  It also proxies assets files under ``/static/`` to the ``storage`` container
  on port ``9000`` which is running MinIO (S3 emulator).

proxito
  Its main goal is to serve documentation pages and handle 404s.
  It proxies all the requests to ``proxito`` container on port ``8000``,
  where the "El Proxito" Django application is running.
  This application returns a small response with ``X-Accel-Redirect`` special HTTP header
  pointing to a MinIO (S3 emulator) path which is used by NGINX to proxy to it.

  Besides, the response from El Proxito contains a bunch of HTTP headers
  that are added by NGINX to the MinIO response to end up in the resulting
  response arriving to the user.

  It also configures a 404 fallback that hits an internal URL on the
  Django application to handle them correctly
  (redirects and custom 404 pages, among others)

  Finally, there are two special URLs configured to proxy the JavaScript files
  required for Read the Docs Addons and serve them directly from a GitHub tag.

  Note server is not exposed _outside_ the Docker internal's network,
  and is accessed only via Wrangler. Keep reading to understand how it's connected.

wrangler
  Node.js implementation of Cloudflare Worker that's in front of "El Proxito".
  It's listening on ``$NGINX_PROXITO_SERVER_NAME`` domain and executes the worker
  ``force-readthedocs-addons.js``.

  This worker hits ``proxito`` NGINX server listening at ``nginx`` container
  on port ``8080``  to fetch the "original response" and manipulates it to
  inject extra HTTP tags required for Read the Docs Addons (``meta`` and ``script``).



ASCII-art explanation
---------------------

.. I used: https://asciiflow.com/


Documentation page on ``$NGINX_PROXITO_SERVER_NAME``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. text::

             ┌────────────────  User
             │
             │                   ▲
   (documentation pages)         │
             │                   │
             │                   │
             ▼ 80                │
    ┌────────────────┐           │
    │                │           │
    │                │           │
    │                │           │
    │   wrangler     │ ──────────┘
    │                │
    │                │
    │                │
    └──────┬─────────┘               ┌──────────────┐        ┌────────────────┐
           │   ▲                     │              │        │                │
           │   │                     │              │    9000│                │
           │   └──────────────────── │              ├───────►│                │
           │                         │    NGINX     │        │    MinIO (S3)  │
           └───────────────────────► │              │◄───────┤                │
                                8080 │              │        │                │
                                     │              │        │                │
                                     └─────┬────────┘        └────────────────┘
                                           │  ▲
                                           │  │
                                           │  │
                                           │  │
                                     8000  ▼  │
                                     ┌────────┴─────┐
                                     │              │
                                     │              │
                                     │  El Proxito  │
                                     │              │
                                     │              │
                                     └──────────────┘


Documentation page on ``$NGINX_WEB_SERVER_NAME``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


.. text::

               User

                │
                │
            (dashboard)
                │
                │
                │
                ▼ 80
        ┌──────────────┐        ┌────────────────┐
        │              │        │                │
        │              │    9000│                │
        │              ├───────►│                │
        │    NGINX     │        │    MinIO (S3)  │
        │              │◄───────┤                │
        │              │        │                │
        │              │        │                │
        └─────┬────────┘        └────────────────┘
              │  ▲
              │  │
              │  │
              │  │
        8000  ▼  │
        ┌────────┴─────┐
        │              │
        │              │
        │     web      │
        │              │
        │              │
        └──────────────┘
