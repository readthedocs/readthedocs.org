"""
Project constants.

Default values and other various configuration for projects, including available
theme names and repository types.
"""

import os
import re

from django.utils.translation import gettext_lazy as _


SPHINX = "sphinx"
MKDOCS = "mkdocs"
SPHINX_HTMLDIR = "sphinx_htmldir"
SPHINX_SINGLEHTML = "sphinx_singlehtml"
# This type is defined by the users in their mkdocs.yml file.
MKDOCS_HTML = "mkdocs_html"
GENERIC = "generic"
DOCUMENTATION_CHOICES = (
    (SPHINX, _("Sphinx Html")),
    (MKDOCS, _("Mkdocs")),
    (SPHINX_HTMLDIR, _("Sphinx HtmlDir")),
    (SPHINX_SINGLEHTML, _("Sphinx Single Page HTML")),
)
DOCTYPE_CHOICES = DOCUMENTATION_CHOICES + (
    (MKDOCS_HTML, _("Mkdocs Html Pages")),
    (GENERIC, _("Generic")),
)


MEDIA_TYPE_HTML = "html"
MEDIA_TYPE_PDF = "pdf"
MEDIA_TYPE_EPUB = "epub"
MEDIA_TYPE_HTMLZIP = "htmlzip"
MEDIA_TYPE_JSON = "json"
MEDIA_TYPE_DIFF = "diff"
DOWNLOADABLE_MEDIA_TYPES = (
    MEDIA_TYPE_PDF,
    MEDIA_TYPE_EPUB,
    MEDIA_TYPE_HTMLZIP,
)
MEDIA_TYPES = (
    MEDIA_TYPE_HTML,
    MEDIA_TYPE_PDF,
    MEDIA_TYPE_EPUB,
    MEDIA_TYPE_HTMLZIP,
    MEDIA_TYPE_JSON,
    MEDIA_TYPE_DIFF,
)

BUILD_COMMANDS_OUTPUT_PATH = "_readthedocs/"
BUILD_COMMANDS_OUTPUT_PATH_HTML = os.path.join(BUILD_COMMANDS_OUTPUT_PATH, "html")

SAMPLE_FILES = (
    ("Installation", "projects/samples/installation.rst.html"),
    ("Getting started", "projects/samples/getting_started.rst.html"),
)

SCRAPE_CONF_SETTINGS = [
    "copyright",
    "project",
    "version",
    "release",
    "source_suffix",
    "html_theme",
    "extensions",
]

HEADING_MARKUP = (
    (1, "="),
    (2, "-"),
    (3, "^"),
    (4, '"'),
)

LIVE_STATUS = 1
DELETED_STATUS = 99

STATUS_CHOICES = (
    (LIVE_STATUS, _("Live")),
    (DELETED_STATUS, _("Deleted")),
)

REPO_TYPE_GIT = "git"

# TODO: Remove this since we only have 1 type.
REPO_CHOICES = ((REPO_TYPE_GIT, _("Git")),)

PUBLIC = "public"
PRIVATE = "private"

PRIVACY_CHOICES = (
    (PUBLIC, _("Public")),
    (PRIVATE, _("Private")),
)

IMPORTANT_VERSION_FILTERS = {
    "slug": "important",
}

# in the future this constant can be replaced with a implementation that
# detect all available Python interpreters in the fly (Maybe using
# update-alternatives linux tool family?).
PYTHON_CHOICES = (
    ("python", _("CPython 2.x")),
    ("python3", _("CPython 3.x")),
)

# Via http://sphinx-doc.org/latest/config.html#confval-language
# Languages supported for the lang_slug in the URL
# Translations for builtin Sphinx messages only available for a subset of these
LANGUAGES = (
    ("aa", "Afar"),
    ("ab", "Abkhaz"),
    ("acr", "Achi"),
    ("af", "Afrikaans"),
    ("agu", "Awakateko"),
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
    ("caa", "Ch'orti'"),
    ("cac", "Chuj"),
    ("cab", "Garífuna"),
    ("cak", "Kaqchikel"),
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
    ("itz", "Itza'"),
    ("iu", "Inuktitut"),
    ("ixl", "Ixil"),
    ("ja", "Japanese"),
    ("jac", "Popti'"),
    ("jv", "Javanese"),
    ("ka", "Georgian"),
    ("kjb", "Q'anjob'al"),
    ("kek", "Q'eqchi'"),
    ("kk", "Kazakh"),
    ("kl", "Kalaallisut"),
    ("km", "Khmer"),
    ("kn", "Kannada"),
    ("knj", "Akateko"),
    ("ko", "Korean"),
    ("ks", "Kashmiri"),
    ("ku", "Kurdish"),
    ("ky", "Kyrgyz"),
    ("la", "Latin"),
    ("ln", "Lingala"),
    ("lo", "Lao"),
    ("lt", "Lithuanian"),
    ("lv", "Latvian"),
    ("mam", "Mam"),
    ("mg", "Malagasy"),
    ("mi", "Maori"),
    ("mk", "Macedonian"),
    ("ml", "Malayalam"),
    ("mn", "Mongolian"),
    ("mop", "Mopan"),
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
    ("pnb", "Western Punjabi"),
    ("poc", "Poqomam"),
    ("poh", "Poqomchi"),
    ("ps", "Pashto"),
    ("pt", "Portuguese"),
    ("qu", "Quechua"),
    ("quc", "K'iche'"),
    ("qum", "Sipakapense"),
    ("quv", "Sakapulteko"),
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
    ("skr", "Saraiki"),
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
    ("ttc", "Tektiteko"),
    ("tzj", "Tz'utujil"),
    ("tw", "Twi"),
    ("ug", "Uyghur"),
    ("uk", "Ukrainian"),
    ("ur", "Urdu"),
    ("usp", "Uspanteko"),
    ("uz", "Uzbek"),
    ("vi", "Vietnamese"),
    ("vo", "Volapuk"),
    ("wo", "Wolof"),
    ("xh", "Xhosa"),
    ("xin", "Xinka"),
    ("yi", "Yiddish"),
    ("yo", "Yoruba"),
    ("za", "Zhuang"),
    # TODO: migrate those projects that are currently using "zh" as language.
    # This is an invalid language code, so the first step is remove it from the
    # list of possible languages.
    # https://github.com/readthedocs/readthedocs.org/issues/11387
    #
    # In [1]: Project.objects.filter(language='zh').count()
    # Out[1]: 1485
    #
    # ("zh", "Chinese"),
    ("zu", "Zulu"),
    # Try these to test our non-2 letter language support
    ("nb-no", "Norwegian Bokmal"),
    ("pt-br", "Brazilian Portuguese"),
    ("es-mx", "Mexican Spanish"),
    ("uk-ua", "Ukrainian"),
    ("zh-cn", "Simplified Chinese"),
    ("zh-tw", "Traditional Chinese"),
)
LANGUAGE_CODES = [code for code, *_ in LANGUAGES]

# Normalize the language codes to lowercase with dashes,
# we use them to match the language codes in the URL.
# The old language codes were uppercase with underscores,
# and are deprecated, but we still need to support them.
old_language_codes = [
    "nb_NO",
    "pt_BR",
    "es_MX",
    "uk_UA",
    "zh_CN",
    "zh_TW",
]
OLD_LANGUAGES_CODE_MAPPING = {code.lower().replace("_", "-"): code for code in old_language_codes}

LANGUAGES_REGEX = "|".join(
    [re.escape(code) for code in LANGUAGE_CODES + list(OLD_LANGUAGES_CODE_MAPPING.values())]
    # Add "zh" here to be able to keep serving projects with this old invalid language code.
    # We don't allow new projects to select this language code anymore.
    #
    # https://github.com/readthedocs/readthedocs.org/issues/11428
    + ["zh"]
)

PROGRAMMING_LANGUAGES = (
    ("words", "Only Words"),
    ("py", "Python"),
    ("js", "JavaScript"),
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
    ("css", "CSS"),
    ("ts", "TypeScript"),
    ("swift", "Swift"),
    ("vb", "Visual Basic"),
    ("r", "R"),
    ("scala", "Scala"),
    ("groovy", "Groovy"),
    ("coffee", "CoffeeScript"),
    ("lua", "Lua"),
    ("haskell", "Haskell"),
    ("other", "Other"),
)

PROJECT_PK_REGEX = r"(?:[-\w]+)"
PROJECT_SLUG_REGEX = r"(?:[-\w]+)"

GITHUB_REGEXS = [
    re.compile(r"github.com/(.+)/(.+)(?:\.git){1}$"),
    # This must come before the one without a / to make sure we don't capture the /
    re.compile(r"github.com/(.+)/(.+)/"),
    re.compile(r"github.com/(.+)/(.+)"),
    re.compile(r"github.com:(.+)/(.+)\.git$"),
]
BITBUCKET_REGEXS = [
    re.compile(r"bitbucket.org/(.+)/(.+)\.git$"),
    re.compile(r"@bitbucket.org/(.+)/(.+)\.git$"),
    # This must come before the one without a / to make sure we don't capture the /
    re.compile(r"bitbucket.org/(.+)/(.+)/"),
    re.compile(r"bitbucket.org/(.+)/(.+)"),
    re.compile(r"bitbucket.org:(.+)/(.+)\.git$"),
]
GITLAB_REGEXS = [
    re.compile(r"gitlab.com/(.+)/(.+)(?:\.git){1}$"),
    # This must come before the one without a / to make sure we don't capture the /
    re.compile(r"gitlab.com/(.+)/(.+)/"),
    re.compile(r"gitlab.com/(.+)/(.+)"),
    re.compile(r"gitlab.com:(.+)/(.+)\.git$"),
]
GITHUB_COMMIT_URL = "https://github.com/{user}/{repo}/commit/{commit}"
GITHUB_PULL_REQUEST_URL = "https://github.com/{user}/{repo}/pull/{number}"
GITHUB_PULL_REQUEST_COMMIT_URL = "https://github.com/{user}/{repo}/pull/{number}/commits/{commit}"
BITBUCKET_COMMIT_URL = "https://bitbucket.org/{user}/{repo}/commits/{commit}"
GITLAB_COMMIT_URL = "https://gitlab.com/{user}/{repo}/commit/{commit}"
GITLAB_MERGE_REQUEST_COMMIT_URL = (
    "https://gitlab.com/{user}/{repo}/commit/{commit}?merge_request_iid={number}"
)
GITLAB_MERGE_REQUEST_URL = "https://gitlab.com/{user}/{repo}/merge_requests/{number}"

# Patterns to pull merge/pull request from providers
GITHUB_PR_PULL_PATTERN = "pull/{id}/head:external-{id}"
GITLAB_MR_PULL_PATTERN = "merge-requests/{id}/head:external-{id}"

# Git provider names
GITHUB_BRAND = "GitHub"
GITLAB_BRAND = "GitLab"

# SSL statuses
SSL_STATUS_VALID = "valid"
SSL_STATUS_INVALID = "invalid"
SSL_STATUS_PENDING = "pending"
SSL_STATUS_UNKNOWN = "unknown"
SSL_STATUS_CHOICES = (
    (SSL_STATUS_VALID, _("Valid and active")),
    (SSL_STATUS_INVALID, _("Invalid")),
    (SSL_STATUS_PENDING, _("Pending")),
    (SSL_STATUS_UNKNOWN, _("Unknown")),
)

MULTIPLE_VERSIONS_WITH_TRANSLATIONS = "multiple_versions_with_translations"
MULTIPLE_VERSIONS_WITHOUT_TRANSLATIONS = "multiple_versions_without_translations"
SINGLE_VERSION_WITHOUT_TRANSLATIONS = "single_version_without_translations"
VERSIONING_SCHEME_CHOICES = (
    (
        MULTIPLE_VERSIONS_WITH_TRANSLATIONS,
        _("Multiple versions with translations (/<language>/<version>/<filename>)"),
    ),
    (
        MULTIPLE_VERSIONS_WITHOUT_TRANSLATIONS,
        _("Multiple versions without translations (/<version>/<filename>)"),
    ),
    (
        SINGLE_VERSION_WITHOUT_TRANSLATIONS,
        _("Single version without translations (/<filename>)"),
    ),
)


ADDONS_FLYOUT_SORTING_ALPHABETICALLY = "alphabetically"
# Compatibility to keep the behavior of the old flyout.
# This isn't a good algorithm, but it's a way to keep the old behavior in case we need it.
ADDONS_FLYOUT_SORTING_SEMVER_READTHEDOCS_COMPATIBLE = "semver-readthedocs-compatible"
# https://pypi.org/project/packaging/
ADDONS_FLYOUT_SORTING_PYTHON_PACKAGING = "python-packaging"
ADDONS_FLYOUT_SORTING_CALVER = "calver"
# Let the user to define a custom pattern and use BumpVer to parse and sort the versions.
# https://github.com/mbarkhau/bumpver#pattern-examples
ADDONS_FLYOUT_SORTING_CUSTOM_PATTERN = "custom-pattern"

ADDONS_FLYOUT_SORTING_CHOICES = (
    (ADDONS_FLYOUT_SORTING_ALPHABETICALLY, _("Alphabetically")),
    (ADDONS_FLYOUT_SORTING_SEMVER_READTHEDOCS_COMPATIBLE, _("SemVer (Read the Docs)")),
    (
        ADDONS_FLYOUT_SORTING_PYTHON_PACKAGING,
        _("Python Packaging (PEP 440 and PEP 425)"),
    ),
    (ADDONS_FLYOUT_SORTING_CALVER, _("CalVer (YYYY.0M.0M)")),
    (ADDONS_FLYOUT_SORTING_CUSTOM_PATTERN, _("Define your own pattern")),
)

ADDONS_FLYOUT_POSITION_BOTTOM_LEFT = "bottom-left"
ADDONS_FLYOUT_POSITION_BOTTOM_RIGHT = "bottom-right"
ADDONS_FLYOUT_POSITION_TOP_LEFT = "top-left"
ADDONS_FLYOUT_POSITION_TOP_RIGHT = "top-right"
ADDONS_FLYOUT_POSITION_CHOICES = (
    (None, _("Default (from theme or Read the Docs)")),
    (ADDONS_FLYOUT_POSITION_BOTTOM_LEFT, _("Bottom left")),
    (ADDONS_FLYOUT_POSITION_BOTTOM_RIGHT, _("Bottom right")),
    (ADDONS_FLYOUT_POSITION_TOP_LEFT, _("Top left")),
    (ADDONS_FLYOUT_POSITION_TOP_RIGHT, _("Top right")),
)
