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
        urlpattern,
        required_replacement_fields=required_replacement_fields,
        single_version=project.single_version,
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


def _validate_urlpattern(urlpattern, required_replacement_fields, single_version=False):
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
    :param single_version: If the pattern is from a single version project.
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
        regex = urlpattern_to_regex(urlpattern, single_version=single_version)
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


def urlpattern_to_regex(urlpattern, single_vesion=False):
    """
    Transform a URL pattern to a regular expression.

    A URL pattern is a string with replacement fields,
    valid replacement fields are: language, version, filename, subproject.

    Before compiling the regular expression, the string is formatted with
    `str.format` to replace each field with a capture group with their respective
    regex pattern.

    This regex is mainly used by the unresolver.

    For example:

        /{language}/{version}

    Would be transformed to:

        ^/(?P<language>en|es|br)(/(?P<version>[a-zA-Z]+)?)?$
    """
    urlpattern = re.escape(urlpattern)
    # The whole pattern was escaped, including the brackets from the
    # replacement fields, we want to keep those in the pattern.
    valid_replacement_fields = ("subproject", "version", "language", "filename")
    for replacement_field in valid_replacement_fields:
        urlpattern = urlpattern.replace("\\{" + replacement_field + "\\}", "{" + replacement_field + "}", 1)
    urlpattern = wrap_urlpattern(urlpattern, single_version=single_vesion)
    urlpattern = f"^{urlpattern}$"
    return re.compile(
        urlpattern.format(
            language=f"(?P<language>{pattern_opts['lang_slug']})",
            version=f"(?P<version>{pattern_opts['version_slug']})",
            filename=f"(?P<filename>{pattern_opts['filename_slug']})",
            subproject=f"(?P<subproject>{pattern_opts['project_slug']})",
        )
    )


def wrap_urlpattern(urlpattern, single_version=False):
    """
    Wrap each component of a pattern inside an optional group to support partial matches.

    If the pattern is from a single version project,
    the only component is the filename, so we need to wrap it.
    Otherwise, we skip the first component, and wrap from the second component,
    since for all others at least one component must match.

    The wrapping happens from the last component, so the group of the next component
    is always contained in the group of the previous component, and so on.

    For example, for /{version}/{language}/{filename},
    the wrapping will happen in the next order:

    - /{version}/{language}/{filename}
    - /{version}/{language}/({filename})?
    - /{version}/{language}(/({filename})?)?
    - /{version}/({language}(/({filename})?)?)?
    - /{version}(/({language}(/({filename})?)?)?)?

    This way that pattern will match the following paths:

    - /en
    - /en/
    - /en/latest
    - /en/latest/
    - /en/latest/filename
    """
    start = 0 if single_version else urlpattern.find("}/")
    end = len(urlpattern)
    while end > 0:
        index = urlpattern.rfind("/{", start, end)
        if index > 0:
            # We first wrap from the start of the component,
            # and then wrap the start of the slash,
            # so paths with or without a trailing slash match.
            urlpattern = _wrap(urlpattern, index + 1)
            urlpattern = _wrap(urlpattern, index)
        end = index
    return urlpattern


def _wrap(urlpattern, index):
    """
    Wrap a pattern in an optional group from the given index.

    For example:

        /{version}/{language}

    Would become

        /{version}/({language})?

    If the index of the second `{` was given (11).
    """
    return urlpattern[:index] + "(" + urlpattern[index:] + ")?"
