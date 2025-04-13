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

_ewe_ecosim_res_types = None

def initialise_ecosim_result_types():
    """Initialise global dictionary that maps between ecosim result types names and the enum"""
    global _ewe_ecosim_res_types

    type_enum = get_ewe_core_module().Ecosim.cEcosimResultWriter.eResultTypes
    _ewe_ecosim_res_types = {
        "Biomass": type_enum.Biomass,
        "ConsumptionBiomass": type_enum.ConsumptionBiomass,
        "PredationMortality": type_enum.PredationMortality,
        "Mortality": type_enum.Mortality,
        "FeedingTime": type_enum.FeedingTime,
        "Prey": type_enum.Prey,
        "Catch": type_enum.Catch,
        "Value": type_enum.Value,
        "AvgWeightOrProdCons": type_enum.AvgWeightOrProdCons,
        "TL": type_enum.TL,
        "TLC": type_enum.TLC,
        "KemptonsQ": type_enum.KemptonsQ,
        "ShannonDiversity": type_enum.ShannonDiversity,
        "FIB": type_enum.FIB,
        "TotalCatch": type_enum.TotalCatch,
        "CatchFleetGroup": type_enum.CatchFleetGroup,
        "MortFleetGroup": type_enum.MortFleetGroup,
        "ValueFleetGroup": type_enum.ValueFleetGroup
    }

def get_ecosim_result_type_enum(type_name: str):
    """Convert a ecosim result type name to the visual basic enumeration"""
    global _ewe_ecosim_res_types

    if _ewe_ecosim_res_types is None:
        initialise_ecosim_result_types()

    return _ewe_ecosim_res_types[type_name]
