"""Default values and other various configuration for projects,
including available theme names and repository types.
"""

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
    ('sphinx', _('Sphinx Html')),
    ('mkdocs', _('Mkdocs (Markdown)')),
    ('sphinx_htmldir', _('Sphinx HtmlDir')),
    ('sphinx_singlehtml', _('Sphinx Single Page HTML')),
    #('sphinx_websupport2', _('Sphinx Websupport')),
    #('sphinx_man', 'Sphinx Man'),
    #('rdoc', 'Rdoc'),
)

DEFAULT_THEME_CHOICES = (
    # Translators: This is a name of a Sphinx theme.
    (THEME_DEFAULT, _('Default')),
    # Translators: This is a name of a Sphinx theme.
    (THEME_SPHINX, _('Sphinx Docs')),
    #(THEME_SCROLLS, 'Scrolls'),
    #(THEME_AGOGO, 'Agogo'),
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

REPO_CHOICES = (
    ('git', _('Git')),
    ('svn', _('Subversion')),
    ('hg', _('Mercurial')),
    ('bzr', _('Bazaar')),
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
    'slug': 'important'
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
    ("aa", "Afar"),
    ("ab", "Abkhaz"),
    ("af", "Afrikaans"),
    ("am", "Amharic"),
    ("ar", "Arabic"),
    ("as", "Assamese"),
    ("ay", "Aymara"),
    ("az", "Azerbaijani"),
    ("ba", "Bashkir"),
    ("be", "Belarusian"),
    ("bg", "Bulgarian"),
    ("bh", "Bihari"),
    ("bi", "Bislama"),
    ("bn", "Bengali"),
    ("bo", "Tibetan"),
    ("br", "Breton"),
    ("ca", "Catalan"),
    ("co", "Corsican"),
    ("cs", "Czech"),
    ("cy", "Welsh"),
    ("da", "Danish"),
    ("de", "German"),
    ("dz", "Dzongkha"),
    ("el", "Greek"),
    ("en", "English"),
    ("eo", "Esperanto"),
    ("es", "Spanish"),
    ("et", "Estonian"),
    ("eu", "Basque"),
    ("fa", "Iranian"),
    ("fi", "Finnish"),
    ("fj", "Fijian"),
    ("fo", "Faroese"),
    ("fr", "French"),
    ("fy", "Western Frisian"),
    ("ga", "Irish"),
    ("gd", "Scottish Gaelic"),
    ("gl", "Galician"),
    ("gn", "Guarani"),
    ("gu", "Gujarati"),
    ("ha", "Hausa"),
    ("hi", "Hindi"),
    ("he", "Hebrew"),
    ("hr", "Croatian"),
    ("hu", "Hungarian"),
    ("hy", "Armenian"),
    ("ia", "Interlingua"),
    ("id", "Indonesian"),
    ("ie", "Interlingue"),
    ("ik", "Inupiaq"),
    ("is", "Icelandic"),
    ("it", "Italian"),
    ("iu", "Inuktitut"),
    ("ja", "Japanese"),
    ("jv", "Javanese"),
    ("ka", "Georgian"),
    ("kk", "Kazakh"),
    ("kl", "Kalaallisut"),
    ("km", "Khmer"),
    ("kn", "Kannada"),
    ("ko", "Korean"),
    ("ks", "Kashmiri"),
    ("ku", "Kurdish"),
    ("ky", "Kyrgyz"),
    ("la", "Latin"),
    ("ln", "Lingala"),
    ("lo", "Lao"),
    ("lt", "Lithuanian"),
    ("lv", "Latvian"),
    ("mg", "Malagasy"),
    ("mi", "Maori"),
    ("mk", "Macedonian"),
    ("ml", "Malayalam"),
    ("mn", "Mongolian"),
    ("mr", "Marathi"),
    ("ms", "Malay"),
    ("mt", "Maltese"),
    ("my", "Burmese"),
    ("na", "Nauru"),
    ("ne", "Nepali"),
    ("nl", "Dutch"),
    ("no", "Norwegian"),
    ("oc", "Occitan"),
    ("om", "Oromo"),
    ("or", "Oriya"),
    ("pa", "Panjabi"),
    ("pl", "Polish"),
    ("ps", "Pashto"),
    ("pt", "Portuguese"),
    ("qu", "Quechua"),
    ("rm", "Romansh"),
    ("rn", "Kirundi"),
    ("ro", "Romanian"),
    ("ru", "Russian"),
    ("rw", "Kinyarwanda"),
    ("sa", "Sanskrit"),
    ("sd", "Sindhi"),
    ("sg", "Sango"),
    ("si", "Sinhala"),
    ("sk", "Slovak"),
    ("sl", "Slovenian"),
    ("sm", "Samoan"),
    ("sn", "Shona"),
    ("so", "Somali"),
    ("sq", "Albanian"),
    ("sr", "Serbian"),
    ("ss", "Swati"),
    ("st", "Southern Sotho"),
    ("su", "Sudanese"),
    ("sv", "Swedish"),
    ("sw", "Swahili"),
    ("ta", "Tamil"),
    ("te", "Telugu"),
    ("tg", "Tajik"),
    ("th", "Thai"),
    ("ti", "Tigrinya"),
    ("tk", "Turkmen"),
    ("tl", "Tagalog"),
    ("tn", "Tswana"),
    ("to", "Tonga"),
    ("tr", "Turkish"),
    ("ts", "Tsonga"),
    ("tt", "Tatar"),
    ("tw", "Twi"),
    ("ug", "Uyghur"),
    ("uk", "Ukrainian"),
    ("ur", "Urdu"),
    ("uz", "Uzbek"),
    ("vi", "Vietnamese"),
    ("vo", "Volapuk"),
    ("wo", "Wolof"),
    ("xh", "Xhosa"),
    ("yi", "Yiddish"),
    ("yo", "Yoruba"),
    ("za", "Zhuang"),
    ("zh", "Chinese"),
    ("zu", "Zulu"),
    # Try these to test our non-2 letter language support
    ("nb_NO", "Norwegian Bokmal"),
    ("pt_BR", "Brazilian Portuguese"),
    ("uk_UA", "Ukrainian"),
    ("zh_CN", "Simplified Chinese"),
    ("zh_TW", "Traditional Chinese"),
)

LANGUAGES_REGEX = "|".join(
    [re.escape(code[0]) for code in LANGUAGES]
)

PROGRAMMING_LANGUAGES = (
    ("words", "Only Words"),
    ("py", "Python"),
    ("js", "Javascript"),
    ("php", "PHP"),
    ("ruby", "Ruby"),
    ("perl", "Perl"),
    ("java", "Java"),
    ("go", "Go"),
    ("julia", "Julia"),
    ("c", "C"),
    ("csharp", "C#"),
    ("cpp", "C++"),
    ("objc", "Objective-C"),
    ("other", "Other"),
)

LOG_TEMPLATE = u"(Build) [{project}:{version}] {msg}"
