# AI Instructions for Read the Docs

This file lives in the `common` repo,
and is copied to each production repo.
Agents don't work with symlinks or submodules,
so this is best for now.

## Team interaction

We want all interaction in public to be between real people.

- **Never** comment on pull requests, commits, or other things as the user.
- Make all public-facing copy like commit messages and pull request descriptions for the reader, and not the author.
- Ensure everything is optimized for clarify, conciseness, and effective communication.

## Project Overview

Read the Docs is a documentation hosting platform that builds and hosts documentation for open source projects.
It supports multiple documentation tools (Sphinx, MkDocs, etc.) and automatically builds documentation from Git repositories.

**Technology Stack:**

- Python 3.14
- Django web framework
- Docker and Docker Compose for development
- PostgreSQL database
- Elasticsearch for search
- Redis for caching and Celery for background tasks

## Commits

- Use short descriptive commit messages
- Only provide simple context, and don't be overly verbose
- Always run `pre-commit run --files <changed files>` before committing to ensure code passes all checks

## Pull Requests

- Always open pull requests as drafts
- Use feature branches for all changes
- Name branches `claude/<short-description>`, e.g. `claude/docs-direct-upload-business`
- Never open pull requests or push commits for security fixes without asking first.
  Public PRs can disclose vulnerabilities before they're patched in production.
- Prefix pull request titles, example `Api:`, `Builds:`, or `Docs:`.
- Open with a summary a human wrote or chose: the shortest text a reader can take in to know what the pull request is for and whether it deserves their attention. One or two sentences; a screenshot too when one shows the change. Before opening the pull request, ask the author for it. They may lift a sentence from your write-up, but it leads only once they have chosen it. Never open with your own text.
- Put your own write-up below that, inside `<details>`, with the model name (and effort level, if you know it) as the `<summary>` — `<summary>Claude Opus 5.5</summary>`. That line is the note that the rest is agent-written: don't add another, and some hosts append a footer of their own. Include the session link inside, if there is one. This is the details-summary pattern: https://simonwillison.net/2026/Nov/9/details-summary/
- Inside it, write for a reviewer with two minutes, as plain paragraphs in this order:
  1. The problem: what was wrong or missing.
  2. The approach, and anything the diff doesn't make obvious: a judgement call, a side fix made along the way, a behavior change.
  3. What the reviewer or merger has to do, if anything: a redirect to add, a setting to change, a follow-up this unblocks.
- Link the issues and pull requests it relates to, and include whatever other context helps the reviewer.
- Don't restate _what_ changed — no "Changes" section, changelog, file lists, or per-change bullets — since the diff already shows that.
- Decide, don't ask: state the choice made and why in a clause, not as an open question to the reviewer.
- Don't include a test plan unless the change can't be verified from the diff.

## Package Management

- Always use `uv` for Python package management and virtual environment operations
- Use `uv pip install` instead of `pip install`
- Use `uv run` to execute Python scripts in the virtual environment

## Docs

- Follow the style guide at https://github.com/readthedocs/readthedocs.org/blob/main/docs/dev/style-guide.rst.
- Always use the marketing name used in the public-facing docs, and not the internal code names referenced in code.
- The `user` directory is public docs, and `dev` is dev-focused. Most of what we do is focus on the user-facing docs.

## Website copy

- Direct, second-person voice. No jargon. Less is more.
- Focus on user benefit, not abstract positioning.
- Don't repeat facts within a section; use standard terminology (e.g. "files changed", "pull request").

## Testing

- Use `pytest` with the `assert foo == bar` assertion style
- Keep the test DB warm with `pytest --reuse-db` to speed up runs

### Running tests locally

Tests do **not** require Docker — they run via `tox` with SQLite and `readthedocs.settings.test`.
Docker Compose is only for the development server.

```bash
# Validate migrations (run after any migration change)
tox -e migrations

# Run linting and formatting checks
tox -e pre-commit

# Run the main test suite (search, proxito, and embed_api tests are excluded by default)
tox -e py314 -- --nomigrations

# Run tests matching a keyword (faster) — use -k because --pyargs readthedocs is hardcoded
tox -e py314 -- -k "<keyword>" --reuse-db --nomigrations

# Run only search tests (requires Elasticsearch sidecar in CI, skip locally unless available)
tox -e search
```

### Migration validation

Always run `tox -e migrations` after adding or modifying migration files. This runs
`manage.py makemigrations --check --dry-run` and catches missing or inconsistent migrations
before they cause `IntegrityError` failures at deploy time.

## Logging

- Use `structlog` keyword arguments for context, never string interpolation
- Name keys as `<model>_<field>`: `project_slug`, `build_id`, `user_username`, `organization_slug`
- Use `_id`, not `_pk`: `invitation_id=invitation.pk`
- Don't use bare keys like `project=`, `build=`, or `username=`
- Bind repeated context once with `log.bind(...)` instead of passing it to every call

## Front-end

- Most templates/css/js are in a separate repository (https://github.com/readthedocs/ext-theme/).
- Fomantic UI is the design system. Use an existing variation before adding CSS, and never use inline styles or `!important`.
- Name custom CSS as a variation on the Fomantic element it extends, like `.ui.invertable.image` or `.ui.labeled.image`, and keep it in that element's `.overrides` file in the theme.
- Take colors from the theme variables (`@primaryColor`, `@secondaryColor`), not hex values or named colors.
- In templates, use Django comments and named blocks, load tags explicitly, and wrap user-facing strings in `{% trans %}`.
- Rebuild and commit the theme's static assets after changing styles or JavaScript.
