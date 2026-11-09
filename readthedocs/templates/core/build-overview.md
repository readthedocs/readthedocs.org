{% comment %}
Template used for generating the build overview page that is posted as a comment on the build PR.

Whitespaces and newlines are important in some places like lists and tables,
make sure to adjust the tags accordingly, as they introduce newlines.

Markdown inside <details> requires a blank line after </summary>.
{% endcomment %}
{% if diff.files %}{% if diff.single_status %}📖 **{{ diff.files|length }} file{{ diff.files|length|pluralize }} {{ diff.single_status }}**{% else %}📖 **{{ diff.files|length }} file{{ diff.files|length|pluralize }} changed** · {{ diff.summary }}{% endif %}

{% for file in diff.deleted|slice:":10" %}- `-` `{{ file.path }}` · [add redirect](https://{{ PRODUCTION_DOMAIN }}{% url "projects_redirects_create" project.slug %}?redirect_type=page&from_url=/{{ file.path|urlencode }})
{% endfor %}{% if diff.deleted|length > 10 %}- *and {{ diff.deleted|length|add:"-10" }} more deleted — see the [build overview]({{ build_url }})*
{% endif %}{% for file in diff.added|slice:":10" %}- `+` [`{{ file.path }}`]({{ file.url }})
{% endfor %}{% if diff.added|length > 10 %}- *and {{ diff.added|length|add:"-10" }} more added — see the [build overview]({{ build_url }})*
{% endif %}{% if diff.modified %}{% if not diff.should_auto_expand %}{% if diff.deleted or diff.added %}
{% endif %}<details>
<summary>Modified files</summary>

{% endif %}{% for file in diff.modified|slice:":10" %}- `±` [`{{ file.path }}`]({{ file.url }}){% if file.diff_url %} · [diff]({{ file.diff_url }}){% endif %}
{% endfor %}{% if diff.modified|length > 10 %}- *and {{ diff.modified|length|add:"-10" }} more — see the [build overview]({{ build_url }})*
{% endif %}{% if not diff.should_auto_expand %}</details>
{% endif %}{% endif %}{% else %}📖 **No files changed** — your changes didn't affect any published file.
{% endif %}
---
[Preview]({{ preview_url }}) · [{{ project.name }} build overview]({{ build_url }}) · built {{ built_at|date:"j M Y, H:i T" }}
