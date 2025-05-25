"""Simple datatypes defined using dataclasses, for describing project data.

Contrast this with the similar 'models' module, which defines Pydantic model
classes.
"""

import dataclasses


@dataclasses.dataclass
class ProjectVersionInfo:
    """
    Version information for a project associated with a branch or tag.

    The name fields is the end-user facing description, e.g., as seen in the
    version selector menu.

    The identifier identifies the source for the build, e.g., a branch or
    commit hash.
    """

    verbose_name: str
    identifier: str
