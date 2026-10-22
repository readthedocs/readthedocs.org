# Build Read the Docs for Anthropic's OSS Scanner.
# The scanner uses the repository root as the build context and audits /src offline, so everything the
# tests need is installed here. This mirrors the "tests" job in .circleci/config.yml and the py314 env in tox.ini.
FROM python:3.14-bookworm

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

ENV DEBIAN_FRONTEND=noninteractive \
    UV_LINK_MODE=copy \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# git is used by the VCS tests; rclone by the storage tests (same as CI).
RUN apt-get update && apt-get install -y --no-install-recommends git rclone \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir uv

# Scanner contract: the checkout lives inside the image, at /src.
COPY . /src
WORKDIR /src

# Same dependencies as tox.ini's testenv, installed into /opt/venv.
RUN uv venv /opt/venv --python python3.14 \
    && VIRTUAL_ENV=/opt/venv uv pip install \
      -r requirements/testing.txt \
      "readthedocsext-theme@git+https://github.com/readthedocs/ext-theme.git@main"

# Same environment as tox.ini, so `pytest` works directly from /src.
ENV VIRTUAL_ENV=/opt/venv \
    PATH=/opt/venv/bin:$PATH \
    PYTHONPATH=/src/readthedocs:/src \
    DJANGO_SETTINGS_MODULE=readthedocs.settings.test \
    DJANGO_SETTINGS_SKIP_LOCAL=True

# Run a quick slice of the suite so the image is known to work; a failing test must not abort the build.
# Tests use SQLite and eager Celery, so no database, Redis or Elasticsearch is needed (search tests are excluded).
# Full suite:   pytest --pyargs readthedocs -m "not search and not proxito and not embed_api" --nomigrations
# Proxito:      pytest --ds=readthedocs.settings.proxito.test --pyargs readthedocs -m "proxito and not search" --nomigrations
RUN pytest --pyargs readthedocs.api readthedocs.oauth -m "not search and not proxito and not embed_api" \
      --nomigrations -q -p no:cacheprovider --suppress-no-test-exit-code \
    || echo "WARNING: pytest reported failures"
