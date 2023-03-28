import re

from django.forms import ValidationError

from readthedocs.constants import pattern_opts


def validate_urlpattern(project, urlpattern):
    """
    Validate the URL pattern for a project.

    We validate that the URL pattern is defined in the correct project,
    URL patterns must be defined in the main project if the project is a translation.

    See ``_validate_urlpattern`` for all the validations.

    Raises ``ValidationError`` if the URL pattern is invalid.

    :param project: Project to validate the URL pattern
    :param urlpattern: URL pattern to validate
    """
    if not urlpattern:
        return

    if project.main_language_project:
        raise ValidationError(
            "This project is a translation of another project, "
            "the URL pattern must be defined in the main project.",
            code="invalid_project",
        )

    if project.single_version:
        required_replacement_fields = ["{filename}"]
    else:
        required_replacement_fields = ["{language}", "{version}", "{filename}"]
    _validate_urlpattern(
        urlpattern, required_replacement_fields=required_replacement_fields
    )


def validate_urlpattern_subproject(project, urlpattern):
    """
    Validate the subproject URL pattern for a project.

    We validate that the subproject URL pattern is defined in a super project,
    not in a subproject.

    See ``_validate_urlpattern`` for all the validations.

    Raises ``ValidationError`` if the URL pattern is invalid.

    :param project: Project to validate the URL pattern
    :param urlpattern: Subproject URL pattern to validate
    """
    if not urlpattern:
        return

    main_project = project.main_language_project or project
    if main_project.is_subproject:
        raise ValidationError(
            "This project is a subproject, the subproject URL pattern must "
            "be defined in the parent project urlpattern_subproject attribute.",
            code="invalid_project",
        )

    _validate_urlpattern(
        urlpattern, required_replacement_fields=["{subproject}", "{filename}"]
    )


def _validate_urlpattern(urlpattern, required_replacement_fields):
    """
    Validate a URL pattern.

    URL patterns must:

    - Start with a slash
    - Have all required replacement fields
    - Generate a valid regex pattern
    - Have the `filename` replacement field as the last component in the pattern

    Raises ``ValidationError`` if the URL pattern is invalid.

    :param urlpattern: URL pattern to validate
    :param required_replacement_fields: List of required replacement fields
    """
    if not urlpattern.startswith("/"):
        raise ValidationError(
            f"Invalid URL pattern: {urlpattern}. "
            "The URL pattern must start with a slash.",
            code="missing_leading_slash",
        )

    for required_field in required_replacement_fields:
        if required_field not in urlpattern:
            raise ValidationError(
                f"Invalid URL pattern: {urlpattern}. "
                f"Missing or invalid replacement field: {required_field}.",
                code="missing_replacement_field",
            )

    try:
        regex = urlpattern_to_regex(urlpattern)
    except KeyError as e:
        invalid_field = e.args[0]
        raise ValidationError(
            f"Invalid URL pattern: {urlpattern}. "
            f"Invalid replacement field: {invalid_field}.",
            code="invalid_replacement_field",
        )
    except re.error as e:
        raise ValidationError(
            f"Invalid regex generated from URL pattern: {urlpattern}. Regex pattern: {e.pattern}.",
            code="invalid_regex",
        )

    filename_index = regex.groupindex.get("filename")
    if filename_index is not None:
        for index in regex.groupindex.values():
            if index > filename_index:
                raise ValidationError(
                    f"Invalid URL pattern: {urlpattern}. "
                    f"The `filename` replacement field must be last component in the pattern.",
                    code="invalid_filename_position",
                )


def urlpattern_to_regex(urlpattern):
    """
    Transform a URL pattern to a regular expression.

    A URL pattern is a regular expression with replacement fields,
    valid replacement fields are: language, version, filename, subproject.

    Before compiling the regular expression, the string is formatted with
    `str.format` to replace each field with a capture group with their respective
    regex pattern.

    This regex is mainly used by the unresolver.

    For example:

        /{language}/{version}

    Would be transformed to:

        ^/(?P<language>en|es|br)/(?P<version>[a-zA-Z]+)$
    """
    urlpattern = f"^{urlpattern}$"
    return re.compile(
        urlpattern.format(
            language=f"(?P<language>{pattern_opts['lang_slug']})",
            version=f"(?P<version>{pattern_opts['version_slug']})",
            filename=f"(?P<filename>{pattern_opts['filename_slug']})",
            subproject=f"(?P<subproject>{pattern_opts['project_slug']})",
        )
    )


def urlpattern_to_plain_text(urlpattern):
    """
    Remove all regex special characters from a URL pattern.

    URL patterns are regular expressions with replacement fields,
    we remove all special regex characters to have a plain text
    representation of the URL. Replacement fields are left untouched.

    For example:

        ^/{language}/{version}$

    Would be transformed to:

        /{language}/{version}

    This operation is useful to build a URL from a URL pattern,
    given the current language, version, filename, or subproject.

    .. note::

       To escape a regex instead of removing its characters, use ``re.escape``.
    """
    remove = {"(", ")", "?"}
    plain_urlpattern = []
    is_escaped = False
    for c in urlpattern:
        # If the previous character was a backslash, the
        # current character is escaped, so we include it as is.
        if is_escaped:
            is_escaped = False
            plain_urlpattern.append(c)
            continue

        if c == "\\":
            is_escaped = True
            continue

        if c not in remove:
            plain_urlpattern.append(c)

    return "".join(plain_urlpattern)
