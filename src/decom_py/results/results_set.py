import os
import pandas as pd
import numpy as np
from typing import Optional

from .config import VARIABLE_CONFIG, CATEGORY_CONFIG

def variable_arr_to_flat_df(var_arr):
    """Convert an xarray to a flattened dataframe with the correct variable name."""
    var_name = var_arr.attrs["name"]
    return var_arr.to_dataframe(name=var_name).reset_index()


class ResultSet:
    """Contains results after scenario runs.

    This class is the user facing store of results. It should not contain references to the
    core object, and should contains all output results and scenario being run.

    Attributes:
        scenarios (dict): Dataframe containing scenario specification for results.
        results (dict): Dictionary mapping result variable names to xarrays.
        country (str): Name of country that the EwE model is based in.
        first_year (int): First Year ecosim is run.
        n_scenarios (int): Number of scenarios run.
        n_varied params (int): Number of parameters changed between scenarios.
    """

    def __init__(self, py_core, scenarios, results: dict):
        self.scenarios = scenarios
        self.results = results
        self._variable_names = list(self.results.keys())

        self.country = py_core.get_country()
        self.first_year = py_core.get_first_year()
        self.n_scenarios = len(self.scenarios)
        self.n_varied_params = self.scenarios.shape[1]

    def __str__(self):
        return f"""
Country: {self.country}
Scenarios Run: {self.n_scenarios}
First Year: {self.first_year}
# Varied Parameters: {self.n_varied_params}
Stored Results: {list(self.results.keys())}
        """

    def __repr__(self):
        return f"ResultSet Object\n {self.__str__()}"

    def __getitem__(self, key):
        return self.results[key]

    def _write_netcdfs(self, save_dir: str):
        """Write all variables to netcdf files."""
        for var_name in self._variable_names:
            filename = VARIABLE_CONFIG[var_name]["save_filename"] + ".nc"
            ds = self.results[var_name].to_dataset(name=var_name)
            ds.to_netcdf(os.path.join(save_dir, filename))

    def _write_dataframes(self, save_dir: str):
        """Write all variables to csv files."""
        categories = [VARIABLE_CONFIG[var_n]["category"] for var_n in self._variable_names]
        unique_cats = list(set(categories))
        dfs: list[Optional[pd.DataFrame]] = [None] * len(unique_cats)

        # Create a data frame for each category and add variables to each category.
        for var_name, var_cat in zip(self._variable_names, categories):
            cat_idx = unique_cats.index(var_cat)
            df_arr = variable_arr_to_flat_df(self.results[var_name])

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

    def save_results(self, save_dir: str, formats: list[str]):
        """Write results to all formats given.

        Only NetCDF4, "netcdf", and CSV, "csv", are currently supported.

        Args:
            formats list[str]: list of formats to save results in.

        """
        if "netcdf" in formats:
            self._write_netcdfs(save_dir)
        if "csv" in formats:
            self._write_dataframes(save_dir)
