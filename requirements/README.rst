Requirements files
==================

This is where we keep the dependency information for our various project parts.

We are using ``pip-tools`` to track our main dependencies in the ``.in`` files.
Then, we "compile" these main dependencies with ``pip-compile`` that result in ``.txt`` files
with all the main dependencies pinned together with their own transitive dependencies pinned as well.
This allow us have reproducible environments.


Auto-update dependencies
------------------------

We use a GitHub Action (``.github/workflows/pip-tools.yaml``) to run ``pip-compile`` on a weekly basis and keep all our dependencies updated.
This action creates a Pull Request with the changes.
In case we are not happy with these changes,
we need to pin the main dependencies to the version we want and write a comment explaining why we are pinning it.
After that, we can re-run the GitHub Action to update the ``.txt`` files.
