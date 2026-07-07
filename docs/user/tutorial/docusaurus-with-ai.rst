Read the Docs quickstart with an AI coding agent
================================================

This is the AI-assisted version of the :doc:`Docusaurus tutorial </tutorial/docusaurus>`.
Instead of clicking through templates and dashboards step by step,
you delegate as much of the work as possible to an AI coding agent
(`Claude Code <https://claude.com/claude-code>`_, `Cursor <https://cursor.sh/>`_,
`GitHub Copilot CLI <https://docs.github.com/en/copilot/github-copilot-in-the-cli>`_,
or any other tool that can run shell commands and call HTTP APIs).

By the end of this quickstart, you will have:

- A `Docusaurus`_ documentation site scaffolded from scratch,
- A public GitHub repository for it,
- A Read the Docs project hosting the built documentation, and
- Pull request builds enabled.

.. _Docusaurus: https://docusaurus.io/

.. note::

   The AI agent does the work that can be automated:
   scaffolding the site, writing the ``.readthedocs.yaml`` configuration,
   creating the GitHub repository, creating the Read the Docs project
   through the :doc:`API </api/v3>`, and triggering the first build.

   A few steps still require you in a browser:
   creating a Read the Docs account (if you don't have one),
   installing the Read the Docs GitHub App,
   and generating an API token.
   The agent will tell you when to do each, then resume.

Prerequisites
-------------

Before you start, make sure you have:

- An AI coding agent installed locally (Claude Code, Cursor, Copilot CLI, etc.) that can read and write files and run shell commands in your project folder.
- The `GitHub CLI <https://cli.github.com/>`_ (``gh``) installed and authenticated (``gh auth login``).
- `Node.js <https://nodejs.org/>`_ 20 or newer for local testing (optional, but recommended).
- A `GitHub account <https://github.com/signup>`_.

You do **not** need a Read the Docs account yet — the agent will help you create one if needed.

Step 1: Scaffold the project
----------------------------

Create an empty folder, open your AI agent inside it, and send this prompt:

.. code-block:: text

   Set up a Docusaurus documentation site in this folder, ready to host on Read the Docs.

   1. Scaffold a new Docusaurus site into a `docs/` subdirectory using
      `npx create-docusaurus@latest docs classic`.
   2. Configure `docs/docusaurus.config.js` for Read the Docs, following
      https://docs.readthedocs.com/platform/latest/intro/docusaurus.html#configure-trailing-slashes
      and https://docs.readthedocs.com/platform/latest/intro/docusaurus.html#set-the-canonical-url:
      set `trailingSlash: true`, and derive `url` and `baseUrl` from the
      `READTHEDOCS_CANONICAL_URL` environment variable so the site loads under
      the version path (e.g. `/en/latest/`) on Read the Docs and sets the
      canonical URL. When that variable is not set (local builds), fall back to
      `url: 'http://localhost:3000'` and `baseUrl: '/'`.
   3. Create a `.readthedocs.yaml` at the repository root that builds the site
      with Node.js 22 using `build.jobs`. The install step should run
      `npm install` inside `docs/`. The HTML build step should run `npm run build`
      inside `docs/`, then copy `docs/build/` into `$READTHEDOCS_OUTPUT/html/`.
   4. Add a `.gitignore` covering `node_modules/` and `docs/build/`.
   5. Initialize a git repository, commit everything on `main`, then create a
      public GitHub repository named `docusaurus-tutorial` with `gh repo create`
      and push.

The agent runs the scaffold, writes the configuration files, and pushes the repository.
When it finishes, you will have a working Docusaurus project on GitHub and a
``.readthedocs.yaml`` like this:

.. code-block:: yaml
   :caption: .readthedocs.yaml

   version: 2

   build:
     os: "ubuntu-22.04"
     tools:
       nodejs: "22"
     jobs:
       install:
         - cd docs/ && npm install
       build:
         html:
           - cd docs/ && npm run build
           - mkdir --parents $READTHEDOCS_OUTPUT/html/
           - cp --recursive docs/build/* $READTHEDOCS_OUTPUT/html/

It will also update ``docs/docusaurus.config.js`` so the site loads correctly
under the version path Read the Docs serves it from (for example ``/en/latest/``)
and sets the :doc:`canonical URL </canonical-urls>`:

.. code-block:: js
   :caption: docs/docusaurus.config.js

   // Derive `url` and `baseUrl` from the canonical URL Read the Docs provides.
   // Together they define the canonical URL of the site.
   const canonical = process.env.READTHEDOCS_CANONICAL_URL;
   const { origin, pathname } = canonical
     ? new URL(canonical)
     : { origin: "http://localhost:3000", pathname: "/" };

   const config = {
     // Required for compatibility with Read the Docs
     trailingSlash: true,
     url: origin,
     baseUrl: pathname,

     // ... the rest of your Docusaurus configuration
   };

   export default config;

.. note::

   If you skip this step, the published site fails to load with an error like
   ``A very common reason is a wrong site baseUrl configuration``. Read the Docs
   serves each version under a path such as ``/en/latest/``, so Docusaurus needs
   a matching ``baseUrl``. Deriving ``url`` and ``baseUrl`` from
   ``READTHEDOCS_CANONICAL_URL`` also sets the site's canonical URL. See
   :doc:`/intro/docusaurus` for background.

.. tip::

   Read the agent's plan before approving destructive commands.
   If you already have files in the folder, ask it to scaffold into a subfolder instead.

Step 2: Let the agent onboard you to Read the Docs
--------------------------------------------------

Now send this prompt to the same agent:

.. code-block:: text

   Help me get this project hosted on Read the Docs.

   First, ask me whether I already have a Read the Docs account.

   - If I don't, walk me through:
       a. Signing up at https://app.readthedocs.org/accounts/signup/ with GitHub.
       b. Installing the Read the Docs Community GitHub App at
          https://github.com/apps/read-the-docs-community for THIS repository only.
   - If I do, confirm the GitHub App is installed for this repository.
     If not, walk me through installing it.

   Installing the GitHub App is REQUIRED and must happen BEFORE creating the
   project: it is what lets Read the Docs build pull request previews and post
   the build status back on the pull request. After I install it, wait until
   Read the Docs has finished importing the repository (it appears under
   https://app.readthedocs.org/dashboard/import/ as a connected repository)
   before continuing.

   Then ask me to create a Read the Docs API token at
   https://app.readthedocs.org/accounts/tokens/create/ and paste it.
   Use that token with the Read the Docs API v3
   (https://docs.readthedocs.com/platform/stable/api/v3.html) to:

   1. POST /api/v3/projects/ to create the project. For the repository URL, use
      the exact GitHub HTML URL from `gh repo view --json url` (for example
      `https://github.com/{username}/docusaurus-tutorial`, with NO `.git` suffix
      and no trailing slash) so Read the Docs links the project to the repository
      connected through the GitHub App. Prefix the project name with my GitHub
      username, e.g. `{username}-docusaurus-tutorial`.
   2. Verify the project is connected to the GitHub repository, not just created
      with a manual URL: GET /api/v3/projects/{slug}/ and confirm it succeeded,
      then tell me to open https://app.readthedocs.org/dashboard/{slug}/edit/ and
      check that the "Connected repository" field points to my GitHub repository.
      If it says the project is not connected, have me select the repository in
      that dropdown and save before continuing.
   3. PATCH /api/v3/projects/{slug}/ to enable pull request builds
      (`external_builds_enabled: true`) and to set a short description and
      a couple of tags like `docusaurus, documentation`.
   4. POST /api/v3/projects/{slug}/versions/latest/builds/ to trigger the
      first build, then poll the build endpoint until it finishes and report
      the result.

   When the build succeeds, give me the published documentation URL.
   Treat the token as a secret — do not commit it or print it back to me.

The agent will pause and ask whether you already have an account.
Answer honestly; if you don't, follow the links it shares,
come back, and confirm when you're done so it can continue.

.. important::

   Your API token is the equivalent of your password for the Read the Docs API.
   Paste it only into a local AI agent you trust. Tokens can be revoked any
   time at https://app.readthedocs.org/accounts/tokens/ if you suspect a leak.

Step 3: Verify the result
-------------------------

When the build finishes, open the documentation URL the agent gave you.
You should see a default Docusaurus site served from Read the Docs.

To confirm pull request builds work, ask the agent:

.. code-block:: text

   Create a new branch, change a heading in `docs/docs/intro.md`, push it,
   and open a pull request. Then wait for the Read the Docs check and link me
   to the preview build.

When the check turns green, you can :doc:`review the preview </pull-requests>`
the same way readers will see it.

Step 4: Configure features that need the dashboard
--------------------------------------------------

A handful of Read the Docs features are not yet available through the API.
Ask your agent to open the right pages for you:

.. code-block:: text

   List the Read the Docs features I should enable from the dashboard, with
   the exact URL for each, for project `{slug}`:

   - Visual diff
   - Link previews
   - Automation rule to build only when files under `docs/` or `.readthedocs.yaml` change
   - Email notifications for failed builds

For each one, the agent should point you at a URL like
``https://app.readthedocs.org/dashboard/{slug}/addons/`` or
``https://app.readthedocs.org/dashboard/{slug}/rules/``.
Click through the link, flip the toggle or save the form, and you're done.

See the related documentation pages if you want background:
:doc:`Visual diff </visual-diff>`, :doc:`Link previews </link-previews>`,
:doc:`Automation rules </automation-rules>`,
:doc:`Build notifications </build-notifications>`.

Step 5: Use the agent for ongoing maintenance
---------------------------------------------

Once your project is on Read the Docs, the agent is still useful.
Some prompts to keep handy:

Debug a failed build
   .. code-block:: text

      My latest Read the Docs build failed. Fetch the build log via
      `GET /api/v3/projects/{slug}/builds/{id}/` and tell me what to fix.

Change the Node.js version
   .. code-block:: text

      Update `.readthedocs.yaml` to use Node.js 24, commit, and push.
      Watch the next build and report whether it succeeded.

Add a new documentation version
   .. code-block:: text

      Create a `1.0.x` branch from `main` on GitHub. Then use the Read the Docs
      API to activate the `1.0.x` version and set `stable` as the default version
      for the project.

Where to go from here
---------------------

You've used an AI agent to scaffold a Docusaurus site, host it on Read the Docs,
and wire up pull request builds — without clicking through most of the dashboard.

To keep going:

- Compare what the agent did with the manual :doc:`Docusaurus tutorial </tutorial/docusaurus>`
  so you understand the pieces it touched.
- Read the :doc:`API v3 reference </api/v3>` to see what else the agent can automate.
- Skim :doc:`/intro/doctools` if you want to try the same pattern with a different
  documentation generator.
- Browse :doc:`/guides/index` for deeper how-to guides on specific features.

Happy documenting!
