# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from __future__ import absolute_import
from django.db import models, migrations
from django.conf import settings
import taggit.managers


class Migration(migrations.Migration):

    dependencies = [
        ('taggit', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='EmailHook',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('email', models.EmailField(max_length=254)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Project',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('pub_date', models.DateTimeField(auto_now_add=True, verbose_name='Publication date')),
                ('modified_date', models.DateTimeField(auto_now=True, verbose_name='Modified date')),
                ('name', models.CharField(max_length=255, verbose_name='Name')),
                ('slug', models.SlugField(unique=True, max_length=255, verbose_name='Slug')),
                ('description', models.TextField(help_text='The reStructuredText description of the project', verbose_name='Description', blank=True)),
                ('repo', models.CharField(help_text='Hosted documentation repository URL', max_length=255, verbose_name='Repository URL')),
                ('repo_type', models.CharField(default=b'git', max_length=10, verbose_name='Repository type', choices=[(b'git', 'Git'), (b'svn', 'Subversion'), (b'hg', 'Mercurial'), (b'bzr', 'Bazaar')])),
                ('project_url', models.URLField(help_text="The project's homepage", verbose_name='Project homepage', blank=True)),
                ('canonical_url', models.URLField(help_text='URL that documentation is expected to serve from', verbose_name='Canonical URL', blank=True)),
                ('version', models.CharField(help_text='Project version these docs apply to, i.e. 1.0a', max_length=100, verbose_name='Version', blank=True)),
                ('copyright', models.CharField(help_text='Project copyright information', max_length=255, verbose_name='Copyright', blank=True)),
                ('theme', models.CharField(default=b'default', help_text='<a href="http://sphinx.pocoo.org/theming.html#builtin-themes" target="_blank">Examples</a>', max_length=20, verbose_name='Theme', choices=[(b'default', 'Default'), (b'sphinxdoc', 'Sphinx Docs'), (b'traditional', 'Traditional'), (b'nature', 'Nature'), (b'haiku', 'Haiku')])),
                ('suffix', models.CharField(default=b'.rst', verbose_name='Suffix', max_length=10, editable=False)),
                ('single_version', models.BooleanField(default=False, help_text='A single version site has no translations and only your "latest" version, served at the root of the domain. Use this with caution, only turn it on if you will <b>never</b> have multiple versions of your docs.', verbose_name='Single version')),
                ('default_version', models.CharField(default=b'latest', help_text='The version of your project that / redirects to', max_length=255, verbose_name='Default version')),
                ('default_branch', models.CharField(default=None, max_length=255, blank=True, help_text='What branch "latest" points to. Leave empty to use the default value for your VCS (eg. <code>trunk</code> or <code>master</code>).', null=True, verbose_name='Default branch')),
                ('requirements_file', models.CharField(default=None, max_length=255, blank=True, help_text='Requires Virtualenv. A <a href="https://pip.pypa.io/en/latest/user_guide.html#requirements-files">pip requirements file</a> needed to build your documentation. Path from the root of your project.', null=True, verbose_name='Requirements file')),
                ('documentation_type', models.CharField(default=b'auto', help_text='Type of documentation you are building. <a href="http://sphinx-doc.org/builders.html#sphinx.builders.html.DirectoryHTMLBuilder">More info</a>.', max_length=20, verbose_name='Documentation type', choices=[(b'auto', 'Automatically Choose'), (b'sphinx', 'Sphinx Html'), (b'mkdocs', 'Mkdocs (Markdown)'), (b'sphinx_htmldir', 'Sphinx HtmlDir'), (b'sphinx_singlehtml', 'Sphinx Single Page HTML')])),
                ('allow_comments', models.BooleanField(default=False, verbose_name='Allow Comments')),
                ('comment_moderation', models.BooleanField(default=False, verbose_name='Comment Moderation)')),
                ('analytics_code', models.CharField(help_text='Google Analytics Tracking ID (ex. <code>UA-22345342-1</code>). This may slow down your page loads.', max_length=50, null=True, verbose_name='Analytics code', blank=True)),
                ('enable_epub_build', models.BooleanField(default=True, help_text='Create a EPUB version of your documentation with each build.', verbose_name='Enable EPUB build')),
                ('enable_pdf_build', models.BooleanField(default=True, help_text='Create a PDF version of your documentation with each build.', verbose_name='Enable PDF build')),
                ('path', models.CharField(help_text='The directory where <code>conf.py</code> lives', verbose_name='Path', max_length=255, editable=False)),
                ('conf_py_file', models.CharField(default=b'', help_text='Path from project root to <code>conf.py</code> file (ex. <code>docs/conf.py</code>).Leave blank if you want us to find it for you.', max_length=255, verbose_name='Python configuration file', blank=True)),
                ('featured', models.BooleanField(default=False, verbose_name='Featured')),
                ('skip', models.BooleanField(default=False, verbose_name='Skip')),
                ('mirror', models.BooleanField(default=False, verbose_name='Mirror')),
                ('use_virtualenv', models.BooleanField(default=False, help_text='Install your project inside a virtualenv using <code>setup.py install</code>', verbose_name='Use virtualenv')),
                ('python_interpreter', models.CharField(default=b'python', help_text='(Beta) The Python interpreter used to create the virtual environment.', max_length=20, verbose_name='Python Interpreter', choices=[(b'python', 'CPython 2.x'), (b'python3', 'CPython 3.x')])),
                ('use_system_packages', models.BooleanField(default=False, help_text='Give the virtual environment access to the global site-packages dir.', verbose_name='Use system packages')),
                ('django_packages_url', models.CharField(max_length=255, verbose_name='Django Packages URL', blank=True)),
                ('privacy_level', models.CharField(default=b'public', help_text='(Beta) Level of privacy that you want on the repository. Protected means public but not in listings.', max_length=20, verbose_name='Privacy Level', choices=[(b'public', 'Public'), (b'protected', 'Protected'), (b'private', 'Private')])),
                ('version_privacy_level', models.CharField(default=b'public', help_text='(Beta) Default level of privacy you want on built versions of documentation.', max_length=20, verbose_name='Version Privacy Level', choices=[(b'public', 'Public'), (b'protected', 'Protected'), (b'private', 'Private')])),
                ('language', models.CharField(default=b'en', help_text="The language the project documentation is rendered in. Note: this affects your project's URL.", max_length=20, verbose_name='Language', choices=[(b'aa', b'Afar'), (b'ab', b'Abkhaz'), (b'af', b'Afrikaans'), (b'am', b'Amharic'), (b'ar', b'Arabic'), (b'as', b'Assamese'), (b'ay', b'Aymara'), (b'az', b'Azerbaijani'), (b'ba', b'Bashkir'), (b'be', b'Belarusian'), (b'bg', b'Bulgarian'), (b'bh', b'Bihari'), (b'bi', b'Bislama'), (b'bn', b'Bengali'), (b'bo', b'Tibetan'), (b'br', b'Breton'), (b'ca', b'Catalan'), (b'co', b'Corsican'), (b'cs', b'Czech'), (b'cy', b'Welsh'), (b'da', b'Danish'), (b'de', b'German'), (b'dz', b'Dzongkha'), (b'el', b'Greek'), (b'en', b'English'), (b'eo', b'Esperanto'), (b'es', b'Spanish'), (b'et', b'Estonian'), (b'eu', b'Basque'), (b'fa', b'Iranian'), (b'fi', b'Finnish'), (b'fj', b'Fijian'), (b'fo', b'Faroese'), (b'fr', b'French'), (b'fy', b'Western Frisian'), (b'ga', b'Irish'), (b'gd', b'Scottish Gaelic'), (b'gl', b'Galician'), (b'gn', b'Guarani'), (b'gu', b'Gujarati'), (b'ha', b'Hausa'), (b'hi', b'Hindi'), (b'he', b'Hebrew'), (b'hr', b'Croatian'), (b'hu', b'Hungarian'), (b'hy', b'Armenian'), (b'ia', b'Interlingua'), (b'id', b'Indonesian'), (b'ie', b'Interlingue'), (b'ik', b'Inupiaq'), (b'is', b'Icelandic'), (b'it', b'Italian'), (b'iu', b'Inuktitut'), (b'ja', b'Japanese'), (b'jv', b'Javanese'), (b'ka', b'Georgian'), (b'kk', b'Kazakh'), (b'kl', b'Kalaallisut'), (b'km', b'Khmer'), (b'kn', b'Kannada'), (b'ko', b'Korean'), (b'ks', b'Kashmiri'), (b'ku', b'Kurdish'), (b'ky', b'Kyrgyz'), (b'la', b'Latin'), (b'ln', b'Lingala'), (b'lo', b'Lao'), (b'lt', b'Lithuanian'), (b'lv', b'Latvian'), (b'mg', b'Malagasy'), (b'mi', b'Maori'), (b'mk', b'Macedonian'), (b'ml', b'Malayalam'), (b'mn', b'Mongolian'), (b'mr', b'Marathi'), (b'ms', b'Malay'), (b'mt', b'Maltese'), (b'my', b'Burmese'), (b'na', b'Nauru'), (b'ne', b'Nepali'), (b'nl', b'Dutch'), (b'no', b'Norwegian'), (b'oc', b'Occitan'), (b'om', b'Oromo'), (b'or', b'Oriya'), (b'pa', b'Panjabi'), (b'pl', b'Polish'), (b'ps', b'Pashto'), (b'pt', b'Portuguese'), (b'qu', b'Quechua'), (b'rm', b'Romansh'), (b'rn', b'Kirundi'), (b'ro', b'Romanian'), (b'ru', b'Russian'), (b'rw', b'Kinyarwanda'), (b'sa', b'Sanskrit'), (b'sd', b'Sindhi'), (b'sg', b'Sango'), (b'si', b'Sinhala'), (b'sk', b'Slovak'), (b'sl', b'Slovenian'), (b'sm', b'Samoan'), (b'sn', b'Shona'), (b'so', b'Somali'), (b'sq', b'Albanian'), (b'sr', b'Serbian'), (b'ss', b'Swati'), (b'st', b'Southern Sotho'), (b'su', b'Sudanese'), (b'sv', b'Swedish'), (b'sw', b'Swahili'), (b'ta', b'Tamil'), (b'te', b'Telugu'), (b'tg', b'Tajik'), (b'th', b'Thai'), (b'ti', b'Tigrinya'), (b'tk', b'Turkmen'), (b'tl', b'Tagalog'), (b'tn', b'Tswana'), (b'to', b'Tonga'), (b'tr', b'Turkish'), (b'ts', b'Tsonga'), (b'tt', b'Tatar'), (b'tw', b'Twi'), (b'ug', b'Uyghur'), (b'uk', b'Ukrainian'), (b'ur', b'Urdu'), (b'uz', b'Uzbek'), (b'vi', b'Vietnamese'), (b'vo', b'Volapuk'), (b'wo', b'Wolof'), (b'xh', b'Xhosa'), (b'yi', b'Yiddish'), (b'yo', b'Yoruba'), (b'za', b'Zhuang'), (b'zh', b'Chinese'), (b'zu', b'Zulu'), (b'nb_NO', b'Norwegian Bokmal'), (b'pt_BR', b'Brazilian Portuguese'), (b'uk_UA', b'Ukrainian'), (b'zh_CN', b'Simplified Chinese'), (b'zh_TW', b'Traditional Chinese')])),
                ('programming_language', models.CharField(default=b'words', choices=[(b'words', b'Only Words'), (b'py', b'Python'), (b'js', b'Javascript'), (b'php', b'PHP'), (b'ruby', b'Ruby'), (b'perl', b'Perl'), (b'java', b'Java'), (b'go', b'Go'), (b'julia', b'Julia'), (b'c', b'C'), (b'csharp', b'C#'), (b'cpp', b'C++'), (b'objc', b'Objective-C'), (b'other', b'Other')], max_length=20, blank=True, help_text='The primary programming language the project is written in.', verbose_name='Programming Language')),
                ('num_major', models.IntegerField(default=2, blank=True, help_text='2 means supporting 3.X.X and 2.X.X, but not 1.X.X', null=True, verbose_name='Number of Major versions')),
                ('num_minor', models.IntegerField(default=2, blank=True, help_text='2 means supporting 2.2.X and 2.1.X, but not 2.0.X', null=True, verbose_name='Number of Minor versions')),
                ('num_point', models.IntegerField(default=2, blank=True, help_text='2 means supporting 2.2.2 and 2.2.1, but not 2.2.0', null=True, verbose_name='Number of Point versions')),
                ('main_language_project', models.ForeignKey(related_name='translations', blank=True, to='projects.Project', null=True)),
            ],
            options={
                'ordering': ('slug',),
                'permissions': (('view_project', 'View Project'),),
            },
        ),
        migrations.CreateModel(
            name='ProjectRelationship',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('child', models.ForeignKey(related_name='superprojects', verbose_name='Child', to='projects.Project')),
                ('parent', models.ForeignKey(related_name='subprojects', verbose_name='Parent', to='projects.Project')),
            ],
        ),
        migrations.CreateModel(
            name='WebHook',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('url', models.URLField(help_text='URL to send the webhook to', blank=True)),
                ('project', models.ForeignKey(related_name='webhook_notifications', to='projects.Project')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='project',
            name='related_projects',
            field=models.ManyToManyField(to='projects.Project', verbose_name='Related projects', through='projects.ProjectRelationship', blank=True),
        ),
        migrations.AddField(
            model_name='project',
            name='tags',
            field=taggit.managers.TaggableManager(to='taggit.Tag', through='taggit.TaggedItem', blank=True, help_text='A comma-separated list of tags.', verbose_name='Tags'),
        ),
        migrations.AddField(
            model_name='project',
            name='users',
            field=models.ManyToManyField(related_name='projects', verbose_name='User', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='emailhook',
            name='project',
            field=models.ForeignKey(related_name='emailhook_notifications', to='projects.Project'),
        ),
    ]
