import pandas as pd
import numpy as np
import xarray as xr
import multiprocessing as mp
from datetime import datetime
from typing import Optional
from numpy.ctypeslib import ctypes

from .config import STD_DIM_NAMES, CATEGORY_CONFIG, VARIABLE_CONFIG
from .results_set import ResultSet
from ..core import results_extraction


def select_dim_len(
    dim_name: str, n_scenarios: int, n_groups: int, n_months: int
) -> int:
    """Given the dimension name, select the length of the dimension."""
    if dim_name == "scenario":
        return n_scenarios
    elif dim_name == "group":
        return n_groups
    elif dim_name == "time":
        return n_months
    elif dim_name == "env_group":
        return n_groups + 1  # Functional groups + environment group.
    raise ValueError(f"Dimension {dim_name} not supported.")


def select_dim_values(dim_name: str, n_scenarios: int, group_names, n_months: int):
    """Given a dimension name, construct the values for the coordinates."""
    if dim_name == "scenario":
        return range(n_scenarios)
    elif dim_name == "group":
        return group_names
    elif dim_name == "time":
        return range(n_months)
    elif dim_name == "env_group":
        return ["Environment", *group_names]  # Functional groups + environment group.
    raise ValueError(f"Dimension {dim_name} not supported.")


def construct_var_buffer(
    variable_name: str, n_scenarios: int, n_groups: int, n_months: int
):
    """Given an variable names, construct a multiprocessor buffer."""
    # Get variable specification
    var_conf = VARIABLE_CONFIG[variable_name]
    var_cat = var_conf["category"]
    # Get dimensions spec
    var_dims = var_conf["dims"]
    var_shape = [
        select_dim_len(dim_n, n_scenarios, n_groups, n_months) for dim_n in var_dims
    ]
    # Create an array with 64 bit float
    return mp.Array("d", int(np.prod(var_shape)))


def construct_xarray(
    variable_name: str,
    n_scenarios: int,
    group_names: list[str],
    n_months: int,
    first_year: int,
    buffer=None,
):
    """Given a variable name and the size of dimensions, construct an empty xarray.

    Arguments:
        variable_name (str): Name of variable
        n_scenarios (int): Number of scenarios
        group_names (list[str]): List of names of functional groups
        n_months (int): Number of months the simulation is run for.
        first_year (int): First year of simulations
        buffer (Optional[mp.array]): Multiprocessor buffer to use as underlying memory for
            xarrray
    """
    # Get variable specification
    var_conf = VARIABLE_CONFIG[variable_name]
    var_cat = var_conf["category"]
    # Get dimensions spec
    var_dims = var_conf["dims"]
    var_shape = [
        select_dim_len(dim_n, n_scenarios, len(group_names), n_months)
        for dim_n in var_dims
    ]
    # Construct dimensions for xarray
    # Get standard dimension names
    var_dims_names = CATEGORY_CONFIG[var_cat]["dims"]
    coords = [
        select_dim_values(dim_n, n_scenarios, group_names, n_months)
        for dim_n in var_dims
    ]
    if buffer is None:
        data = np.empty(tuple(var_shape), dtype=float)
    else:
        data = np.frombuffer(buffer.get_obj(), dtype=np.float64).reshape(
            tuple(var_shape)
        )

    empty_xr = xr.DataArray(data, coords=coords, dims=var_dims_names)
    # Fill in attributes
    empty_xr.attrs["name"] = var_conf["variable_name"]
    empty_xr.attrs["unit"] = var_conf["unit"]
    empty_xr.attrs["Run Date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    empty_xr.attrs["First Year"] = first_year

    return empty_xr


def construct_extraction_objects(var_names, py_core) -> tuple[list, dict]:
    """Construct results extractors."""
    # Get the name of all extractor constructors
    extractor_names = [VARIABLE_CONFIG[var_n]["extractor_name"] for var_n in var_names]
    # Get unique names and so duplicate objects are not constructed
    uniq_names = list(set(extractor_names))
    # For each variable, get an index for each unique extractor
    extr_index = [uniq_names.index(var_n) for var_n in extractor_names]
    # Construct the extractors for each variable.
    uniq_extractor_objs = [
        getattr(results_extraction, extr)(py_core.get_core(), py_core.get_state())
        for extr in uniq_names
    ]
    # Construct a dictionary of variable names to variable extractors
    variable_extractors = {
        var_name: uniq_extractor_objs[i] for (var_name, i) in zip(var_names, extr_index)
    }
    # Get unique names and so duplicate objects are not constructed
    return uniq_extractor_objs, variable_extractors


class ResultManager:
    """A result manager collects, formats and writes results.

    The result manager uses result extractors to extract results from the EwE core and
    format them in to xarray data arrays. When the scenarios runs are completed, the result
    manager can write the results to a range of formats.

    Attributes:
        _py_core: EwE python core wrapper instance.
        _var_names: The names of variables to save. Should match those found in config.py
        _scenarios: Scenario dataframe for the corresponding model runs.
        variable_stores (dict): Dictionary of xarrays, one for each variable being recorded.
        _unique_extractors (list): Result extractors used to get results from the core.
            Unique.
        _variable_extractors (dict): Same underlying objects as _unique_extractors but
            aligned with variable_ordering
        _packed_input (dict): name of variables to query result extractors when multiple variables
            are packaed into the same array in visual basic.
    """

    def __init__(
        self,
        py_core,
        var_names,
        scenarios: pd.DataFrame,
        shared_store: Optional[dict] = None,
    ):
        self._py_core = py_core
        self._var_names = var_names
        self._scenarios = scenarios

        self._n_months = py_core.Ecosim.get_n_years() * 12
        self._n_scenarios = len(scenarios)
        self._group_names = py_core.get_functional_group_names()

        first_year = self._py_core.get_first_year()

        if not shared_store is None:
            if set(shared_store.keys()) != set(var_names):
                msg = "Shared stores keys do not match variables names"
                msg += f". Received {shared_store.keys} and {var_names}"
                raise KeyError(msg)
            # Construct variable stores from multiprocessing buffer
            self.variable_stores = {
                vn: construct_xarray(
                    vn,
                    self._n_scenarios,
                    self._group_names,
                    self._n_months,
                    first_year,
                    shared_store[vn],
                )
                for vn in var_names
            }
        else:
            self.variable_stores = {
                vn: construct_xarray(
                    vn, self._n_scenarios, self._group_names, self._n_months, first_year
                )
                for vn in var_names
            }

        # Get the result extractors and a list of extractors aligned with variables
        self._unique_extractors, self._variable_extractors = (
            construct_extraction_objects(var_names, py_core)
        )
        # Get the inputs needed for the extracts get_result function.
        self._packed_input = {
            nm: VARIABLE_CONFIG[nm]["extractor_input"] for nm in var_names
        }

    @staticmethod
    def construct_mp_result_manager(py_core, var_names, scenarios):
        """Construct a result manager using multiprocessor arrays.

        Construct a result manager that uses multiprocessor arrays as the underlying buffer
        for the stored xarrays.

        Arguments:
            py_core (CoreInstance): Core instance to extract results from.
            var_names (list[str]): List of result varibles to store.
            scenarios (DataFrame): Dataframe containing the parameters used for each
                scenario
        """
        _n_months = py_core.Ecosim.get_n_years() * 12
        _n_scenarios = len(scenarios)
        _n_groups = len(py_core.get_functional_group_names())

        mp_buffers = {
            vn: construct_var_buffer(vn, _n_scenarios, _n_groups, _n_months)
            for vn in var_names
        }

        manager = ResultManager(py_core, var_names, scenarios, mp_buffers)

        return manager, mp_buffers

    def refresh_result_stores(self):
        """Load the ecosim results into the Result Extraction Buffers."""
        for extractor in self._unique_extractors:
            extractor.refresh_buffer()

    def collect_results(self, scenario_idx: int):
        """Load the ecosim results into the variable_stores."""
        self.refresh_result_stores()
        dim_index = {STD_DIM_NAMES["scenario"]: scenario_idx}
        for var_name in self._var_names:
            get_input = self._packed_input[var_name]
            var_arr = self.variable_stores[var_name]
            var_extr = self._variable_extractors[var_name]

            var_arr[dim_index] = (
                var_extr.get_result()
                if get_input == ""
                else var_extr.get_result(get_input)
            )

    def to_result_set(self):
        """Construct a results set from a result manager."""
        return ResultSet(self._py_core, self._scenarios, self.variable_stores)
