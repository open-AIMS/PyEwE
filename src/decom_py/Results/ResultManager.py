import pandas as pd
import numpy as np
import XArray as xr
from datetime import datetime

from .config import STD_DIM_NAMES, CATEGORY_CONFIG, VARIABLE_CONFIG
from .. import EwEResultExtraction

def parse_group_stats_df(filepath: str, var_name: str, lines_to_skip: int):
    df = pl.read_csv(filepath, skip_lines=lines_to_skip)

    return df.unpivot(index="time step", variable_name="Group", value_name=var_name)

def select_dim_len(dim_name: str, n_scenarios: int, n_groups: int, n_months: int) -> int:
    if dim_name == STD_DIM_NAMES["scenario"]:
        return n_scenarios
    elif dim_name == STD_DIM_NAMES["group"]:
        return n_groups
    elif dim_name == STD_DIM_NAMES["time"]:
        return n_months
    raise ValueError(f"Dimension {dim_name} not supported.")

def construct_xarray(
    variable_name: str,
    n_scenarios: int,
    n_groups: int,
    n_months: int
):
    """Given a variable name and the size of dimensions, construct an empty xarray."""
    var_conf = VARIABLE_CONFIG[variable_name]
    var_cat = var_conf["category"]
    var_dims = CATEGORY_CONFIG[var_cat]["dims"]
    var_shape = [
        select_dim_len(dim_n, n_scenarios, n_groups, n_months)
        for dim_n in var_dims
    ]
    coords  = [range(dim_len) for dim_len in var_shape]
    data = np.empty(tuple(var_shape), dtype=float)
    empty_xr = xr.DataArray(data, coords=coords, dims=var_dims)
    empty_xr.attrs["name"] = var_conf["variable_name"]
    empty_xr.attrs["unit"] = var_conf["unit"]
    empty_xr.attrs["unit"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return empty_xr

def construct_extraction_objects(var_names, py_core):
    """Construct results constructors"""
    # Get the name of all extractor constructors
    extractor_names = [
        VARIABLE_CONFIG[var_n]["extractor_name"]
    ]
    # Get unique names and so duplicate objects are not constructed
    uniq_names = list(set(extractor_names))
    extr_index = [uniq_names.index(var_n) for var_n in extractor_names]
    uniq_extractor_objs = [
        getattr(EwEResultExtraction, extr)(py_core.get_core(), py_core.get_state())
        for extr in uniq_names
    ]
    # Get unique names and so duplicate objects are not constructed
    return [uniq_extractor_objs[i] for i in extr_index]

class ResultManager:

    def __init__(
        self,
        py_core,
        var_names,
        scenarios: pd.DataFrame,
        save_dir: str
    ):
        self._py_core = py_core
        self._scenarios = scenarios
        self._save_dir = save_dir
        self._ecotracer_results = None

        self._n_months = py_core.Ecosim.get_n_years() * 12
        self._n_scenarios = len(scenarios)
        self._n_groups = py_core.n_groups()

        self._variable_stores = [
            construct_xarray(vn, self._n_scenarios, self._n_groups, self._n_months)
            for vn in var_names
        ]
        # Get the result extractors and a list of extractors aligned with variables
        self._unique_extractors, self._variable_extractors = construct_extraction_objects(
            var_names, py_core
        )
        # Get the inputs needed for the extracts get_results function.
        self._packed_input = [
            VARIABLE_CONFIG[nm]["extractor_input"] for nm in var_names
        ]

    def refresh_result_stores(self):
        """Load the ecosim results into the Result Extraction Buffers."""
        for extractor in self._unique_extractors:
            extractor.refresh_buffer()

    def collect_results(self, scenario_idx: int):
        for (var_arr, var_extr, ex_in) in zip(
            self._variable_stores,
            self._variable_extractors,
            self._packed_input
        ):
            var_arr[
                {'STD_DIM_NAMES["scenario"]': scenario_idx}
            ] = var_extr.get_results() if ex_in == "" else var_extr.get_results(ex_in)
