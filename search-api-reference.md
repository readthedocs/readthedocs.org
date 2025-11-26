# Read the Docs Search API - curl Reference for AI Agents

Quick reference for AI agents to search Read the Docs documentation programmatically.

## Base Configuration

```bash
API_BASE="https://app.readthedocs.org/api/v3/search/"
# For commercial: "https://app.readthedocs.com/api/v3/search/"
```

## Core Search Command

```bash
# Basic search
curl -s "https://app.readthedocs.org/api/v3/search/?q=project:PROJECT_SLUG+QUERY&page_size=50"

# With jq for pretty printing
curl -s "https://app.readthedocs.org/api/v3/search/?q=project:PROJECT_SLUG+QUERY&page_size=50" | jq

# URL encode spaces and special characters
# Use + for spaces or %20
# project:docs authentication → project:docs+authentication
```

## Response Structure

```json
{
    "count": 41,
    "next": "url_to_next_page",
    "previous": null,
    "projects": [
        {"slug": "docs", "versions": [{"slug": "latest"}]}
    ],
    "query": "processed_query",
    "results": [
        {
            "type": "page",
            "project": {"slug": "docs", "alias": null},
            "version": {"slug": "latest"},
            "title": "Page Title",
            "domain": "https://docs.readthedocs.io",
            "path": "/en/latest/page.html",
            "highlights": {
                "title": ["<span>matched</span> term"]
            },
            "blocks": [
                {
                    "type": "section",
                    "id": "section-id",
                    "title": "Section Title",
                    "content": "Section text...",
                    "highlights": {
                        "content": ["text with <span>matched</span> terms"]
                    }
                }
            ]
        }
    ]
}
```

## Query Syntax for AI Agents

### Project Targeting
```bash
# Single project, default version
curl -s 'https://app.readthedocs.org/api/v3/search/?q=project:docs+authentication'

# Specific version
curl -s 'https://app.readthedocs.org/api/v3/search/?q=project:docs/latest+authentication'

# Multiple projects
curl -s 'https://app.readthedocs.org/api/v3/search/?q=project:docs+project:django+api'

# Include subprojects
curl -s 'https://app.readthedocs.org/api/v3/search/?q=subprojects:docs/latest+configuration'
```

### Advanced Search Operators
```bash
# Exact phrase (most useful for precise matches)
curl -s 'https://app.readthedocs.org/api/v3/search/?q=project:docs+"configuration+file"'

# Prefix search (find variations)
# matches: config, configuration, configure
curl -s 'https://app.readthedocs.org/api/v3/search/?q=project:docs+config*'

# Fuzzy search (handle typos)
# finds "authentication"
curl -s 'https://app.readthedocs.org/api/v3/search/?q=project:docs+authenitcation~2'

# Proximity search (words near each other)
# "build" and "docker" within 3 words
curl -s 'https://app.readthedocs.org/api/v3/search/?q=project:docs+"build+docker"~3'
```

## Common AI Agent Patterns

### 1. Find Documentation About Specific Topic
```bash
# Get documentation pages about a specific topic
curl -s 'https://app.readthedocs.org/api/v3/search/?q=project:django+authentication+middleware&page_size=10' | jq

# Extract just titles and URLs
curl -s 'https://app.readthedocs.org/api/v3/search/?q=project:django+authentication&page_size=10' | \
  jq -r '.results[] | "\(.title): \(.domain)\(.path)"'
```

### 2. Extract Content from Search Results
```bash
# Extract all text content for LLM context
curl -s 'https://app.readthedocs.org/api/v3/search/?q=project:requests+authentication' | \
  jq -r '.results[] | "## \(.title)\nSource: \(.domain)\(.path)\n\n\(.blocks[] | "### \(.title)\n\(.content)\n")"'

# Get just block content
curl -s 'https://app.readthedocs.org/api/v3/search/?q=project:requests+authentication' | \
  jq -r '.results[].blocks[].content'
```

### 3. Search Multiple Related Projects
```bash
# Search across multiple related projects (Django ecosystem)
curl -s 'https://app.readthedocs.org/api/v3/search/?q=project:django+project:django-rest-framework+project:celery+task+queue&page_size=50' | jq
```

### 4. Get All Results (Pagination)
```bash
# Fetch first page
curl -s 'https://app.readthedocs.org/api/v3/search/?q=project:sphinx+extension&page_size=50&page=1' | jq

# Fetch next page (use the 'next' URL from response)
curl -s 'https://app.readthedocs.org/api/v3/search/?q=project:sphinx+extension&page_size=50&page=2' | jq

# Check if there are more pages
curl -s 'https://app.readthedocs.org/api/v3/search/?q=project:sphinx+extension&page_size=50' | jq '.next'
```

### 5. Find Code Examples
```bash
# Search for pages likely containing code examples
curl -s 'https://app.readthedocs.org/api/v3/search/?q=project:flask+authentication+code*+example*+tutorial*+guide*&page_size=20' | \
  jq -r '.results[] | select(.title | test("example|tutorial|guide|howto"; "i")) | "\(.domain)\(.path)"'
```

### 6. Check Documentation Coverage
```bash
# Check how many documentation pages exist for each topic
curl -s 'https://app.readthedocs.org/api/v3/search/?q=project:django+authentication&page_size=1' | jq '.count'
curl -s 'https://app.readthedocs.org/api/v3/search/?q=project:django+database&page_size=1' | jq '.count'
curl -s 'https://app.readthedocs.org/api/v3/search/?q=project:django+caching&page_size=1' | jq '.count'
curl -s 'https://app.readthedocs.org/api/v3/search/?q=project:django+deployment&page_size=1' | jq '.count'
```

## Quick Reference for AI Agents

```bash
# Basic search
curl -s 'https://app.readthedocs.org/api/v3/search/?q=project:PROJECT-SLUG+SEARCH+TERMS'

# Specific version
curl -s 'https://app.readthedocs.org/api/v3/search/?q=project:PROJECT-SLUG/latest+SEARCH+TERMS'

# Include subprojects
curl -s 'https://app.readthedocs.org/api/v3/search/?q=subprojects:PROJECT-SLUG+SEARCH+TERMS'

# Exact phrase
curl -s 'https://app.readthedocs.org/api/v3/search/?q=project:PROJECT-SLUG+"exact+phrase"'

# Fuzzy search (typo tolerance)
curl -s 'https://app.readthedocs.org/api/v3/search/?q=project:PROJECT-SLUG+word~2'

# Prefix search
curl -s 'https://app.readthedocs.org/api/v3/search/?q=project:PROJECT-SLUG+prefix*'
```

## Response Parsing with jq

```bash
# Get just URLs
curl -s 'https://app.readthedocs.org/api/v3/search/?q=project:docs+api' | \
  jq -r '.results[] | "\(.domain)\(.path)"'

# Get titles and URLs
curl -s 'https://app.readthedocs.org/api/v3/search/?q=project:docs+api' | \
  jq -r '.results[] | "\(.title): \(.domain)\(.path)"'

# Extract all block content
curl -s 'https://app.readthedocs.org/api/v3/search/?q=project:docs+api' | \
  jq -r '.results[].blocks[].content'

# Check which projects were actually searched
curl -s 'https://app.readthedocs.org/api/v3/search/?q=project:docs+api' | \
  jq '.projects[] | {slug: .slug, versions: [.versions[].slug]}'
```

## Common Projects to Search

```bash
# Popular Python projects
docs           # Python official docs
django         # Django
flask          # Flask
requests       # Requests
numpy          # NumPy
pandas-docs    # Pandas
sphinx         # Sphinx
pytest         # pytest
sqlalchemy     # SQLAlchemy

# Example usage
curl -s 'https://app.readthedocs.org/api/v3/search/?q=project:django+models' | jq
```

---

*API Endpoint: `https://app.readthedocs.org/api/v3/search/`*
*Max page_size: 50 | Max projects per query: 100*
