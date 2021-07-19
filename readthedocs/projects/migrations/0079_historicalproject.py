# Generated by Django 2.2.24 on 2021-07-19 18:57

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import readthedocs.projects.models
import readthedocs.projects.validators
import simple_history.models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('oauth', '0014_remove_remoterepository_project'),
        ('projects', '0078_add_external_builds_privacy_level_field'),
    ]

    operations = [
        migrations.CreateModel(
            name='HistoricalProject',
            fields=[
                ('id', models.IntegerField(auto_created=True, blank=True, db_index=True, verbose_name='ID')),
                ('pub_date', models.DateTimeField(blank=True, db_index=True, editable=False, verbose_name='Publication date')),
                ('modified_date', models.DateTimeField(blank=True, db_index=True, editable=False, verbose_name='Modified date')),
                ('name', models.CharField(max_length=63, verbose_name='Name')),
                ('slug', models.SlugField(max_length=63, verbose_name='Slug')),
                ('description', models.TextField(blank=True, help_text='Short description of this project', verbose_name='Description')),
                ('repo', models.CharField(db_index=True, help_text='Hosted documentation repository URL', max_length=255, validators=[readthedocs.projects.validators.RepositoryURLValidator()], verbose_name='Repository URL')),
                ('repo_type', models.CharField(choices=[('git', 'Git'), ('svn', 'Subversion'), ('hg', 'Mercurial'), ('bzr', 'Bazaar')], default='git', max_length=10, verbose_name='Repository type')),
                ('project_url', models.URLField(blank=True, help_text="The project's homepage", verbose_name='Project homepage')),
                ('canonical_url', models.URLField(blank=True, help_text='URL that documentation is expected to serve from', verbose_name='Canonical URL')),
                ('single_version', models.BooleanField(default=False, help_text='A single version site has no translations and only your "latest" version, served at the root of the domain. Use this with caution, only turn it on if you will <b>never</b> have multiple versions of your docs.', verbose_name='Single version')),
                ('default_version', models.CharField(default='latest', help_text='The version of your project that / redirects to', max_length=255, verbose_name='Default version')),
                ('default_branch', models.CharField(blank=True, default=None, help_text='What branch "latest" points to. Leave empty to use the default value for your VCS (eg. <code>trunk</code> or <code>master</code>).', max_length=255, null=True, verbose_name='Default branch')),
                ('requirements_file', models.CharField(blank=True, default=None, help_text='A <a href="https://pip.pypa.io/en/latest/user_guide.html#requirements-files">pip requirements file</a> needed to build your documentation. Path from the root of your project.', max_length=255, null=True, verbose_name='Requirements file')),
                ('documentation_type', models.CharField(choices=[('sphinx', 'Sphinx Html'), ('mkdocs', 'Mkdocs'), ('sphinx_htmldir', 'Sphinx HtmlDir'), ('sphinx_singlehtml', 'Sphinx Single Page HTML')], default='sphinx', help_text='Type of documentation you are building. <a href="http://www.sphinx-doc.org/en/stable/builders.html#sphinx.builders.html.DirectoryHTMLBuilder">More info on sphinx builders</a>.', max_length=20, verbose_name='Documentation type')),
                ('urlconf', models.CharField(blank=True, default=None, help_text='Supports the following keys: $language, $version, $subproject, $filename. An example: `$language/$version/$filename`.', max_length=255, null=True, verbose_name='Documentation URL Configuration')),
                ('external_builds_enabled', models.BooleanField(default=False, help_text='More information in <a href="https://docs.readthedocs.io/page/guides/autobuild-docs-for-pull-requests.html">our docs</a>', verbose_name='Build pull requests for this project')),
                ('external_builds_privacy_level', models.CharField(choices=[('public', 'Public'), ('private', 'Private')], default=readthedocs.projects.models.default_privacy_level, help_text='Should builds from pull requests be public?', max_length=20, null=True, verbose_name='Privacy level of Pull Requests')),
                ('cdn_enabled', models.BooleanField(default=False, verbose_name='CDN Enabled')),
                ('analytics_code', models.CharField(blank=True, help_text='Google Analytics Tracking ID (ex. <code>UA-22345342-1</code>). This may slow down your page loads.', max_length=50, null=True, verbose_name='Analytics code')),
                ('analytics_disabled', models.BooleanField(default=False, help_text='Disable Google Analytics completely for this project (requires rebuilding documentation)', null=True, verbose_name='Disable Analytics')),
                ('container_image', models.CharField(blank=True, max_length=64, null=True, verbose_name='Alternative container image')),
                ('container_mem_limit', models.CharField(blank=True, help_text='Memory limit in Docker format -- example: <code>512m</code> or <code>1g</code>', max_length=10, null=True, verbose_name='Container memory limit')),
                ('container_time_limit', models.IntegerField(blank=True, null=True, verbose_name='Container time limit in seconds')),
                ('build_queue', models.CharField(blank=True, max_length=32, null=True, verbose_name='Alternate build queue id')),
                ('max_concurrent_builds', models.IntegerField(blank=True, null=True, verbose_name='Maximum concurrent builds allowed for this project')),
                ('allow_promos', models.BooleanField(default=True, help_text='If unchecked, users will still see community ads.', verbose_name='Allow paid advertising')),
                ('ad_free', models.BooleanField(default=False, help_text='If checked, do not show advertising for this project', verbose_name='Ad-free')),
                ('show_version_warning', models.BooleanField(default=False, help_text='Show warning banner in non-stable nor latest versions.', verbose_name='Show version warning')),
                ('enable_epub_build', models.BooleanField(default=True, help_text='Create a EPUB version of your documentation with each build.', verbose_name='Enable EPUB build')),
                ('enable_pdf_build', models.BooleanField(default=True, help_text='Create a PDF version of your documentation with each build.', verbose_name='Enable PDF build')),
                ('path', models.CharField(editable=False, help_text='The directory where <code>conf.py</code> lives', max_length=255, verbose_name='Path')),
                ('conf_py_file', models.CharField(blank=True, default='', help_text='Path from project root to <code>conf.py</code> file (ex. <code>docs/conf.py</code>). Leave blank if you want us to find it for you.', max_length=255, verbose_name='Python configuration file')),
                ('featured', models.BooleanField(default=False, verbose_name='Featured')),
                ('skip', models.BooleanField(default=False, verbose_name='Skip')),
                ('install_project', models.BooleanField(default=False, help_text='Install your project inside a virtualenv using <code>setup.py install</code>', verbose_name='Install Project')),
                ('python_interpreter', models.CharField(choices=[('python', 'CPython 2.x'), ('python3', 'CPython 3.x')], default='python3', help_text='The Python interpreter used to create the virtual environment.', max_length=20, verbose_name='Python Interpreter')),
                ('use_system_packages', models.BooleanField(default=False, help_text='Give the virtual environment access to the global site-packages dir.', verbose_name='Use system packages')),
                ('privacy_level', models.CharField(choices=[('public', 'Public'), ('private', 'Private')], default='public', help_text='Should the project dashboard be public?', max_length=20, verbose_name='Privacy Level')),
                ('language', models.CharField(choices=[('aa', 'Afar'), ('ab', 'Abkhaz'), ('acr', 'Achi'), ('af', 'Afrikaans'), ('agu', 'Awakateko'), ('am', 'Amharic'), ('ar', 'Arabic'), ('as', 'Assamese'), ('ay', 'Aymara'), ('az', 'Azerbaijani'), ('ba', 'Bashkir'), ('be', 'Belarusian'), ('bg', 'Bulgarian'), ('bh', 'Bihari'), ('bi', 'Bislama'), ('bn', 'Bengali'), ('bo', 'Tibetan'), ('br', 'Breton'), ('ca', 'Catalan'), ('caa', "Ch'orti'"), ('cac', 'Chuj'), ('cab', 'Garífuna'), ('cak', 'Kaqchikel'), ('co', 'Corsican'), ('cs', 'Czech'), ('cy', 'Welsh'), ('da', 'Danish'), ('de', 'German'), ('dz', 'Dzongkha'), ('el', 'Greek'), ('en', 'English'), ('eo', 'Esperanto'), ('es', 'Spanish'), ('et', 'Estonian'), ('eu', 'Basque'), ('fa', 'Iranian'), ('fi', 'Finnish'), ('fj', 'Fijian'), ('fo', 'Faroese'), ('fr', 'French'), ('fy', 'Western Frisian'), ('ga', 'Irish'), ('gd', 'Scottish Gaelic'), ('gl', 'Galician'), ('gn', 'Guarani'), ('gu', 'Gujarati'), ('ha', 'Hausa'), ('hi', 'Hindi'), ('he', 'Hebrew'), ('hr', 'Croatian'), ('hu', 'Hungarian'), ('hy', 'Armenian'), ('ia', 'Interlingua'), ('id', 'Indonesian'), ('ie', 'Interlingue'), ('ik', 'Inupiaq'), ('is', 'Icelandic'), ('it', 'Italian'), ('itz', "Itza'"), ('iu', 'Inuktitut'), ('ixl', 'Ixil'), ('ja', 'Japanese'), ('jac', "Popti'"), ('jv', 'Javanese'), ('ka', 'Georgian'), ('kjb', "Q'anjob'al"), ('kek', "Q'eqchi'"), ('kk', 'Kazakh'), ('kl', 'Kalaallisut'), ('km', 'Khmer'), ('kn', 'Kannada'), ('knj', 'Akateko'), ('ko', 'Korean'), ('ks', 'Kashmiri'), ('ku', 'Kurdish'), ('ky', 'Kyrgyz'), ('la', 'Latin'), ('ln', 'Lingala'), ('lo', 'Lao'), ('lt', 'Lithuanian'), ('lv', 'Latvian'), ('mam', 'Mam'), ('mg', 'Malagasy'), ('mi', 'Maori'), ('mk', 'Macedonian'), ('ml', 'Malayalam'), ('mn', 'Mongolian'), ('mop', 'Mopan'), ('mr', 'Marathi'), ('ms', 'Malay'), ('mt', 'Maltese'), ('my', 'Burmese'), ('na', 'Nauru'), ('ne', 'Nepali'), ('nl', 'Dutch'), ('no', 'Norwegian'), ('oc', 'Occitan'), ('om', 'Oromo'), ('or', 'Oriya'), ('pa', 'Panjabi'), ('pl', 'Polish'), ('pnb', 'Western Punjabi'), ('poc', 'Poqomam'), ('poh', 'Poqomchi'), ('ps', 'Pashto'), ('pt', 'Portuguese'), ('qu', 'Quechua'), ('quc', "K'iche'"), ('qum', 'Sipakapense'), ('quv', 'Sakapulteko'), ('rm', 'Romansh'), ('rn', 'Kirundi'), ('ro', 'Romanian'), ('ru', 'Russian'), ('rw', 'Kinyarwanda'), ('sa', 'Sanskrit'), ('sd', 'Sindhi'), ('sg', 'Sango'), ('si', 'Sinhala'), ('sk', 'Slovak'), ('skr', 'Saraiki'), ('sl', 'Slovenian'), ('sm', 'Samoan'), ('sn', 'Shona'), ('so', 'Somali'), ('sq', 'Albanian'), ('sr', 'Serbian'), ('ss', 'Swati'), ('st', 'Southern Sotho'), ('su', 'Sudanese'), ('sv', 'Swedish'), ('sw', 'Swahili'), ('ta', 'Tamil'), ('te', 'Telugu'), ('tg', 'Tajik'), ('th', 'Thai'), ('ti', 'Tigrinya'), ('tk', 'Turkmen'), ('tl', 'Tagalog'), ('tn', 'Tswana'), ('to', 'Tonga'), ('tr', 'Turkish'), ('ts', 'Tsonga'), ('tt', 'Tatar'), ('ttc', 'Tektiteko'), ('tzj', "Tz'utujil"), ('tw', 'Twi'), ('ug', 'Uyghur'), ('uk', 'Ukrainian'), ('ur', 'Urdu'), ('usp', 'Uspanteko'), ('uz', 'Uzbek'), ('vi', 'Vietnamese'), ('vo', 'Volapuk'), ('wo', 'Wolof'), ('xh', 'Xhosa'), ('xin', 'Xinka'), ('yi', 'Yiddish'), ('yo', 'Yoruba'), ('za', 'Zhuang'), ('zh', 'Chinese'), ('zu', 'Zulu'), ('nb_NO', 'Norwegian Bokmal'), ('pt_BR', 'Brazilian Portuguese'), ('es_MX', 'Mexican Spanish'), ('uk_UA', 'Ukrainian'), ('zh_CN', 'Simplified Chinese'), ('zh_TW', 'Traditional Chinese')], default='en', help_text="The language the project documentation is rendered in. Note: this affects your project's URL.", max_length=20, verbose_name='Language')),
                ('programming_language', models.CharField(blank=True, choices=[('words', 'Only Words'), ('py', 'Python'), ('js', 'JavaScript'), ('php', 'PHP'), ('ruby', 'Ruby'), ('perl', 'Perl'), ('java', 'Java'), ('go', 'Go'), ('julia', 'Julia'), ('c', 'C'), ('csharp', 'C#'), ('cpp', 'C++'), ('objc', 'Objective-C'), ('css', 'CSS'), ('ts', 'TypeScript'), ('swift', 'Swift'), ('vb', 'Visual Basic'), ('r', 'R'), ('scala', 'Scala'), ('groovy', 'Groovy'), ('coffee', 'CoffeeScript'), ('lua', 'Lua'), ('haskell', 'Haskell'), ('other', 'Other')], default='words', help_text='The primary programming language the project is written in.', max_length=20, verbose_name='Programming Language')),
                ('has_valid_webhook', models.BooleanField(default=False, help_text='This project has been built with a webhook')),
                ('has_valid_clone', models.BooleanField(default=False, help_text='This project has been successfully cloned')),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_date', models.DateTimeField()),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_type', models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
                ('history_user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('main_language_project', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='projects.Project')),
                ('remote_repository', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='oauth.RemoteRepository')),
            ],
            options={
                'verbose_name': 'historical project',
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': 'history_date',
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
    ]
