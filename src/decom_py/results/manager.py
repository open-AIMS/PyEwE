import warnings
import pandas as pd
import numpy as np
import xarray as xr
import os
from datetime import datetime
from typing import Optional

from .config import STD_DIM_NAMES, CATEGORY_CONFIG, VARIABLE_CONFIG
from ..core import results_extraction


def variable_arr_to_flat_df(var_arr):
    """Convert an xarray to a flattened dataframe with the correct variable name."""
    var_name = var_arr.attrs["name"]
    return var_arr.to_dataframe(name=var_name).reset_index()


def select_dim_len(
    dim_name: str, n_scenarios: int, n_groups: int, n_months: int
) -> int:
    """Given the dimension name, select the len of the dimension."""
    if dim_name == "scenario":
        return n_scenarios
    elif dim_name == "group":
        return n_groups
    elif dim_name == "time":
        return n_months
    elif dim_name == "env_group":
        return n_groups + 1
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
        return ["Environment", *group_names]
    raise ValueError(f"Dimension {dim_name} not supported.")


def construct_xarray(
    variable_name: str,
    n_scenarios: int,
    group_names: list[str],
    n_months: int,
    first_year: int,
):
    """Given a variable name and the size of dimensions, construct an empty xarray."""
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
    data = np.empty(tuple(var_shape), dtype=float)
    empty_xr = xr.DataArray(data, coords=coords, dims=var_dims_names)
    # Fill in attributes
    empty_xr.attrs["name"] = var_conf["variable_name"]
    empty_xr.attrs["unit"] = var_conf["unit"]
    empty_xr.attrs["unit"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
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
        _variable_stores (dict): Dictionary of xarrays, one for each variable being recorded.
        _unique_extractors (list): Result extractors used to get results from the core. 
            Unique.
        _variable_extractors (dict): Same underlying objects as _unique_extractors but 
            aligned with variable_ordering
        _packed_input (dict): name of variables to query result extractors when multiple variables
            are packaed into the same array in visual basic.
    """

    def __init__(self, py_core, var_names, scenarios: pd.DataFrame):
        self._py_core = py_core
        self._var_names = var_names
        self._scenarios = scenarios

        self._n_months = py_core.Ecosim.get_n_years() * 12
        self._n_scenarios = len(scenarios)
        self._group_names = py_core.get_functional_group_names()

        first_year = self._py_core.get_first_year()
        self._variable_stores = {
            vn : construct_xarray(
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

    def refresh_result_stores(self):
        """Load the ecosim results into the Result Extraction Buffers."""
        for extractor in self._unique_extractors:
            extractor.refresh_buffer()

    def collect_results(self, scenario_idx: int):
        """Load the ecosim results into the _variable_stores."""
        self.refresh_result_stores()
        dim_index = {STD_DIM_NAMES["scenario"]: scenario_idx}
        for var_name in self._var_names:
            get_input = self._packed_input[var_name]
            var_arr = self._variable_stores[var_name]
            var_extr = self._variable_extractors[var_name]

            var_arr[dim_index] = (
                var_extr.get_result() if get_input == "" else var_extr.get_result(get_input)
            )

    def _write_netcdfs(self, save_dir: str):
        """Write all variables to netcdf files."""
        for var_name in self._var_names:
            filename = VARIABLE_CONFIG[var_name]["save_filename"] + ".nc"
            ds = self._variable_stores[var_name].to_dataset(name=var_name)
            ds.to_netcdf(os.path.join(save_dir, filename))

    def _write_dataframes(self, save_dir: str):
        """Write all variables to csv files."""
        categories = [VARIABLE_CONFIG[var_n]["category"] for var_n in self._var_names]
        unique_cats = list(set(categories))
        dfs: list[Optional[pd.DataFrame]] = [None] * len(unique_cats)

        # Create a data frame for each category and add variables to each category.
        for var_name, var_cat in zip(self._var_names, categories):
            cat_idx = unique_cats.index(var_cat)
            df_arr = variable_arr_to_flat_df(self._variable_stores[var_name])

            dfs[cat_idx] = df_arr if dfs[cat_idx] is None else pd.merge(
                dfs[cat_idx],
                df_arr,
                on=CATEGORY_CONFIG[var_cat]["dims"],
                how="outer",
            )

        for df, cat_name in zip(dfs, unique_cats):
            if df is None:
                raise ValueError("Category data frame is None and was not initialised.")

            df.to_csv(os.path.join(save_dir, cat_name + ".csv"), index=False)

    def write_results(self, save_dir: str, formats: list[str]):
        """Write results to all formats given.

        Only NetCDF4, "netcdf", and CSV, "csv", are currently supported.

        Args:
            formats list[str]: list of formats to save results in.

        """
        if "netcdf" in formats:
            self._write_netcdfs(save_dir)
        if "csv" in formats:
            self._write_dataframes(save_dir)
