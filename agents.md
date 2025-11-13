# agents.md

## Fast Linting with uv

To run all pre-commit linters using uv (fast, isolated):

```bash
uv pip install pre-commit
uv run -- pre-commit run --all-files --show-diff-on-failure
```

This will install pre-commit and run all configured hooks without polluting your global environment.

## Fast Testing with uv

To run your test suite using uv (isolated, fast):

```bash
uv pip install -r requirements/testing.txt
uv run -- pytest
```

This installs test dependencies and runs pytest without affecting your global environment.

### Running specific tests (example)

To run a specific test (like you would with tox -e py3 -- --no-migrations -k test_project_delete_triggers_pageview_cleanup):

```bash
uv pip install -r requirements/testing.txt
uv run -- pytest --no-migrations -k test_project_delete_triggers_pageview_cleanup
```
