from __future__ import division, print_function, unicode_literals

from .utils import apply_fs


def test_apply_fs_with_empty_contents(tmpdir):
    # Doesn't do anything if second parameter is empty.
    apply_fs(tmpdir, {})
    assert tmpdir.listdir() == []


def test_apply_fs_create_empty_file(tmpdir):
    # Create empty file.
    apply_fs(tmpdir, {'file': ''})
    assert len(tmpdir.listdir()) == 1
    assert tmpdir.join('file').read() == ''


def test_apply_fs_create_file_with_content(tmpdir):
    # Create file with content.
    apply_fs(tmpdir, {'file': 'content'})
    assert tmpdir.join('file').read() == 'content'


def test_apply_fs_create_subdirectory(tmpdir):
    # Create file with content.
    apply_fs(tmpdir, {'subdir': {'file': 'content'}})
    assert tmpdir.join('subdir', 'file').read() == 'content'
