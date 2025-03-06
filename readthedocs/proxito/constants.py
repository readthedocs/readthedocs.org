from enum import Enum
from enum import auto


class RedirectType(Enum):
    http_to_https = auto()
    to_canonical_domain = auto()
    subproject_to_main_domain = auto()
    # Application defined redirect.
    system = auto()
    # User defined redirect.
    user = auto()
