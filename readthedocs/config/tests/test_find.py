from __future__ import division, print_function, unicode_literals

import os

import pytest
import six

from readthedocs.config.find import find_all, find_one

from .utils import apply_fs


def test_find_no_files(tmpdir):
    with tmpdir.as_cwd():
        paths = list(find_all(os.getcwd(), r'readthedocs.yml'))
    assert len(paths) == 0


def test_find_at_root(tmpdir):
    apply_fs(tmpdir, {'readthedocs.yml': '', 'otherfile.txt': ''})

    base = str(tmpdir)
    paths = list(find_all(base, r'readthedocs\.yml'))
    assert paths == [
        os.path.abspath(os.path.join(base, 'readthedocs.yml'))
    ]


def test_find_nested(tmpdir):
    apply_fs(tmpdir, {
        'first': {
            'readthedocs.yml': '',
        },
        'second': {
            'confuser.txt': 'content',
        },
        'third': {
            'readthedocs.yml': 'content',
            'Makefile': '',
        },
    })
    apply_fs(tmpdir, {'first/readthedocs.yml': ''})

    base = str(tmpdir)
    paths = set(find_all(base, r'readthedocs\.yml'))
    assert paths == {
        str(tmpdir.join('first', 'readthedocs.yml')),
        str(tmpdir.join('third', 'readthedocs.yml')),
    }


def test_find_multiple_files(tmpdir):
    apply_fs(tmpdir, {
        'first': {
            'readthedocs.yml': '',
            '.readthedocs.yml': 'content',
        },
        'second': {
            'confuser.txt': 'content',
        },
        'third': {
            'readthedocs.yml': 'content',
            'Makefile': '',
        },
    })
    apply_fs(tmpdir, {'first/readthedocs.yml': ''})

    base = str(tmpdir)
    paths = set(find_all(base, r'\.?readthedocs\.yml'))
    assert paths == {
        str(tmpdir.join('first', 'readthedocs.yml')),
        str(tmpdir.join('first', '.readthedocs.yml')),
        str(tmpdir.join('third', 'readthedocs.yml')),
    }


@pytest.mark.skipif(not six.PY2, reason='Only for python2')
def test_find_unicode_path(tmpdir):
    base_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), 'fixtures/bad_encode_project')
    )
    path = find_one(base_path, r'readthedocs\.yml')
    assert path == ''
    unicode_base_path = base_path.decode('utf-8')
    assert isinstance(unicode_base_path, unicode)
    path = find_one(unicode_base_path, r'readthedocs\.yml')
    assert path == ''
