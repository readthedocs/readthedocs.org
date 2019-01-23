# -*- coding: utf-8 -*-

def apply_fs(tmpdir, contents):
    """
    Create the directory structure specified in ``contents``.

    It's a dict of filenames as keys and the file contents as values. If the
    value is another dict, it's a subdirectory.
    """
    for filename, content in contents.items():
        if hasattr(content, 'items'):
            apply_fs(tmpdir.mkdir(filename), content)
        else:
            file = tmpdir.join(filename)
            file.write(content)
    return tmpdir
