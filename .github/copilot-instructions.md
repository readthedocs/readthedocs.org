# Copilot Instructions for Read the Docs

## Project Overview

Read the Docs is a documentation hosting platform that builds and hosts documentation for open source projects. It supports multiple documentation tools (Sphinx, MkDocs, etc.) and automatically builds documentation from Git repositories.

**Technology Stack:**
- Python 3.x
- Django web framework
- Docker and Docker Compose for development
- PostgreSQL database
- Elasticsearch for search
- Redis for caching and Celery for background tasks

## Development Environment

### Setup
- Development is done using Docker and Docker Compose
- The project requires Docker, Docker Compose, and gVisor (for sandboxed builds)
- Development setup guide: `docs/dev/install.rst`
- Minimum requirements: 10GB disk space, 2GB memory for containers, 8GB total system memory

### Repository Structure
- `readthedocs/` - Main Django application code
- `docs/` - Documentation source (reStructuredText)
- `dockerfiles/` - Docker configuration
- `common/` - Common submodule (shared code)
- `readthedocs/rtd_tests/` - Test suite

## Coding Standards

### Python Code
- Follow PEP 8 style guidelines
- Use Django conventions and best practices
- Write idiomatic Python code
- Keep code modular and maintainable

### Testing
- Tests are located in `readthedocs/rtd_tests/`
- Use pytest as the test runner (configured in `pytest.ini`)
- Write tests for new features and bug fixes
- Test markers available: `search`, `serve`, `proxito`, `embed_api`, `sphinx`
- Run tests with: `pytest`

### Documentation
- Documentation is written in reStructuredText
- Located in `docs/` directory
- Follow existing documentation style and structure
- Build documentation locally to verify changes
- See `docs/dev/docs.rst` for documentation guidelines

## Django-Specific Guidelines

### Models
- Follow Django model conventions
- Use appropriate field types
- Add helpful docstrings and comments
- Include proper `__str__` methods

### Views and URLs
- Use class-based views where appropriate
- Follow REST principles for API endpoints
- Keep views focused and single-purpose
- URL patterns in `readthedocs/urls.py` and app-specific url files

### Templates
- Templates are in `readthedocs/templates/`
- Follow Django template best practices
- Use template inheritance appropriately
- Keep logic in views, not templates

### Settings
- Settings are in `readthedocs/settings/`
- Different settings files for different environments
- Use environment variables for sensitive data

## Code Organization

### Apps
The project is organized into Django apps, each with specific responsibilities:
- `projects/` - Project management
- `builds/` - Build system
- `api/` - REST API
- `oauth/` - OAuth authentication
- `organizations/` - Organization management
- `subscriptions/` - Payment and subscriptions
- And many more in `readthedocs/`

### Common Patterns
- Use Django signals for cross-app communication
- Celery tasks for background processing
- Use Django's ORM for database queries
- Follow the repository pattern for complex queries

## Contributing Guidelines

### Before Submitting Changes
1. Read the full contributing guide: `docs/dev/contribute.rst`
2. Set up your development environment properly
3. Write or update tests for your changes
4. Update documentation if needed
5. Run tests locally to ensure they pass
6. Follow the code style used in the project

### Pull Requests
- Keep changes focused and minimal
- Write clear commit messages
- Reference related issues
- Update tests and documentation
- Ensure CI passes

### Good First Issues
- Look for issues labeled "Good First Issue" on GitHub
- These are designed for newcomers to the project
- Start with these before tackling complex features

## API and External Services

### REST API
- API code is in `readthedocs/api/`
- Use Django REST Framework
- Follow REST conventions
- Document API endpoints

### Integrations
- GitHub, GitLab, Bitbucket integrations in `readthedocs/integrations/`
- OAuth flows in `readthedocs/oauth/`
- Webhook handlers for version control webhooks

## Security Considerations

- Never commit secrets or credentials
- Use environment variables for sensitive configuration
- Follow Django security best practices
- Be aware of OWASP top 10 vulnerabilities
- Use Django's built-in security features (CSRF, XSS protection, etc.)

## Performance

- Be mindful of database query performance
- Use `select_related` and `prefetch_related` for foreign keys
- Cache expensive operations where appropriate
- Consider background tasks for long-running operations

## Front-end

- Front-end code uses HTML, CSS, and JavaScript
- Static files in `readthedocs/static/`
- See `docs/dev/front-end.rst` for front-end guidelines
- Keep JavaScript minimal and progressive enhancement in mind

## Useful Commands

```bash
# Run tests
pytest

# Run specific test markers
pytest -m search

# Run Django management commands
python manage.py <command>

# Build documentation
make -C docs html
```

## Additional Resources

- Full documentation: https://docs.readthedocs.io/
- Contributing guide: https://docs.readthedocs.com/dev/latest/contribute.html
- Development docs: `docs/dev/` directory
- Issue tracker: https://github.com/readthedocs/readthedocs.org/issues
