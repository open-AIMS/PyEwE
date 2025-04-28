import polars as pl
import pandas as pd
import os
import shutil

def parse_group_stats_df(filepath: str, var_name: str, lines_to_skip: int):
    df = pl.read_csv(filepath, skip_lines=lines_to_skip)

    return df.unpivot(index="time step", variable_name="Group", value_name=var_name)

class ResultManager:


    def __init__(self, py_core, scenarios: pd.DataFrame, save_dir: str):
        self._py_core = py_core
        self._scenarios = scenarios
        self._save_dir = save_dir
        self._ecotracer_results = None

        self._ecotracer_tmp_save_path = os.path.join(
            os.path.join(self._save_dir), "_tmp_tracer.csv"
        )

    def collect_results(self, scenario_idx: int):
        self._py_core.save_ecotracer_results(self._ecotracer_tmp_save_path)
        tracer_res = parse_group_stats_df(self._ecotracer_tmp_save_path, "Concentration", 14)
        tracer_res = tracer_res.with_columns(
            pl.lit(scenario_idx).alias("Scenario")
        )
        tracer_res = tracer_res.select(["Scenario"] + tracer_res.columns[:-1])

        if self._ecotracer_results is None:
            self._ecotracer_results = tracer_res
        else:
            self._ecotracer_results = pl.concat([self._ecotracer_results], how="diagonal")

        shutil.os.remove(self._ecotracer_tmp_save_path)

    def write_results(self):
        self._scenarios.to_csv(os.path.join(self._save_dir, "scenarios.csv"))
        self._ecotracer_results.write_csv(os.path.join(self._save_dir, "ecotracer_results.csv"))
