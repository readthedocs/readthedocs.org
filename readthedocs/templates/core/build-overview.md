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
{% if diff.added %}{% if diff.added|length == 1 %}
<p>➕ <a href="{{ diff.added.0.url }}">{{ diff.added.0.path }}</a></p>
{% else %}
<p><strong>➕ Added</strong></p>
<ul>
{% for file in diff.added %}<li><a href="{{ file.url }}">{{ file.path }}</a></li>
{% endfor %}</ul>
{% endif %}{% endif %}{% if diff.modified %}{% if diff.should_auto_expand %}
<details>
<summary>📝 {{ diff.modified|length }} modified</summary>
{% else %}
<p><strong>📝 Modified</strong></p>
{% endif %}<ul>
{% for file in diff.modified %}<li><a href="{{ file.url }}">{{ file.path }}</a></li>
{% endfor %}</ul>
{% if diff.should_auto_expand %}</details>
{% endif %}{% endif %}{% if diff.deleted %}{% if diff.should_auto_expand %}
<details>
<summary>➖ {{ diff.deleted|length }} deleted</summary>
{% else %}
<p><strong>➖ Deleted</strong></p>
{% endif %}<ul>
{% for file in diff.deleted %}<li><a href="{{ file.url }}">{{ file.path }}</a></li>
{% endfor %}</ul>
{% if diff.should_auto_expand %}</details>
{% endif %}{% endif %}
</details>
{% else %}
No files changed.
{% endif %}
