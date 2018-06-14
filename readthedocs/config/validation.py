INVALID_BOOL = ''
INVALID_CHOICE = ''
INVALID_LIST = ''
INVALID_DIRECTORY = ''
INVALID_FILE = ''
INVALID_PATH = ''
INVALID_STRING = ''


class ValidationError(Exception):
    pass


def validate_list(value):
    pass


def validate_choice(value, choices):
    pass


def validate_bool(value):
    pass


def validate_directory(value, base_path):
    pass


def validate_file(value, base_path):
    pass


def validate_path(value, base_path):
    pass


def validate_string(value):
    pass
