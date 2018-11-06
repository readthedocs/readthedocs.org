from __future__ import division, print_function, unicode_literals

from os import path

import pytest
import six
import yamale
from readthedocs.config.tests import utils
from yamale.validators import DefaultValidators, Validator

V2_SCHEMA = path.join(
    path.dirname(__file__),
    '../fixtures/spec/v2/schema.yml'
)


class PathValidator(Validator):

    """
    Path validator

    Checks if the given value is a string and a existing
    file.
    """

    tag = 'path'
    constraints = []
    configuration_file = '.'

    def _is_valid(self, value):
        if isinstance(value, six.string_types):
            file_ = path.join(
                path.dirname(self.configuration_file),
                value
            )
            return path.exists(file_)
        return False


def create_yaml(tmpdir, content):
    fs = {
        'environment.yml': '',
        'mkdocs.yml': '',
        'rtd.yml': content,
        'docs': {
            'conf.py': '',
            'requirements.txt': '',
        },
    }
    utils.apply_fs(tmpdir, fs)
    return path.join(tmpdir.strpath, 'rtd.yml')


def validate_schema(file):
    validators = DefaultValidators.copy()
    PathValidator.configuration_file = file
    validators[PathValidator.tag] = PathValidator

    data = yamale.make_data(file)
    schema = yamale.make_schema(
        V2_SCHEMA,
        validators=validators
    )
    yamale.validate(schema, data)


def assertValidConfig(tmpdir, content):
    file = create_yaml(tmpdir, content)
    validate_schema(file)


def assertInvalidConfig(tmpdir, content, msgs=()):
    file = create_yaml(tmpdir, content)
    with pytest.raises(ValueError) as excinfo:
        validate_schema(file)
    for msg in msgs:
        assert msg in str(excinfo.value)


def test_minimal_config(tmpdir):
    assertValidConfig(tmpdir, 'version: "2"')


def test_invalid_version(tmpdir):
    assertInvalidConfig(
        tmpdir,
        'version: "latest"',
        ['version:', "'latest' not in"]
    )


def test_invalid_version_1(tmpdir):
    assertInvalidConfig(
        tmpdir,
        'version: "1"',
        ['version', "'1' not in"]
    )


def test_formats(tmpdir):
    content = '''
version: "2"
formats:
  - pdf
    '''
    assertValidConfig(tmpdir, content)


def test_formats_all(tmpdir):
    content = '''
version: "2"
formats:
  - htmlzip
  - pdf
  - epub
    '''
    assertValidConfig(tmpdir, content)


def test_formats_key_all(tmpdir):
    content = '''
version: "2"
formats: all
    '''
    assertValidConfig(tmpdir, content)


def test_formats_invalid(tmpdir):
    content = '''
version: "2"
formats:
  - invalidformat
  - singlehtmllocalmedia
    '''
    assertInvalidConfig(
        tmpdir,
        content,
        ['formats', "'invalidformat' not in"]
    )


def test_formats_empty(tmpdir):
    content = '''
version: "2"
formats: []
    '''
    assertValidConfig(tmpdir, content)


def test_conda(tmpdir):
    content = '''
version: "2"
conda:
  environment: environment.yml
    '''
    assertValidConfig(tmpdir, content)


def test_conda_invalid(tmpdir):
    content = '''
version: "2"
conda:
  environment: environment.yaml
    '''
    assertInvalidConfig(
        tmpdir,
        content,
        ['environment.yaml', 'is not a path']
    )


def test_conda_missing_key(tmpdir):
    content = '''
version: "2"
conda:
  files: environment.yml
    '''
    assertInvalidConfig(
        tmpdir,
        content,
        ['conda.environment: Required']
    )


@pytest.mark.parametrize('value', ['stable', 'latest'])
def test_build(tmpdir, value):
    content = '''
version: "2"
build:
  image: "{value}"
    '''
    assertValidConfig(tmpdir, content.format(value=value))


def test_build_missing_image_key(tmpdir):
    content = '''
version: "2"
build:
  imagine: "2.0"  # note the typo
    '''
    assertValidConfig(tmpdir, content)


def test_build_invalid(tmpdir):
    content = '''
version: "2"
build:
  image: "9.0"
    '''
    assertInvalidConfig(
        tmpdir,
        content,
        ["build.image: '9.0' not in"]
    )


@pytest.mark.parametrize('value', ['2', '2.7', '3', '3.5', '3.6'])
def test_python_version(tmpdir, value):
    content = '''
version: "2"
python:
  version: "{value}"
    '''
    assertValidConfig(tmpdir, content.format(value=value))


def test_python_version_invalid(tmpdir):
    content = '''
version: "2"
python:
  version: "4"
    '''
    assertInvalidConfig(
        tmpdir,
        content,
        ["version: '4' not in"]
    )


def test_python_version_no_key(tmpdir):
    content = '''
version: "2"
python:
  guido: true
    '''
    assertValidConfig(tmpdir, content)


def test_python_requirements(tmpdir):
    content = '''
version: "2"
python:
  install:
    - requirements: docs/requirements.txt
    '''
    assertValidConfig(tmpdir, content)


def test_python_install_requirements(tmpdir):
    content = '''
version: "2"
python:
  install:
    - requirements: 23
    '''
    assertInvalidConfig(
        tmpdir,
        content,
        ['requirements:', "'23' is not a path"]
    )


@pytest.mark.parametrize('value', ['pip', 'setuptools'])
def test_python_install(tmpdir, value):
    content = '''
version: "2"
python:
  version: "3.6"
  install:
    - path: .
      method: {value}
    '''
    assertValidConfig(tmpdir, content.format(value=value))


def test_python_install_invalid(tmpdir):
    content = '''
version: "2"
python:
  install: guido
    '''
    assertInvalidConfig(
        tmpdir,
        content,
        ["python.install: 'guido' is not a list"]
    )


def test_python_install_null(tmpdir):
    content = '''
version: "2"
python:
  install: null
    '''
    assertValidConfig(tmpdir, content)


def test_python_install_extra_requirements(tmpdir):
    content = '''
version: "2"
python:
  install:
    - path: .
      extra_requirements:
        - test
        - dev
    '''
    assertValidConfig(tmpdir, content)


@pytest.mark.parametrize('value', ['', 'null', '[]'])
def test_python_extra_requirements_empty(tmpdir, value):
    content = '''
version: "2"
python:
  install:
    - path: .
      extra_requirements: {value}
    '''
    assertValidConfig(tmpdir, content.format(value=value))


@pytest.mark.parametrize('value', ['true', 'false'])
def test_python_system_packages(tmpdir, value):
    content = '''
version: "2"
python:
  system_packages: {value}
    '''
    assertValidConfig(tmpdir, content.format(value=value))


@pytest.mark.parametrize('value', ['not true', "''", '[]'])
def test_python_system_packages_invalid(tmpdir, value):
    content = '''
version: "2"
python:
  system_packages: {value}
    '''
    assertInvalidConfig(
        tmpdir,
        content.format(value=value),
        ['is not a bool']
    )


def test_sphinx(tmpdir):
    content = '''
version: "2"
sphinx:
  configuration: docs/conf.py
    '''
    assertValidConfig(tmpdir, content)


def test_sphinx_default_value(tmpdir):
    content = '''
version: "2"
sphinx:
  file: docs/conf.py  # Default value for configuration key
    '''
    assertValidConfig(tmpdir, content)


@pytest.mark.parametrize('value', ['2', 'non-existent-file.yml'])
def test_sphinx_invalid(tmpdir, value):
    content = '''
version: "2"
sphinx:
  configuration: {value}
    '''
    assertInvalidConfig(
        tmpdir,
        content,
        ['is not a path']
    )


def test_sphinx_fail_on_warning(tmpdir):
    content = '''
version: "2"
sphinx:
  fail_on_warning: true
    '''
    assertValidConfig(tmpdir, content)


@pytest.mark.parametrize('value', ['not true', "''", '[]'])
def test_sphinx_fail_on_warning_invalid(tmpdir, value):
    content = '''
version: "2"
sphinx:
  fail_on_warning: {value}
    '''
    assertInvalidConfig(
        tmpdir,
        content.format(value=value),
        ['is not a bool']
    )


def test_mkdocs(tmpdir):
    content = '''
version: "2"
mkdocs:
  configuration: mkdocs.yml
    '''
    assertValidConfig(tmpdir, content)


def test_mkdocs_default_value(tmpdir):
    content = '''
version: "2"
mkdocs:
  file: mkdocs.yml  # Default value for configuration key
    '''
    assertValidConfig(tmpdir, content)


@pytest.mark.parametrize('value', ['2', 'non-existent-file.yml'])
def test_mkdocs_invalid(tmpdir, value):
    content = '''
version: "2"
mkdocs:
  configuration: {value}
    '''
    assertInvalidConfig(
        tmpdir,
        content,
        ['is not a path']
    )


def test_mkdocs_fail_on_warning(tmpdir):
    content = '''
version: "2"
mkdocs:
  fail_on_warning: true
    '''
    assertValidConfig(tmpdir, content)


@pytest.mark.parametrize('value', ['not true', "''", '[]'])
def test_mkdocs_fail_on_warning_invalid(tmpdir, value):
    content = '''
version: "2"
mkdocs:
  fail_on_warning: {value}
    '''
    assertInvalidConfig(
        tmpdir,
        content.format(value=value),
        ['is not a bool']
    )


def test_submodules_include(tmpdir):
    content = '''
version: "2"
submodules:
  include:
    - one
    - two
    - three
  recursive: false
    '''
    assertValidConfig(tmpdir, content)


def test_submodules_include_all(tmpdir):
    content = '''
version: "2"
submodules:
include: all
    '''
    assertValidConfig(tmpdir, content)


def test_submodules_exclude(tmpdir):
    content = '''
version: "2"
submodules:
exclude:
  - one
  - two
  - three
    '''
    assertValidConfig(tmpdir, content)


def test_submodules_exclude_all(tmpdir):
    content = '''
version: "2"
submodules:
  exclude: all
  recursive: true
    '''
    assertValidConfig(tmpdir, content)


def test_redirects(tmpdir):
    content = '''
version: "2"
redirects:
  page:
    'guides/install.html': 'install.html'
        '''
    assertValidConfig(tmpdir, content)


def test_redirects_invalid(tmpdir):
    content = '''
version: "2"
redirects:
  page:
    'guides/install.html': true
    '''
    assertInvalidConfig(
        tmpdir,
        content,
        ['is not a str']
    )


@pytest.mark.parametrize('value', ['', 'null', '{}'])
def test_redirects_empty(tmpdir, value):
    content = '''
version: "2"
redirects: {value}
    '''
    assertValidConfig(tmpdir, content.format(value=value))
