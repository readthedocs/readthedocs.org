# -*- coding: utf-8 -*-
"""
Project constants.

Default values and other various configuration for projects, including available
theme names and repository types.
"""

from __future__ import (
    absolute_import, division, print_function, unicode_literals)

import re

from django.utils.translation import ugettext_lazy as _

THEME_DEFAULT = 'default'
THEME_SPHINX = 'sphinxdoc'
THEME_SCROLLS = 'scrolls'
THEME_AGOGO = 'agogo'
THEME_TRADITIONAL = 'traditional'
THEME_NATURE = 'nature'
THEME_HAIKU = 'haiku'

DOCUMENTATION_CHOICES = (
    ('auto', _('Automatically Choose')),
    ('sphinx', _('Sphinx Html')),
    ('mkdocs', _('Mkdocs (Markdown)')),
    ('sphinx_htmldir', _('Sphinx HtmlDir')),
    ('sphinx_singlehtml', _('Sphinx Single Page HTML')),
)

DEFAULT_THEME_CHOICES = (
    # Translators: This is a name of a Sphinx theme.
    (THEME_DEFAULT, _('Default')),
    # Translators: This is a name of a Sphinx theme.
    (THEME_SPHINX, _('Sphinx Docs')),
    # (THEME_SCROLLS, 'Scrolls'),
    # (THEME_AGOGO, 'Agogo'),
    # Translators: This is a name of a Sphinx theme.
    (THEME_TRADITIONAL, _('Traditional')),
    # Translators: This is a name of a Sphinx theme.
    (THEME_NATURE, _('Nature')),
    # Translators: This is a name of a Sphinx theme.
    (THEME_HAIKU, _('Haiku')),
)

SAMPLE_FILES = (
    ('Installation', 'projects/samples/installation.rst.html'),
    ('Getting started', 'projects/samples/getting_started.rst.html'),
)

SCRAPE_CONF_SETTINGS = [
    'copyright',
    'project',
    'version',
    'release',
    'source_suffix',
    'html_theme',
    'extensions',
]

HEADING_MARKUP = (
    (1, '='),
    (2, '-'),
    (3, '^'),
    (4, '"'),
)

LIVE_STATUS = 1
DELETED_STATUS = 99

STATUS_CHOICES = (
    (LIVE_STATUS, _('Live')),
    (DELETED_STATUS, _('Deleted')),
)

REPO_TYPE_GIT = 'git'
REPO_TYPE_SVN = 'svn'
REPO_TYPE_HG = 'hg'
REPO_TYPE_BZR = 'bzr'

REPO_CHOICES = (
    (REPO_TYPE_GIT, _('Git')),
    (REPO_TYPE_SVN, _('Subversion')),
    (REPO_TYPE_HG, _('Mercurial')),
    (REPO_TYPE_BZR, _('Bazaar')),
)

PUBLIC = 'public'
PROTECTED = 'protected'
PRIVATE = 'private'

PRIVACY_CHOICES = (
    (PUBLIC, _('Public')),
    (PROTECTED, _('Protected')),
    (PRIVATE, _('Private')),
)

IMPORTANT_VERSION_FILTERS = {
    'slug': 'important',
}

# in the future this constant can be replaced with a implementation that
# detect all available Python interpreters in the fly (Maybe using
# update-alternatives linux tool family?).
PYTHON_CHOICES = (
    ('python', _('CPython 2.x')),
    ('python3', _('CPython 3.x')),
)

# Via http://sphinx-doc.org/latest/config.html#confval-language
# Languages supported for the lang_slug in the URL
# Translations for builtin Sphinx messages only available for a subset of these
LANGUAGES = (
    ('aa', 'Afar'),
    ('ab', 'Abkhaz'),
    ('acr', 'Achi'),
    ('af', 'Afrikaans'),
    ('agu', 'Awakateko'),
    ('am', 'Amharic'),
    ('ar', 'Arabic'),
    ('as', 'Assamese'),
    ('ay', 'Aymara'),
    ('az', 'Azerbaijani'),
    ('ba', 'Bashkir'),
    ('be', 'Belarusian'),
    ('bg', 'Bulgarian'),
    ('bh', 'Bihari'),
    ('bi', 'Bislama'),
    ('bn', 'Bengali'),
    ('bo', 'Tibetan'),
    ('br', 'Breton'),
    ('ca', 'Catalan'),
    ('caa', 'Ch\'orti\''),
    ('cac', 'Chuj'),
    ('cab', 'Garífuna'),
    ('cak', 'Kaqchikel'),
    ('co', 'Corsican'),
    ('cs', 'Czech'),
    ('cy', 'Welsh'),
    ('da', 'Danish'),
    ('de', 'German'),
    ('dz', 'Dzongkha'),
    ('el', 'Greek'),
    ('en', 'English'),
    ('eo', 'Esperanto'),
    ('es', 'Spanish'),
    ('et', 'Estonian'),
    ('eu', 'Basque'),
    ('fa', 'Iranian'),
    ('fi', 'Finnish'),
    ('fj', 'Fijian'),
    ('fo', 'Faroese'),
    ('fr', 'French'),
    ('fy', 'Western Frisian'),
    ('ga', 'Irish'),
    ('gd', 'Scottish Gaelic'),
    ('gl', 'Galician'),
    ('gn', 'Guarani'),
    ('gu', 'Gujarati'),
    ('ha', 'Hausa'),
    ('hi', 'Hindi'),
    ('he', 'Hebrew'),
    ('hr', 'Croatian'),
    ('hu', 'Hungarian'),
    ('hy', 'Armenian'),
    ('ia', 'Interlingua'),
    ('id', 'Indonesian'),
    ('ie', 'Interlingue'),
    ('ik', 'Inupiaq'),
    ('is', 'Icelandic'),
    ('it', 'Italian'),
    ('itz', 'Itza\''),
    ('iu', 'Inuktitut'),
    ('ixl', 'Ixil'),
    ('ja', 'Japanese'),
    ('jac', 'Popti\''),
    ('jv', 'Javanese'),
    ('ka', 'Georgian'),
    ('kjb', 'Q\'anjob\'al'),
    ('kek', 'Q\'eqchi\''),
    ('kk', 'Kazakh'),
    ('kl', 'Kalaallisut'),
    ('km', 'Khmer'),
    ('kn', 'Kannada'),
    ('knj', 'Akateko'),
    ('ko', 'Korean'),
    ('ks', 'Kashmiri'),
    ('ku', 'Kurdish'),
    ('ky', 'Kyrgyz'),
    ('la', 'Latin'),
    ('ln', 'Lingala'),
    ('lo', 'Lao'),
    ('lt', 'Lithuanian'),
    ('lv', 'Latvian'),
    ('mam', 'Mam'),
    ('mg', 'Malagasy'),
    ('mi', 'Maori'),
    ('mk', 'Macedonian'),
    ('ml', 'Malayalam'),
    ('mn', 'Mongolian'),
    ('mop', 'Mopan'),
    ('mr', 'Marathi'),
    ('ms', 'Malay'),
    ('mt', 'Maltese'),
    ('my', 'Burmese'),
    ('na', 'Nauru'),
    ('ne', 'Nepali'),
    ('nl', 'Dutch'),
    ('no', 'Norwegian'),
    ('oc', 'Occitan'),
    ('om', 'Oromo'),
    ('or', 'Oriya'),
    ('pa', 'Panjabi'),
    ('pl', 'Polish'),
    ('pnb', 'Western Punjabi'),
    ('poc', 'Poqomam'),
    ('poh', 'Poqomchi'),
    ('ps', 'Pashto'),
    ('pt', 'Portuguese'),
    ('qu', 'Quechua'),
    ('quc', 'K\'iche\''),
    ('qum', 'Sipakapense'),
    ('quv', 'Sakapulteko'),
    ('rm', 'Romansh'),
    ('rn', 'Kirundi'),
    ('ro', 'Romanian'),
    ('ru', 'Russian'),
    ('rw', 'Kinyarwanda'),
    ('sa', 'Sanskrit'),
    ('sd', 'Sindhi'),
    ('sg', 'Sango'),
    ('si', 'Sinhala'),
    ('sk', 'Slovak'),
    ('skr', 'Saraiki'),
    ('sl', 'Slovenian'),
    ('sm', 'Samoan'),
    ('sn', 'Shona'),
    ('so', 'Somali'),
    ('sq', 'Albanian'),
    ('sr', 'Serbian'),
    ('ss', 'Swati'),
    ('st', 'Southern Sotho'),
    ('su', 'Sudanese'),
    ('sv', 'Swedish'),
    ('sw', 'Swahili'),
    ('ta', 'Tamil'),
    ('te', 'Telugu'),
    ('tg', 'Tajik'),
    ('th', 'Thai'),
    ('ti', 'Tigrinya'),
    ('tk', 'Turkmen'),
    ('tl', 'Tagalog'),
    ('tn', 'Tswana'),
    ('to', 'Tonga'),
    ('tr', 'Turkish'),
    ('ts', 'Tsonga'),
    ('tt', 'Tatar'),
    ('ttc', 'Tektiteko'),
    ('tzj', 'Tz\'utujil'),
    ('tw', 'Twi'),
    ('ug', 'Uyghur'),
    ('uk', 'Ukrainian'),
    ('ur', 'Urdu'),
    ('usp', 'Uspanteko'),
    ('uz', 'Uzbek'),
    ('vi', 'Vietnamese'),
    ('vo', 'Volapuk'),
    ('wo', 'Wolof'),
    ('xh', 'Xhosa'),
    ('xin', 'Xinka'),
    ('yi', 'Yiddish'),
    ('yo', 'Yoruba'),
    ('za', 'Zhuang'),
    ('zh', 'Chinese'),
    ('zu', 'Zulu'),
    # Try these to test our non-2 letter language support
    ('nb_NO', 'Norwegian Bokmal'),
    ('pt_BR', 'Brazilian Portuguese'),
    ('es_MX', 'Mexican Spanish'),
    ('uk_UA', 'Ukrainian'),
    ('zh_CN', 'Simplified Chinese'),
    ('zh_TW', 'Traditional Chinese'),
)

LANGUAGES_REGEX = '|'.join([re.escape(code[0]) for code in LANGUAGES])

PROGRAMMING_LANGUAGES = (
    ('words', 'Only Words'),
    ('py', 'Python'),
    ('js', 'JavaScript'),
    ('php', 'PHP'),
    ('ruby', 'Ruby'),
    ('perl', 'Perl'),
    ('java', 'Java'),
    ('go', 'Go'),
    ('julia', 'Julia'),
    ('c', 'C'),
    ('csharp', 'C#'),
    ('cpp', 'C++'),
    ('objc', 'Objective-C'),
    ('css', 'CSS'),
    ('ts', 'TypeScript'),
    ('swift', 'Swift'),
    ('vb', 'Visual Basic'),
    ('r', 'R'),
    ('scala', 'Scala'),
    ('groovy', 'Groovy'),
    ('coffee', 'CoffeeScript'),
    ('lua', 'Lua'),
    ('haskell', 'Haskell'),
    ('other', 'Other'),
)

LOG_TEMPLATE = '(Build) [{project}:{version}] {msg}'

PROJECT_PK_REGEX = '(?:[-\w]+)'
PROJECT_SLUG_REGEX = '(?:[-\w]+)'

GITHUB_REGEXS = [
    re.compile('github.com/(.+)/(.+)(?:\.git){1}$'),
    re.compile('github.com/(.+)/(.+)'),
    re.compile('github.com:(.+)/(.+)\.git$'),
]
BITBUCKET_REGEXS = [
    re.compile('bitbucket.org/(.+)/(.+)\.git$'),
    re.compile('@bitbucket.org/(.+)/(.+)\.git$'),
    re.compile('bitbucket.org/(.+)/(.+)/?'),
    re.compile('bitbucket.org:(.+)/(.+)\.git$'),
]
GITLAB_REGEXS = [
    re.compile('gitlab.com/(.+)/(.+)(?:\.git){1}$'),
    re.compile('gitlab.com/(.+)/(.+)'),
    re.compile('gitlab.com:(.+)/(.+)\.git$'),
]
GITHUB_URL = (
    'https://github.com/{user}/{repo}/'
    '{action}/{version}{docroot}{path}{source_suffix}')
BITBUCKET_URL = (
    'https://bitbucket.org/{user}/{repo}/'
    'src/{version}{docroot}{path}{source_suffix}')
GITLAB_URL = (
    'https://gitlab.com/{user}/{repo}/'
    '{action}/{version}{docroot}{path}{source_suffix}')
