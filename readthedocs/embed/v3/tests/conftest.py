import os
import shutil
import pytest

from .utils import srcdir


@pytest.fixture(autouse=True, scope="module")
def remove_sphinx_build_output():
    """Remove _build/ folder, if exist."""
    for path in (srcdir,):
        build_path = os.path.join(path, "_build")
        if os.path.exists(build_path):
            shutil.rmtree(build_path)
