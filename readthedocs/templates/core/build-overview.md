{% comment %}
Template used for generating the build overview page that is posted as a comment on the build PR.

Whitespaces and newlines are important in some places like lists and tables,
make sure to adjust the tags accordingly, as they introduce newlines.
{% endcomment %}
### Documentation build overview

> 📚 [{{ project.name }}](https://{{ PRODUCTION_DOMAIN }}{% url "projects_detail" project.slug %}) | 🛠️ Build [#{{ current_version_build.pk }}](https://{{ PRODUCTION_DOMAIN }}{% url "builds_detail" project.slug current_version_build.pk %}) | 📁 Comparing {{ current_version_build.commit }} against [{{ base_version.verbose_name }}]({{ base_version.get_absolute_url }}) ({{ base_version_build.commit }})

[<kbd> &nbsp; 🔍 Preview build &nbsp; </kbd>]({{ current_version.get_absolute_url }})

{% if diff.files %}
<details{% if diff.should_auto_expand %} open{% endif %}>
<summary>{{ diff.files|length }} files changed{% if diff.added %} · ➕ {{ diff.added|length }} added{% endif %}{% if diff.modified %} · 📝 {{ diff.modified|length }} modified{% endif %}{% if diff.deleted %} · ➖ {{ diff.deleted|length }} deleted{% endif %}</summary>
<table>
{% if diff.added %}<tr><th align="left" colspan="2">➕ Added</th></tr>
{% for file in diff.added %}<tr><td>&nbsp;&nbsp;<a href="{{ file.url }}">{{ file.path }}</a></td></tr>
{% endfor %}{% endif %}{% if diff.modified %}<tr><th align="left" colspan="2">📝 Modified</th></tr>
{% for file in diff.modified %}<tr><td>&nbsp;&nbsp;<a href="{{ file.url }}">{{ file.path }}</a></td></tr>
{% endfor %}{% endif %}{% if diff.deleted %}<tr><th align="left" colspan="2">➖ Deleted</th></tr>
{% for file in diff.deleted %}<tr><td>&nbsp;&nbsp;<a href="{{ file.url }}">{{ file.path }}</a></td></tr>
{% endfor %}{% endif %}</table>
</details>
{% else %}
No files changed.
{% endif %}
