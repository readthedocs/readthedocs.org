# -*- coding: utf-8 -*-
from __future__ import division, print_function, unicode_literals

import os

from mock import patch
from pytest import raises
from six import text_type

from readthedocs.config.validation import (
    INVALID_BOOL, INVALID_CHOICE, INVALID_DIRECTORY, INVALID_FILE, INVALID_LIST,
    INVALID_PATH, INVALID_STRING, ValidationError, validate_bool,
    validate_choice, validate_directory, validate_file, validate_list,
    validate_path, validate_string)


class TestValidateBool(object):
    def test_it_accepts_true(self):
        assert validate_bool(True) is True

    def test_it_accepts_false(self):
        assert validate_bool(False) is False

    def test_it_accepts_0(self):
        assert validate_bool(0) is False

    def test_it_accepts_1(self):
        assert validate_bool(1) is True

    def test_it_fails_on_string(self):
        with raises(ValidationError) as excinfo:
            validate_bool('random string')
        assert excinfo.value.code == INVALID_BOOL


class TestValidateChoice(object):

    def test_it_accepts_valid_choice(self):
        result = validate_choice('choice', ('choice', 'another_choice'))
        assert result is 'choice'

        with raises(ValidationError) as excinfo:
            validate_choice('c', 'abc')
        assert excinfo.value.code == INVALID_LIST

    def test_it_rejects_invalid_choice(self):
        with raises(ValidationError) as excinfo:
            validate_choice('not-a-choice', ('choice', 'another_choice'))
        assert excinfo.value.code == INVALID_CHOICE


class TestValidateList(object):

    def test_it_accepts_list_types(self):
        result = validate_list(['choice', 'another_choice'])
        assert result == ['choice', 'another_choice']

        result = validate_list(('choice', 'another_choice'))
        assert result == ['choice', 'another_choice']

        def iterator():
            yield 'choice'

        result = validate_list(iterator())
        assert result == ['choice']

        with raises(ValidationError) as excinfo:
            validate_choice('c', 'abc')
        assert excinfo.value.code == INVALID_LIST

    def test_it_rejects_string_types(self):
        with raises(ValidationError) as excinfo:
            result = validate_list('choice')
        assert excinfo.value.code == INVALID_LIST


class TestValidateDirectory(object):

    def test_it_uses_validate_path(self, tmpdir):
        patcher = patch('readthedocs.config.validation.validate_path')
        with patcher as validate_path:
            path = text_type(tmpdir.mkdir('a directory'))
            validate_path.return_value = path
            validate_directory(path, str(tmpdir))
            validate_path.assert_called_with(path, str(tmpdir))

    def test_it_rejects_files(self, tmpdir):
        tmpdir.join('file').write('content')
        with raises(ValidationError) as excinfo:
            validate_directory('file', str(tmpdir))
        assert excinfo.value.code == INVALID_DIRECTORY


class TestValidateFile(object):

    def test_it_uses_validate_path(self, tmpdir):
        patcher = patch('readthedocs.config.validation.validate_path')
        with patcher as validate_path:
            path = tmpdir.join('a file')
            path.write('content')
            path = str(path)
            validate_path.return_value = path
            validate_file(path, str(tmpdir))
            validate_path.assert_called_with(path, str(tmpdir))

    def test_it_rejects_directories(self, tmpdir):
        tmpdir.mkdir('directory')
        with raises(ValidationError) as excinfo:
            validate_file('directory', str(tmpdir))
        assert excinfo.value.code == INVALID_FILE


class TestValidatePath(object):

    def test_it_accepts_relative_path(self, tmpdir):
        tmpdir.mkdir('a directory')
        validate_path('a directory', str(tmpdir))

    def test_it_accepts_files(self, tmpdir):
        tmpdir.join('file').write('content')
        validate_path('file', str(tmpdir))

    def test_it_accepts_absolute_path(self, tmpdir):
        path = str(tmpdir.mkdir('a directory'))
        validate_path(path, 'does not matter')

    def test_it_returns_absolute_path(self, tmpdir):
        tmpdir.mkdir('a directory')
        path = validate_path('a directory', str(tmpdir))
        assert path == os.path.abspath(path)

    def test_it_only_accepts_strings(self):
        with raises(ValidationError) as excinfo:
            validate_path(None, '')
        assert excinfo.value.code == INVALID_STRING

    def test_it_rejects_non_existent_path(self, tmpdir):
        with raises(ValidationError) as excinfo:
            validate_path('does not exist', str(tmpdir))
        assert excinfo.value.code == INVALID_PATH


class TestValidateString(object):

    def test_it_accepts_unicode(self):
        result = validate_string(u'Unicöde')
        assert isinstance(result, text_type)

    def test_it_accepts_nonunicode(self):
        result = validate_string('Unicode')
        assert isinstance(result, text_type)

    def test_it_rejects_float(self):
        with raises(ValidationError) as excinfo:
            validate_string(123.456)
        assert excinfo.value.code == INVALID_STRING

    def test_it_rejects_none(self):
        with raises(ValidationError) as excinfo:
            validate_string(None)
        assert excinfo.value.code == INVALID_STRING
