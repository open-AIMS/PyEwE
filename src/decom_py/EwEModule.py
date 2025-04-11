import clr
import sys
from pathlib import Path
from importlib import import_module
from warnings import warn

_ewe_core_module = None

def initialise(ewe_binary_dir: str) -> None:
    """Initialise the EwE Core binaries.

    Args:
        ewe_binary_dir (str): Path to a directory containing EwE binaries.
    """
    global _ewe_core_module 

    ewe_bin_dir = Path(ewe_binary_dir)
    if not ewe_bin_dir.exists():
        raise FileNotFoundError(ewe_bin_dir)

    ewe_core_path = ewe_bin_dir.joinpath('EwECore.dll')
    if not ewe_core_path.exists():
        raise FileNotFoundError(ewe_core_path)

    clr.AddReference(str(ewe_core_path))

    _ewe_core_module = import_module('EwECore')
        

def get_ewe_core_module():
    """Get the EwE Core module."""
    if _ewe_core_module is None:
        raise RuntimeError("EwE Core module not initialised. Call initialise().")

    return _ewe_core_module
