from __future__ import division, print_function, unicode_literals

import os
import pytest
import six
from readthedocs.config.find import find_one

from .utils import apply_fs


def test_find_no_files(tmpdir):
    with tmpdir.as_cwd():
        path = find_one(os.getcwd(), r'readthedocs.yml')
    assert path == ''


def test_find_at_root(tmpdir):
    apply_fs(tmpdir, {'readthedocs.yml': '', 'otherfile.txt': ''})
    base = str(tmpdir)
    path = find_one(base, r'readthedocs\.yml')
    assert path == os.path.abspath(os.path.join(base, 'readthedocs.yml'))


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
