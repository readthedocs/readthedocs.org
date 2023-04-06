from django.forms import ValidationError


def validate_custom_prefix(project, prefix):
    """
    Validate and clean the custom path prefix for a project.

    We validate that the prefix is defined in the correct project.
    Prefixes must be defined in the main project if the project is a translation.

    Raises ``ValidationError`` if the prefix is invalid.

    :param project: Project to validate the prefix
    :param prefix: Prefix to validate
    """
    if not prefix:
        return

    if project.main_language_project:
        raise ValidationError(
            "This project is a translation of another project, "
            "the custom prefix must be defined in the main project.",
            code="invalid_project",
        )

    return _clean_prefix(prefix)


def validate_custom_subproject_prefix(project, prefix):
    """
    Validate and clean the custom subproject prefix for a project.

    We validate that the subproject prefix is defined in a super project,
    not in a subproject.

    Raises ``ValidationError`` if the prefix is invalid.

    :param project: Project to validate the prefix
    :param prefix: Subproject prefix to validate
    """
    if not prefix:
        return

    main_project = project.main_language_project or project
    if main_project.is_subproject:
        raise ValidationError(
            "This project is a subproject, the subproject prefix must "
            "be defined in the parent project custom_subproject_prefix attribute.",
            code="invalid_project",
        )

    return _clean_prefix(prefix)


def _clean_prefix(prefix):
    """
    Validate and clean a prefix.

    Prefixes must:

    - Start and end with a slash

    :param prefix: Prefix to clean and validate
    """
    # TODO we could validate that only alphanumeric characters are used?
    prefix = prefix.strip("/")
    if not prefix:
        return "/"
    return f"/{prefix}/"
