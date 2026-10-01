Edge redirects Worker
=====================

Example Cloudflare Worker that answers El Proxito's hostname level redirects
at the edge from a per-hostname record in Workers KV.
It accompanies the "Edge redirects for Read the Docs" proposal
and is not deployed anywhere yet.

What it does
------------

For each request to a documentation domain, the Worker reads
``host:<hostname>`` from KV and evaluates, in proxito's order:

* HTTP to HTTPS
* ``//`` collapse
* subproject domain to main domain
* public domain to canonical custom domain
* ``/page/<file>``, ``/`` and ``/<lang>/`` to the default version
* old language codes such as ``/pt_BR/``
* trailing slash on ``/<lang>/<version>``

Anything else, and any request for a hostname without a record,
is forwarded to the origin unchanged except for an ``X-RTD-Edge-Redirect``
header that says why the edge did not answer.

Modes
-----

``EDGE_REDIRECTS_MODE`` in ``wrangler.toml`` selects the behaviour:

shadow
    Always forward to the origin. The header carries the redirect the Worker
    would have sent, so proxito can log it next to its own decision.

live
    Answer from the edge, but only for records with ``edge_redirects: true``.
    Everything else behaves as in shadow mode.

Running the tests
-----------------

The tests use Node's built-in runner and need no dependencies::

    cd dockerfiles/wrangler/edge-redirects
    node --test

``cases.json`` is the table of hostname record plus URL to expected redirect.
The intent is for the Django test suite to run the same table against proxito,
so the two implementations cannot drift apart silently.

Local development
-----------------

``wrangler dev`` runs the Worker locally with a preview KV namespace.
Seed a record with::

    wrangler kv key put --binding REDIRECTS --preview "host:docs.readthedocs.io" \
        "$(python -c 'import json; print(json.dumps(json.load(open("cases.json"))["records"]["docs"]))')"

See the record format at the top of ``worker.js``.
