{% comment %}
Template used for generating the build overview page that is posted as a comment on the build PR.

Whitespaces and newlines are important in some places like lists and tables,
make sure to adjust the tags accordingly, as they introduce newlines.

Markdown inside <details> requires a blank line after </summary>.
{% endcomment %}
### Documentation build overview

{% if current_version_build.state == "cancelled" %}🚫 **Build cancelled**{% elif not current_version_build.finished %}⏳ **Build in progress**{% elif current_version_build.success %}✅ **Build successful**{% else %}❌ **Build failed**{% endif %} · _Updated {{ now|date:"Y-m-d H:i T" }}_

[![Preview build](https://img.shields.io/badge/%F0%9F%94%8D%20Preview%20build-0066CC?style=for-the-badge&labelColor=0066CC)]({{ current_version.get_absolute_url }})

<details>
<summary>Build details</summary>
<br>

📚 [{{ project.name }}](https://{{ PRODUCTION_DOMAIN }}{% url "projects_detail" project.slug %}) · 🛠️ Build [#{{ current_version_build.pk }}](https://{{ PRODUCTION_DOMAIN }}{% url "builds_detail" project.slug current_version_build.pk %}) · 📁 Comparing {{ current_version_build.commit }} against [{{ base_version.verbose_name }}]({{ base_version.get_absolute_url }}) ({{ base_version_build.commit }})

</details>

{% if diff.files %}{% if diff.should_auto_expand %}
<details open>
<summary>{{ diff.files|length }} file{{ diff.files|length|pluralize }} changed</summary>
<br>
{% for file in diff.added %}<code>+</code> <a href="{{ file.url }}"><code>{{ file.path }}</code></a><br>
{% endfor %}{% for file in diff.modified %}<code>±</code> <a href="{{ file.url }}"><code>{{ file.path }}</code></a><br>
{% endfor %}{% for file in diff.deleted %}<code>-</code> <a href="{{ file.url }}"><code>{{ file.path }}</code></a><br>
{% endfor %}</details>
{% else %}
<details>
<summary>{{ diff.files|length }} file{{ diff.files|length|pluralize }} changed{% if diff.added %} · <code>+</code> {{ diff.added|length }} added{% endif %}{% if diff.modified %} · <code>±</code> {{ diff.modified|length }} modified{% endif %}{% if diff.deleted %} · <code>-</code> {{ diff.deleted|length }} deleted{% endif %}</summary>
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
{% for file in diff.deleted|slice:":10" %}- [`{{ file.path }}`]({{ file.url }})
{% endfor %}{% if diff.deleted|length > 10 %}- *and {{ diff.deleted|length|add:"-10" }} more...*
{% endif %}{% endif %}
</details>
{% endif %}{% else %}
No files changed.
{% endif %}
