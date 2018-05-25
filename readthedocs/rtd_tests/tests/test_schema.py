from os import getcwd, path

import pytest
import yamale
from django.test import TestCase
from readthedocs.rtd_tests.utils import apply_fs


class TestYAMLSchemaV2(TestCase):

    def setUp(self):
        base_path = path.join(getcwd(), 'rtd_tests/fixtures/spec/v2')
        self.schema = yamale.make_schema(
            path.join(base_path, 'schema.yml')
        )

    @pytest.fixture(autouse=True)
    def tmpdir(self, tmpdir):
        self.tmpdir = tmpdir

    def create_yaml(self, content):
        fs = {
            'rtd.yml': content,
        }
        apply_fs(self.tmpdir, fs)
        return path.join(self.tmpdir.strpath, 'rtd.yml')

    def assertValidConfig(self, content):
        file = self.create_yaml(content)
        data = yamale.make_data(file)
        yamale.validate(self.schema, data)

    def assertInvalidConfig(self, content, msgs=()):
        file = self.create_yaml(content)
        data = yamale.make_data(file)
        with pytest.raises(ValueError) as excinfo:
            yamale.validate(self.schema, data)
        for msg in msgs:
            self.assertIn(msg, str(excinfo.value))

    def test_minimal_config(self):
        self.assertValidConfig('version: "2"')

    def test_invalid_version(self):
        self.assertInvalidConfig(
            'version: "latest"',
            ["version: 'latest' not in"]
        )

    def test_invalid_version_1(self):
        self.assertInvalidConfig(
            'version: "1"',
            ["version: '1' not in"]
        )

    def test_valid_formats(self):
        content = '''
version: "2"
formats:
  - pdf
  - singlehtmllocalmedia
        '''
        self.assertValidConfig(content)

    def test_all_valid_formats(self):
        content = '''
version: "2"
formats:
  - htmlzip
  - pdf
  - epub
  - singlehtmllocalmedia
        '''
        self.assertValidConfig(content)

    def test_valid_formats_all(self):
        content = '''
version: "2"
formats: all
        '''
        self.assertValidConfig(content)

    def test_invalid_formats(self):
        content = '''
version: "2"
formats:
  - invalidformat
  - singlehtmllocalmedia
        '''
        self.assertInvalidConfig(
            content,
            ['formats', "'invalidformat' not in"]
        )

    def tets_empty_formats(self):
        content = '''
version: "2"
formats: []
        '''
        self.assertValidConfig(content)

    def test_valid_requirements_file(self):
        content = '''
version: "2"
requirements_file: docs/requirements.txt
        '''
        self.assertValidConfig(content)

    def test_invalid_requirements_file(self):
        content = '''
version: "2"
requirements_file: 23
        '''
        self.assertInvalidConfig(
            content,
            ["requirements_file: '23' is not a str"]
        )

    def test_valid_conda(self):
        content = '''
version: "2"
conda:
  file: environment.yml
        '''
        self.assertValidConfig(content)

    def test_invalid_conda(self):
        content = '''
version: "2"
conda:
   files: environment.yml
        '''
        self.assertInvalidConfig(
            content,
            ['conda.file: Required']
        )

    def test_valid_build(self):
        content = '''
version: "2"
build:
  image: "{image}"
        '''
        for image in ['1.0', '2.0', 'latest']:
            self.assertValidConfig(content.format(image=image))

    def test_missing_key_build(self):
        content = '''
version: "2"
build:
  imagine: "2.0"
        '''
        self.assertInvalidConfig(
            content,
            ['build.image: Required']
        )

    def test_invalid_build(self):
        content = '''
version: "2"
build:
  image: "4.0"
        '''
        self.assertInvalidConfig(
            content,
            ["build.image: '4.0' not in"]
        )

    def test_python_version(self):
        content = '''
version: "2"
python:
  version: "{version}"
        '''
        versions = ['2', '2.7', '3', '3.3', '3.4', '3.5', '3.6']
        for version in versions:
            self.assertValidConfig(content.format(version=version))

    def test_invalid_python_version(self):
        content = '''
version: "2"
python:
  version: "4"
        '''
        self.assertInvalidConfig(
            content,
            ["version: '4' not in"]
        )

    def test_no_python_version(self):
        content = '''
version: "2"
python:
  guido: true
        '''
        self.assertValidConfig(content)

    def test_python_install(self):
        content = '''
version: "2"
python:
  version: "3.6"
  install: {install}
        '''
        for install in ['pip', 'setup.py']:
            self.assertValidConfig(content.format(install=install))

    def test_invalid_python_install(self):
        content = '''
version: "2"
python:
  install: guido
        '''
        self.assertInvalidConfig(
            content,
            ["python.install: 'guido' not in"]
        )

    def test_python_extra_requirements(self):
        content = '''
version: "2"
python:
  extra_requirements:
    - test
    - dev
        '''
        self.assertValidConfig(content)

    def test_invalid_python_extra_requirements(self):
        content = '''
version: "2"
python:
  extra_requirements:
    - 1
    - dev
        '''
        self.assertInvalidConfig(
            content,
            ["'1' is not a str"]
        )

    def test_python_system_packages(self):
        content = '''
version: "2"
python:
  system_packages: {option}
        '''
        for option in ['true', 'false']:
            self.assertValidConfig(content.format(option=option))

    def test_invalid_python_system_packages(self):
        content = '''
version: "2"
python:
  system_packages: not true
        '''
        self.assertInvalidConfig(content, ['is not a bool'])

    def test_sphinx(self):
        content = '''
version: "2"
sphinx:
   file: docs/conf.py
        '''
        self.assertValidConfig(content)

    def test_invalid_sphinx(self):
        content = '''
version: "2"
sphinx:
  file: 2
        '''
        self.assertInvalidConfig(
            content,
            ['is not a str']
        )

    def test_submodules_include(self):
        content = '''
version: "2"
submodules:
  include:
    - one
    - two
    - three
  recursive: false
        '''
        self.assertValidConfig(content)

    def test_submodules_include_all(self):
        content = '''
version: "2"
submodules:
  include: all
        '''
        self.assertValidConfig(content)

    def test_submodules_exclude(self):
        content = '''
version: "2"
submodules:
  exclude:
    - one
    - two
    - three
        '''
        self.assertValidConfig(content)

    def test_submodules_exclude_all(self):
        content = '''
version: "2"
submodules:
  exclude: all
  recursive: true
        '''
        self.assertValidConfig(content)

    def test_redirects(self):
        content = '''
version: "2"
redirects:
  page:
    'guides/install.html': 'install.html'
            '''
        self.assertValidConfig(content)

    def test_invalid_redirects(self):
        content = '''
version: "2"
redirects:
  page:
    'guides/install.html': true
        '''
        self.assertInvalidConfig(
            content,
            ['is not a str']
        )
