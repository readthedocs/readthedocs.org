import os

from pytest import raises

from readthedocs.config.validation import (
    INVALID_BOOL,
    INVALID_CHOICE,
    INVALID_LIST,
    INVALID_STRING,
    ValidationError,
    validate_bool,
    validate_choice,
    validate_list,
    validate_path,
    validate_string,
)


class TestValidateBool:
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


class TestValidateChoice:

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


class TestValidateList:

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
            validate_list('choice')
        assert excinfo.value.code == INVALID_LIST


class TestValidatePath:

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


class TestValidateString:

    def test_it_accepts_unicode(self):
        result = validate_string('Unicöde')
        assert isinstance(result, str)

    def test_it_accepts_nonunicode(self):
        result = validate_string('Unicode')
        assert isinstance(result, str)

    def test_it_rejects_float(self):
        with raises(ValidationError) as excinfo:
            validate_string(123.456)
        assert excinfo.value.code == INVALID_STRING

    def test_it_rejects_none(self):
        with raises(ValidationError) as excinfo:
            validate_string(None)
        assert excinfo.value.code == INVALID_STRING
