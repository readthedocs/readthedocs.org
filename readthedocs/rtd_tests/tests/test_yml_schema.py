from os import path

import pytest
from readthedocs.rtdyml import BuildConfig
from readthedocs.rtd_tests.utils import apply_fs


def create_yaml(tmpdir, content):
    fs = {
        'environment.yml': '',
        'rtd.yml': content,
        'docs': {
            'conf.py': '',
            'requirements.txt': '',
        },
    }
    apply_fs(tmpdir, fs)
    return path.join(tmpdir.strpath, 'rtd.yml')


def assertValidConfig(tmpdir, content):
    file = create_yaml(tmpdir, content)
    build = BuildConfig(file)
    build.validate()


def assertInvalidConfig(tmpdir, content, msgs=()):
    file = create_yaml(tmpdir, content)
    with pytest.raises(ValueError) as excinfo:
        BuildConfig(file).validate()
    for msg in msgs:
        msg in str(excinfo.value)


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


@pytest.mark.parametrize('value', ['1.0', '2.0', 'latest'])
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


def test_no_python_version(tmpdir):
    content = '''
version: "2"
python:
  guido: true
    '''
    assertValidConfig(tmpdir, content)


def test_valid_requirements(tmpdir):
    content = '''
version: "2"
python:
  requirements: docs/requirements.txt
    '''
    assertValidConfig(tmpdir, content)


def test_invalid_requirements_file(tmpdir):
    content = '''
version: "2"
python:
  requirements: 23
    '''
    assertInvalidConfig(
        tmpdir,
        content,
        ['requirements:', "'23' is not a path"]
    )


@pytest.mark.parametrize('value', ['pip', 'setup.py'])
def test_python_install(tmpdir, value):
    content = '''
version: "2"
python:
  version: "3.6"
  install: {value}
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
        ["python.install: 'guido' not in"]
    )


def test_python_extra_requirements(tmpdir):
    content = '''
version: "2"
python:
  extra_requirements:
    - test
    - dev
    '''
    assertValidConfig(tmpdir, content)


def test_python_extra_requirements_invalid(tmpdir):
    content = '''
version: "2"
python:
  extra_requirements:
    - 1
    - dev
    '''
    assertInvalidConfig(
        tmpdir,
        content,
        ["'1' is not a str"]
    )


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
  file: docs/conf.py  # Default value for configuration key
    '''
    assertValidConfig(tmpdir, content)


@pytest.mark.parametrize('value', ['2', 'environment.py'])
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


def test_invalid_redirects(tmpdir):
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
