{% comment %}
Template used for generating the build overview page that is posted as a comment on the build PR.

Whitespaces and newlines are important in some places like lists and tables,
make sure to adjust the tags accordingly, as they introduce newlines.

Markdown inside <details> requires a blank line after </summary>.
{% endcomment %}
{% if diff.files %}📖 **{{ diff.files|length }} file{{ diff.files|length|pluralize }} changed** — [preview the docs]({{ preview_url }})
{% if diff.should_auto_expand %}
<details open>
<summary>{{ diff.summary }}</summary>
<br>
{% for file in diff.added %}<code>+</code> <a href="{{ file.url }}"><code>{{ file.path }}</code></a><br>
{% endfor %}{% for file in diff.modified %}<code>±</code> <a href="{{ file.url }}"><code>{{ file.path }}</code></a><br>
{% endfor %}{% for file in diff.deleted %}<code>-</code> <code>{{ file.path }}</code> (<a href="https://{{ PRODUCTION_DOMAIN }}{% url "projects_redirects_create" project.slug %}?redirect_type=page&amp;from_url=/{{ file.path|urlencode }}">add redirect</a>)<br>
{% endfor %}</details>
{% else %}
<details>
<summary>{{ diff.summary }}</summary>
<br>
{% if diff.added %}
`+` **Added**
{% for file in diff.added|slice:":10" %}- [`{{ file.path }}`]({{ file.url }})
{% endfor %}{% if diff.added|length > 10 %}- *and {{ diff.added|length|add:"-10" }} more...*
{% endif %}{% endif %}{% if diff.modified %}
`±` **Modified**
{% for file in diff.modified|slice:":10" %}- [`{{ file.path }}`]({{ file.url }})
{% endfor %}{% if diff.modified|length > 10 %}- *and {{ diff.modified|length|add:"-10" }} more...*
{% endif %}{% endif %}{% if diff.deleted %}
`-` **Deleted**
{% for file in diff.deleted|slice:":10" %}- `{{ file.path }}` ([add redirect](https://{{ PRODUCTION_DOMAIN }}{% url "projects_redirects_create" project.slug %}?redirect_type=page&from_url=/{{ file.path|urlencode }}))
{% endfor %}{% if diff.deleted|length > 10 %}- *and {{ diff.deleted|length|add:"-10" }} more...*
{% endif %}{% endif %}
</details>
{% endif %}{% else %}📖 **No files changed** — [preview the docs]({{ preview_url }})

Your changes didn't affect any published file.
{% endif %}
---
[Build overview](https://{{ PRODUCTION_DOMAIN }}{% url "builds_detail" project.slug current_version_build.pk %}) · last updated {{ last_updated|date:"j M Y, H:i T" }}
