import json
import os

_DATA_FILES = {
    'pipeline': ['installation.json', 'signals.json'],
    'kuma': ['documentation.json', 'docker.json'],
    'docs': ['story.json', 'wiping.json'],
}


def _get_dummy_json():
    dictionary = {}
    for key, value in _DATA_FILES.items():
        data = []
        for file_name in value:
            current_path = os.path.abspath(os.path.dirname(__file__))
            path = os.path.join(current_path, "data", key, file_name)
            with open(path) as f:
                content = json.load(f)
                data.append(content)

        dictionary[key] = data

    return dictionary


DUMMY_PAGE_JSON = _get_dummy_json()
ALL_PROJECTS = DUMMY_PAGE_JSON.keys()
