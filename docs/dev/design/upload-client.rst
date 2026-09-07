Upload client: CLI and GitHub Action
====================================

Goals
-----

- Give users a supported way to upload documentation artifacts that isn't "call our API by hand".
- Work on GitHub Actions, on other CI providers, and on a laptop.
- Maintain a single implementation of the upload logic, not one per environment.
- Keep the cost of running it on GitHub Actions close to zero, with nothing for the user to install.
- Be maintainable by a small team over several years.

Non-goals
---------

- Replace the documented HTTP API.
  Calling the API directly with :program:`curl` must remain possible and documented.
- Build a general purpose Read the Docs CLI.
  This client does one thing: upload artifacts.
  Other commands can be added later, but they should not drive the design now.
- Design the token model.
  This document assumes a project-scoped token is coming, and notes where the client depends on it.

Context
-------

The upload API is described in the "Build anywhere, host with the best" design document
(https://github.com/readthedocs/readthedocs.org/pull/13134).
That document deliberately leaves the client vague, and the discussion in its review concluded
that the client deserves its own design.
This document covers only the client.

There is broad agreement on two points from that discussion:

- The first iteration ships without a client.
  :program:`curl` is enough to validate the API, and we should not rush a client design.
- A GitHub Action is the best user experience on GitHub, because it can resolve the Git metadata for the user.

The disagreement is about what the client is written in and how it is distributed.

What the client must do
-----------------------

The HTTP part of the client is small.
It is three requests:

#. ``POST /api/v3/upload/initiate/``, which returns the build, the version, and a presigned URL.
#. A multipart ``POST`` of the zip file to that presigned URL.
#. ``POST /api/v3/upload/complete/`` with the build ID and a status.

The parts that carry real complexity are elsewhere,
and they are the reason we want a client at all.

Metadata resolution
~~~~~~~~~~~~~~~~~~~

The client has to turn the environment it is running in into ``version.name``, ``version.type``, and ``version.commit``.

On GitHub Actions this is not a simple variable read.
For a ``pull_request`` event, ``GITHUB_SHA`` is the ephemeral merge commit, not the head of the pull request,
so the commit we want is ``github.event.pull_request.head.sha``.
Users writing this by hand will get it wrong, and the failure is silent:
the preview builds, but it is stamped with a commit that does not exist in their history.

The same resolution has to exist for GitLab CI, Circle CI, and other providers,
and fall back to :program:`git` when run locally.
This logic must live in one place.

Packaging
~~~~~~~~~

The client builds the zip in the structure the API expects
(``html/``, ``pdf/``, ``epub/``, ``htmlzip/``), excluding things like ``.git``,
and producing a deterministic archive.

Pre-flight validation
~~~~~~~~~~~~~~~~~~~~~

The client should fail before uploading, not after, when it can.
Checking that the HTML directory exists and contains an ``index.html``,
and that the archive is within the size limit,
turns a slow failure after a several hundred megabyte upload into an instant one.

All of these checks are also done server side.
The client's copy exists only for faster feedback.

Failure reporting
~~~~~~~~~~~~~~~~~

If the upload to S3 fails, the client must still call ``complete/`` with ``status: failed``.
Otherwise the build stays in its triggered state and consumes the project's pending upload quota.
There is a server side task that expires abandoned uploads,
but that is a backstop and not a substitute for the client reporting what happened.

Outputs
~~~~~~~

The client should report the build ID, the build URL, and the resulting documentation URL,
so they can be used by later steps in a workflow.

Decision axes
-------------

Most of the disagreement so far comes down to a small number of independent questions.
Naming them separately makes the options easier to compare:

Runtime assumption
  What has to already exist where the client runs?
  This differs between GitHub-hosted runners, self-hosted runners, other CI providers, and laptops.

Cold cost on GitHub Actions
  How long does the step take before it does any work?

Operating system support
  Does it work on Linux, macOS, and Windows runners?

Team familiarity
  Can any of us fix it during an incident?

Distribution and upgrades
  How do users get it, and how do they get the next version?

Number of implementations
  How many codebases implement the upload logic?

Options considered
------------------

Documented HTTP only
~~~~~~~~~~~~~~~~~~~~

Users call the API with :program:`curl` and build the zip themselves.

Pros:

- Nothing to build, distribute, or maintain.
- No runtime assumptions beyond :program:`curl`.
- Keeps the API honest, since it is the only interface.

Cons:

- Every user reimplements metadata resolution, and some will get the pull request commit wrong.
- No pre-flight validation, so failures are slow.
- Users who abort a script leave abandoned builds consuming their quota.
- Parsing JSON in a shell needs :program:`jq`, which is an extra dependency.

This is the right first iteration, and the wrong end state.

Bash script
~~~~~~~~~~~

A script we distribute, downloaded and run by the user.

Pros:

- No runtime to install on Linux and macOS.
- Trivially inspectable.

Cons:

- Windows is not supported without WSL or Git Bash.
- Shell is a poor language for the logic we actually need: conditional metadata resolution,
  JSON parsing, retries, and cleanup on failure.
- We do not have a strong shell maintenance skill set on the team.
- Distribution and upgrades are unsolved: a downloaded script does not update itself,
  and pinning it is manual.

The review discussion largely converged against this option.

JavaScript action plus npm CLI
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

One implementation in JavaScript or TypeScript, published twice:
as a GitHub Action using the ``node`` runner, and as an npm package with a ``bin`` entry point
for other CI providers and laptops.

Pros:

- Genuinely zero cold cost on GitHub Actions.
  JavaScript actions run on the Node binary bundled with the runner,
  so there is nothing to install and no runtime assumption at all.
- Works on Linux, macOS, and Windows runners identically.
- One implementation serving both distribution channels.
- We already maintain JavaScript in the addons repository, so this is not unfamiliar territory.

Cons:

- The action has to ship a bundled build artifact (typically via ``ncc``) committed to the repository,
  or a release workflow that produces it.
  Committed build output is a recurring maintenance annoyance.
- The non-GitHub story is weaker for our actual audience.
  Most projects uploading documentation are building it with Sphinx, MkDocs, or Zensical,
  so their environment already has Python and may not have Node.
  ``npx`` is the less convenient fallback for those users.
- More of the team is comfortable in Python than in the Node packaging ecosystem.

Python CLI plus composite action
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

One implementation in Python, published to PyPI,
with a composite action in the same repository that runs it.

The composite action does not install anything.
GitHub checks out the action's own repository onto the runner before running it,
and exposes that location as ``$GITHUB_ACTION_PATH``,
so the action can run the client directly out of its own checkout
using the Python interpreter that is preinstalled on GitHub-hosted runners.

Pros:

- One implementation, in the language the team knows best.
- Near-zero cold cost on GitHub Actions, with no ``pip``, ``pipx``, ``uv``, or network access in the step.
- The best fallback story off GitHub for a documentation audience that already has Python.
- No committed build artifacts.
- The action and the PyPI package are the same code from the same tag.

Cons:

- Assumes a usable Python interpreter is present.
  This holds on all GitHub-hosted runner images, but not necessarily on self-hosted runners.
- It works best under a zero dependency constraint, discussed below, which costs some developer convenience.
- Slightly more indirection than a JavaScript action: the action is a wrapper around a CLI,
  rather than being the implementation.

Compiled binary
~~~~~~~~~~~~~~~

A client in Go or Rust, distributed as static binaries.

Pros:

- No runtime assumption whatsoever.
- Fast, and a single artifact per platform.

Cons:

- Nobody on the team currently works in Go or Rust,
  which matters more than usual for something users run in their CI.
- Requires cross-compilation, release infrastructure, and per-platform distribution.
- The advantage only pays off in environments that have neither Python nor Node,
  which is a narrow slice of our users.

If we ever need this, we can produce standalone binaries from a Python implementation
rather than rewriting the client.

Docker container action
~~~~~~~~~~~~~~~~~~~~~~~

Pros:

- Fully controlled environment.

Cons:

- Slow. The image is pulled or built on every run.
- Only supported on Linux runners.
- Does nothing for users outside GitHub Actions.

This option is not viable for a step users run on every commit.

Separate implementations per environment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A JavaScript action for GitHub and a separate Python CLI for everyone else.

Pros:

- Each environment gets the best possible implementation.

Cons:

- Two codebases implementing the same protocol, two release processes, two sets of bugs.
- Behaviour will drift, and the drift will be in metadata resolution,
  which is the part users cannot debug.
- For a team of our size this is the highest ongoing cost of any option here.

Comparison
----------

.. list-table::
   :header-rows: 1
   :widths: 26 16 14 14 14 16

   * - Option
     - Runtime assumed
     - Cold cost
     - Windows
     - Implementations
     - Team fit
   * - Documented HTTP only
     - curl, jq
     - none
     - poor
     - zero
     - good
   * - Bash script
     - bash, jq
     - none
     - no
     - one
     - poor
   * - JavaScript action plus npm CLI
     - none on GitHub, Node elsewhere
     - none
     - yes
     - one
     - fair
   * - Python CLI plus composite action
     - Python
     - very low
     - yes
     - one
     - good
   * - Compiled binary
     - none
     - low
     - yes
     - one
     - poor
   * - Docker container action
     - none
     - high
     - no
     - one
     - fair
   * - Separate implementations
     - varies
     - none
     - yes
     - two
     - poor

Proposed solution
-----------------

Build one Python client in one repository,
and ship a composite action from the root of that same repository.

Repository layout
~~~~~~~~~~~~~~~~~

A single repository, published two ways from a single tag:

- As a package on PyPI, for other CI providers and for laptops.
- As a GitHub Action, referenced as ``readthedocs/upload-action@v1``.

Releasing means tagging, publishing to PyPI, and moving the floating major version tag.
There is one version number and one changelog.

The zero dependency constraint
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The client should use only the Python standard library:
``urllib.request``, ``zipfile``, ``json``, and ``argparse``.
Building the multipart request by hand instead of using ``requests`` is roughly forty lines.

This constraint is what makes the rest of the proposal work, and it buys more than it costs:

- The action can run the client straight from its checkout, with no installation step.
- ``pip install`` into a user's existing documentation environment can never conflict with their pins.
  This matters, because many users will install it next to Sphinx or MkDocs.
- There is no dependency upgrade or vulnerability churn to absorb.
- A single file distribution stays possible as an escape hatch.

The cost is real: no ``requests``, no rich output formatting, and hand-written multipart encoding.
We should decide deliberately whether to hold this constraint, because it is easy to lose by accident later.

We should also declare and test a minimum supported Python version.

Action interface
~~~~~~~~~~~~~~~~

.. code-block:: yaml

   name: Read the Docs Upload
   description: Upload pre-built documentation to Read the Docs
   inputs:
     token:
       description: 'Read the Docs API token. Use a secret.'
       required: true
     project:
       description: 'Project slug. Optional once project-scoped tokens are available.'
       required: false
     path:
       description: 'Directory containing the built HTML.'
       required: true
     version-name:
       description: 'Override the inferred branch/tag name or pull request number.'
       required: false
     version-type:
       description: 'Override inference: branch, tag, or external.'
       required: false
     commit:
       description: 'Override the inferred commit hash.'
       required: false
   outputs:
     build-id:
       description: 'Build ID returned by the upload API.'
     build-url:
       description: 'URL of the build detail page.'
     docs-url:
       description: 'URL where the uploaded documentation is served.'
     version-slug:
       description: 'Slug of the version that was created or updated.'

   runs:
     using: composite
     steps:
       - shell: bash
         run: >
           python "$GITHUB_ACTION_PATH/src/rtd_upload/__main__.py" upload
           --path "$INPUT_PATH"
         env:
           RTD_TOKEN: ${{ inputs.token }}
           INPUT_PATH: ${{ inputs.path }}

The token is passed through the environment and never as a command line argument,
so it does not appear in process listings or in the command echo that composite actions print.

Every inferred value has an explicit override.
Inference that cannot be overridden becomes a trap for monorepos and manually dispatched workflows.

Example usage
~~~~~~~~~~~~~

The common case, where the action resolves all the Git metadata:

.. code-block:: yaml

   name: Docs

   on:
     push:
       branches: [main]
       tags: ['v*']
     pull_request:

   jobs:
     docs:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v5
         - uses: actions/setup-python@v6
           with:
             python-version: '3.13'
         - run: pip install -r docs/requirements.txt
         - run: sphinx-build -b html docs/ _build/html

         - uses: readthedocs/upload-action@v1
           with:
             token: ${{ secrets.RTD_TOKEN }}
             project: my-project
             path: _build/html

The same workflow for a project that does not use Python to build its documentation.
Note that there is still no interpreter setup for the upload step itself:

.. code-block:: yaml

         - uses: actions/setup-node@v6
           with:
             node-version: '22'
         - run: npm ci && npm run build

         - uses: readthedocs/upload-action@v1
           with:
             token: ${{ secrets.RTD_TOKEN }}
             project: my-project
             path: dist

What the action resolves from the event:

.. list-table::
   :header-rows: 1

   * - Trigger
     - ``version.name``
     - ``version.type``
     - ``version.commit``
   * - Push to ``main``
     - ``main``
     - ``branch``
     - ``github.sha``
   * - Push tag ``v1.2.0``
     - ``v1.2.0``
     - ``tag``
     - ``github.sha``
   * - Pull request 481
     - ``481``
     - ``external``
     - ``event.pull_request.head.sha``

Outside of GitHub, the same client is invoked directly,
and performs the same inference from the CI provider's environment variables
or from :program:`git` when run locally:

.. code-block:: bash

   export RTD_TOKEN=...
   uvx readthedocs-upload upload --project my-project --path _build/html

Distribution and upgrades
-------------------------

A concern raised in review was that a client we distribute will not stay up to date.

- The floating major version tag on the action means users pinned to ``@v1``
  get fixes without doing anything, and Dependabot handles major upgrades,
  which is a workflow users already have for actions.
- The client should send a version in its ``User-Agent`` header.
  This tells us what version spread is actually deployed, instead of guessing.
- The API should be able to return an optional warning field that the client prints.
  This gives us a deprecation channel that costs almost nothing to build now
  and is very hard to add later.

Authentication and pull requests from forks
-------------------------------------------

Secrets are not available to ``pull_request`` events triggered from forks.
Pull request previews are the headline use case for this feature on open source projects,
so this will affect a lot of users and generate support requests.

None of the available answers are good:

- ``pull_request_target`` exposes the secret, and is dangerous if the workflow checks out the pull request head.
- Accepting that fork pull requests get no preview is a real regression against our current build system,
  which handles this case today.
- A short-lived credential obtained through OIDC, with no stored secret,
  is the correct long-term answer and is already noted as a future direction in the API design document.

At minimum, the client should detect a missing token in this situation
and fail with an explanation and a link, rather than surfacing a bare authentication error.

This interacts directly with the project-scoped token work,
and the token model should not be finalized without considering it.

Risks and open questions
------------------------

- Do we hold the zero dependency constraint, and what is the minimum Python version we support?
- ``--project`` becomes optional once project-scoped tokens land.
  The argument parsing should anticipate this so it is not a breaking change.

First iteration
---------------

#. Ship the API with documented :program:`curl` usage and no client, as already planned.
#. Build the CLI first, and the action as a wrapper around it.
   Building the action first would push metadata resolution into YAML,
   where it cannot be reused or tested.
#. Release both from a single tag.

References
----------

- Build anywhere, host with the best: https://github.com/readthedocs/readthedocs.org/pull/13134
- https://github.com/readthedocs/readthedocs.org/issues/1083
