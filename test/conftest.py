import os
import pytest
import tempfile
import shutil
from pathlib import Path

@pytest.fixture(scope="session")
def get_ewe_bin_dir() -> str:
    ewe_bin_dir = os.environ.get("EWE_BIN_DIR_PATH") 
    
    if ewe_bin_dir is None:
        pytest.skip("EwE bin path not provided. Set EWE_BIN_DIR_PATH environment variable.")
        return ""

    ewe_bin_path = Path(ewe_bin_dir)
    if not ewe_bin_path.exists():
        pytest.skip(f"EwE binaries not found at {ewe_bin_dir}.")
        return ""

    return str(ewe_bin_path.resolve())

@pytest.fixture(scope="session")
def temp_dir():
    temp_dir = tempfile.mkdtemp()
    yield temp_dir

    shutil.rmtree(temp_dir)

@pytest.fixture(scope="session")
def get_model_path() -> str:
    model_path = os.environ.get("EWE_MODEL_PATH") 
    
    if model_path is None:
        pytest.skip("EwE model path not provided. Set EWE_MODEL_PATH environment variable.")
        return ""

    ewe_model_path = Path(model_path)
    if not ewe_model_path.exists():
        pytest.skip(f"Model file not found at {model_path}.")

    temp_model_path = Path(temp_dir) / original_path.name
    shutil.copy2(original_path, temp_model_path)
    
    # Return the path to the temporary copy
    return str(temp_model_path)
