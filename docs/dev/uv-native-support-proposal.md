# Native `uv` Support Proposal (Issue #11289)

Issue: https://github.com/readthedocs/readthedocs.org/issues/11289

## Context

We want native `uv` support in `python.install` focused on common use cases:

- `requirements.txt`
- `uv.lock`
- selecting dependency groups

This proposal updates the earlier direction with these explicit constraints:

- Prefer using `uv` environment variables such as `UV_PYTHON`, `UV_PROJECT` and `UV_PROJECT_ENVIRONMENT`.
- Define these environment variables inside the director (`director.py`) so they are transparent for the user.
  Do **not** use them as prefix for commands in the frontend: `UV_PROJECT_ENVIRONMENT="$READTHEDOCS_VIRTUALENV_PATH" uv sync`.
- When a project uses `python.install.method: uv`, replace Read the Docs virtualenv creation (`python -mvirtualenv ...`) with an explicit uv environment creation command: `uv env "$READTHEDOCS_VIRTUALENV_PATH"`.
- When using `uv`, skip Read the Docs pip bootstrap commands:
  - `python -m pip install --upgrade --no-cache-dir pip setuptools`
  - `python -m pip install --upgrade --no-cache-dir sphinx`

## Proposed Config Shape

```yaml
python:
  install:
    - method: uv
      operation: sync
      path: .
      groups: [docs]
      extras: null
```

Command called: `uv sync --group docs`.

```yaml
python:
  install:
    - method: uv
      operation: pip
      path: mymodule/awesome
      groups: null
      extras:
        - docs
```

Command called: `uv pip install mymodule/awesome[docs]`.

```yaml
python:
  install:
    - method: uv
      operation: pip
      requirements: docs/requirements.txt
      groups: null
      extras: null
```

Command called: `uv pip install -r docs/requirements.txt`.

### Fields

- `method`: add `uv` (existing: `pip`, `setuptools`)
- `operation`: `sync` or `pip`
- `path`: directory containing the project metadata (default: `.`)
- `requirements`: path to `requirements.txt` file
- `groups`: list of group names or `all`
- `extras`: list of extras names or `all`

## Environment variables

- `UV_PYTHON` is set as `asdf which python`
- `UV_PROJECT_ENVIRONMENT` is set as `$READTHEDOCS_VIRTUALENV_PATH`
- `UV_PROJECT` is set with the value defined in `python.install.path`

## Commands

### Common

Create the environment once, explicitly, using the selected Python:

```bash
uv env "$READTHEDOCS_VIRTUALENV_PATH"
```

Note that the environment will be created with the Python version defined in `UV_PYTHON`.

### `operation: sync`

Base command:

```bash
uv sync
```

Flags mapping:

- `groups: all` -> `--all-groups`
- `groups: ["docs", "lint"]` -> `--group docs --group lint`
- `extras: all` -> `--all-extras`
- `extras: ["pdf", "plot"]` -> `--extra pdf --extra plot`

Examples:

```bash
uv sync --group docs
```

```bash
uv sync --all-groups --all-extras
```

### `operation: pip`

Use `uv pip install` for compatibility flows.

Requirements file:

```bash
uv pip install -r <requirements-file>
```

Local project path install:

```bash
uv pip install .
```

With extras:

```bash
uv pip install ".[docs,pdf]"
```

## Docker Image Changes

To support `method: uv` natively, `uv` must be available in the build environment. Since our Ubuntu images manage toolchains via `asdf`, the following commands need to be added to the Dockerfile:

```dockerfile
RUN asdf plugin add uv && asdf install uv latest
```

At build time, when `python.install` contains any `method: uv` entry, Read the Docs should activate the installed version before running uv commands:

```bash
asdf global uv latest
```

If we don't want to modify our Docker images just yet, we can do the same as we are doing for `pip` where we upgrade it always before start working with the environment. In the case of `uv` we need to call

```bash
asdf plugin add uv
asdf install uv latest
asdf global uv latest
```

The overhead is expected to be comparable to the existing `pip`/`setuptools` upgrade step.
This would be the simplest way and I'd recommend that for now.

## Build Pipeline Changes

### Current behavior to bypass for `uv`

For uv-based installs we should skip:

1. Base venv creation (`python -mvirtualenv $READTHEDOCS_VIRTUALENV_PATH`) and replace it with `uv venv "$READTHEDOCS_VIRTUALENV_PATH"`
2. Core pip bootstrap (`pip setuptools` upgrade)
3. Core Sphinx bootstrap (`sphinx` install)

### New behavior for `uv`

When `python.install` contains any uv entries:

1. Create the environment with `uv venv "$REDTHEDOCS_VIRTUALENV_PATH"`.
2. Do not call RTD core `pip`/`setuptools`/`sphinx` install commands.
3. Execute uv install entries directly (since we are using `UV_` variables)
4. Continue with regular build steps (Sphinx/MkDocs invocation), assuming dependencies come from uv-managed environment.

**Note on `sphinx-build` invocation:** `uv env` produces a standard PEP 405 virtualenv at `$READTHEDOCS_VIRTUALENV_PATH`.
Read the Docs already activates that path (adds its `bin/` to PATH) before invoking build tools, so `sphinx-build` (and `mkdocs`, etc.) remain callable directly — no `uv run sphinx-build` is needed.
The build invocation layer is unchanged.


## Implementation done using `build.jobs` as example

These examples show that the idea works as expected.
We need to implement it natively now :)

### Using `uv sync`

```yaml
version: 2
build:
  os: ubuntu-24.04
  tools:
    python: "3.14"
  jobs:
    pre_create_environment:
      - asdf plugin add uv
      - asdf install uv latest
      - asdf global uv latest
    install:
      - UV_PYTHON=`asdf which python` UV_PROJECT_ENVIRONMENT="$READTHEDOCS_VIRTUALENV_PATH" uv sync
    build:
      html:
        - sphinx-build -T -b html docs $READTHEDOCS_OUTPUT/html
```

- `pre_create_environment` commands won't be needed as they will be automatically executed by Read the Docs at `BuildDirector.install_build_tools`.
- There is no need to call `uv env` since `uv sync` will create the env for us.
- We need to pass `UV_PYTHON` to `uv sync` so it creates the environment using the Python version defined in `build.tools.python` and fails otherwise. It will be set automatically by Read the Docs and won't be shown to users.
- `UV_PROJECT_ENVIRONMENT` will be set automatically by Read the Docs and won't be needed to be prepended in the commands.
- Link to the build using `uv sync`: https://app.readthedocs.org/projects/test-builds/builds/31966279/

### Using `uv pip install -r requirements.txt`

```yaml
version: 2
build:
  os: ubuntu-26.04
  tools:
    python: latest
  jobs:
    pre_create_environment:
      - asdf plugin add uv
      - asdf install uv latest
      - asdf global uv latest
    create_environment:
      - UV_PYTHON=`asdf which python` uv venv $READTHEDOCS_VIRTUALENV_PATH
    install:
      - uv pip install -r requirements.txt
    build:
      html:
        - sphinx-build -T -b html docs $READTHEDOCS_OUTPUT/html
```

- Link to the build  using `uv pip install -r requirements` https://app.readthedocs.org/projects/test-builds/builds/31965642/

## Python version mismatching

If the user select `build.tools.python: 3.12` but then uses `requires-python = ">=3.14"` in `pyproject.toml`,
`uv` will remove the environment and create another one with the pre-compiled Python version they manage:

```bash
 	asdf global python 3.12.10
	asdf plugin add uv
	asdf install uv latest
	asdf global uv latest
	uv venv --python `asdf which python` $READTHEDOCS_VIRTUALENV_PATH
 ```

 ```
	UV_PROJECT_ENVIRONMENT="$READTHEDOCS_VIRTUALENV_PATH" uv sync
Downloading cpython-3.14.3-linux-x86_64-gnu (download) (34.6MiB)
 Downloaded cpython-3.14.3-linux-x86_64-gnu (download)
Using CPython 3.14.3
Removed virtual environment at: /home/docs/checkouts/readthedocs.org/user_builds/test-builds/envs/uv
Creating virtual environment at: /home/docs/checkouts/readthedocs.org/user_builds/test-builds/envs/uv
```

We are explicitly calling `uv sync` with `UV_PYTHON` on porpuse to avoid this behavior and make the build to fail if these versions mismatch.
Otherwise, it will conflict with `build.tools.python` version and it will be pretty confusing.

## Validation Rules

### For `method: uv`

- `operation` is required: `sync` or `pip`
- `path` default is `.`

`operation: sync`

- `groups` allowed (`all` or list)
- `extras` allowed (`all` or list)
- `requirements` not allowed

`operation: pip`

- one of `requirements` or `path` is required
- `groups` not allowed
- `extras` allowed only for local `path` install semantics (`.[extra]`)

General

- reject empty lists for `groups`/`extras` (omit key instead)
- reject invalid mixed forms (`all` + list)

## Compatibility and Rollout

- Existing `pip` and `setuptools` behavior remains unchanged.
- `uv` behavior is opt-in via `method: uv`.
- First iteration should target common flows only; advanced uv options can be added later.
- We considered supporting both `--frozen` and `--locked` in schema, but deferred them because they are not common enough for a first iteration.
- Users that strictly need lockfile behavior can still use `UV_FROZEN=1` or `UV_LOCKED=1` via build environment customization or overwrite the `build.jobs.*` manually.

## Examples to Document Publicly

### Lockfile + docs group

```yaml
python:
  install:
    - method: uv
      operation: sync
      path: .
      groups: [docs]
```

### Lockfile + all groups/extras

```yaml
python:
  install:
    - method: uv
      operation: sync
      path: .
      groups: all
      extras: all
```

### Requirements file compatibility

```yaml
python:
  install:
    - method: uv
      operation: pip
      requirements: docs/requirements.txt
```

### Monorepo project path

```yaml
python:
  install:
    - method: uv
      operation: sync
      path: packages/docs-site
      groups: [docs]
```
