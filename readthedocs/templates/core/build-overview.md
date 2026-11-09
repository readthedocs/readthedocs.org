{% comment %}
Template used for generating the build overview page that is posted as a comment on the build PR.

Whitespaces and newlines are important in some places like lists and tables,
make sure to adjust the tags accordingly, as they introduce newlines.

Markdown inside <details> requires a blank line after </summary>.
{% endcomment %}
{% if diff.files %}{% if diff.should_collapse %}<details>
<summary>📖 {{ diff.headline }}</summary>

{% else %}📖 {{ diff.headline }}

{% endif %}{% for file in diff.added|slice:":10" %}- `+` [`{{ file.path }}`]({{ file.url }})
{% endfor %}{% if diff.added|length > 10 %}- *and {{ diff.added|length|add:"-10" }} more added*
{% endif %}{% for file in diff.modified|slice:":10" %}- `±` [`{{ file.path }}`]({{ file.url }}){% if file.diff_url %} · [diff]({{ file.diff_url }}){% endif %}
{% endfor %}{% if diff.modified|length > 10 %}- *and {{ diff.modified|length|add:"-10" }} more modified*
{% endif %}{% for file in diff.deleted|slice:":10" %}- `-` `{{ file.path }}` · [add redirect](https://{{ PRODUCTION_DOMAIN }}{% url "projects_redirects_create" project.slug %}?redirect_type=page&from_url={{ file.redirect_from_url|urlencode }})
{% endfor %}{% if diff.deleted|length > 10 %}- *and {{ diff.deleted|length|add:"-10" }} more deleted*
{% endif %}{% if diff.should_collapse %}</details>
{% endif %}{% else %}📖 No files changed
{% endif %}
---
[Preview]({{ preview_url }}) · [{{ project.name }} build overview]({{ build_url }}) · built {{ built_at|date:"DATETIME_FORMAT" }} UTC
