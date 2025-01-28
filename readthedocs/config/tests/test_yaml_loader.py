from readthedocs.doc_builder.backends.mkdocs import ProxyPythonName, yaml_load_safely

content = """
int: 3
float: !!float 3
function: !!python/name:python_function
other_function: !!python/name:module.other.function
unknown: !!python/module:python_module
"""


def test_yaml_load_safely():
    expected = {
        "int": 3,
        "float": 3.0,
        "function": ProxyPythonName("python_function"),
        "other_function": ProxyPythonName("module.other.function"),
        "unknown": None,
    }
    data = yaml_load_safely(content)

    assert data == expected
    assert type(data["int"]) is int
    assert type(data["float"]) is float
    assert type(data["function"]) is ProxyPythonName
    assert type(data["other_function"]) is ProxyPythonName
    assert data["function"].value == "python_function"
    assert data["other_function"].value == "module.other.function"
