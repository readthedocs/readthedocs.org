import textwrap
from readthedocs.doc_builder.backends.mkdocs import yaml_load_safely


def test_yaml_load_safely():
    expected = {
        'int': 3,
        'float': 3.0,
        'unknown': None,
    }

    content = textwrap.dedent('''
    int: 3
    float: !!float 3
    unknown: !!python/name:unknown_funtion
    ''')
    data = yaml_load_safely(content)
    assert data == expected
    assert type(data['int']) is int
    assert type(data['float']) is float
