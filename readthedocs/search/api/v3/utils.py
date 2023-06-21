from readthedocs.projects.models import Feature


def should_use_advanced_query(projects):
    # TODO: we should make this a parameter in the API,
    # we are checking if the first project has this feature for now.
    if projects:
        project = projects[0][0]
        return not project.has_feature(Feature.DEFAULT_TO_FUZZY_SEARCH)
    return True
