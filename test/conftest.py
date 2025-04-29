from os import environ
from os import path
from decom_py import get_ewe_core_module
import pytest
import tempfile
import shutil
from pathlib import Path

from decom_py import initialise, get_ewe_core_module


@pytest.fixture(scope="session")
def ewe_module():
    ewe_bin_dir = environ.get("EWE_BIN_DIR_PATH")

    if ewe_bin_dir is None:
        pytest.skip(
            "EwE bin path not provided. Set EWE_BIN_DIR_PATH environment variable."
        )
        return ""

    ewe_bin_path = Path(ewe_bin_dir)
    if not ewe_bin_path.exists():
        pytest.skip(f"EwE binaries not found at {ewe_bin_dir}.")
        return None

    initialise(str(ewe_bin_path.resolve()))

    return get_ewe_core_module()

@pytest.fixture(scope="session")
def model_path():
    return path.join(
        path.dirname(path.abspath(__file__)), "resources", "BlackSea.EwEaccdb"
    )

@pytest.fixture(scope="session")
def tmp_model_path(tmpdir_factory) -> str:
    model_path = path.join(
        path.dirname(path.abspath(__file__)), "resources", "BlackSea.EwEaccdb"
    )

    mod_path_obj = Path(model_path)
    if not mod_path_obj.exists():
        pytest.skip(f"Model file not found at {model_path}.")

    temp_model_path = tmpdir_factory.mktemp("model").join(mod_path_obj.name)
    shutil.copy2(model_path, temp_model_path)

    # Return the path to the temporary copy
    return str(temp_model_path)
