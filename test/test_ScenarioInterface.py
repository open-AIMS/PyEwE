import pytest
import shutil
import os
import pandas as pd
import numpy as np
from io import StringIO
from math import isclose

from decom_py import EwEScenarioInterface

RESOURCES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources")

# Model parameter file paths
ECOTRACER_GROUP_INFO_PATH = os.path.join(
    RESOURCES, "test_inputs", "BlackSea-Ecotracer input.csv"
)
ECOSIM_GROUP_INFO_PATH = os.path.join(
    RESOURCES, "test_inputs", "BlackSea-Group info.csv"
)
VULNERABILITIES_PATH = os.path.join(
    RESOURCES, "test_inputs", "BlackSea-Vulnerabilities.csv"
)

def remove_files(directory_path):
    # Iterate through files in the directory (excluding nested directories)
    shutil.rmtree(directory_path)
    os.makedirs(directory_path, exist_ok=True)

@pytest.fixture(scope="class")
def scenario_run_results(model_path, ewe_module):
    """Runs the scenario once and provides the output directory."""
    ewe_int = EwEScenarioInterface(model_path)

    ecosim_group_info = pd.read_csv(ECOSIM_GROUP_INFO_PATH)
    ecosim_vuln = pd.read_csv(VULNERABILITIES_PATH)
    ecotracer_params = pd.read_csv(ECOTRACER_GROUP_INFO_PATH)

    # Set up ecosim parameters
    ewe_int.set_ecosim_group_info(ecosim_group_info)
    ewe_int.set_ecosim_vulnerabilities(ecosim_vuln)
    ewe_int.set_simulation_duration(75)

    # Set up scenario DataFrame
    p_prefixes = [
        "init_c",
        "immig_c",
        "direct_abs_r",
        "phys_decay_r",
        "excretion_r",
        "meta_decay_r",
    ]
    vals = [1.0]
    col_names = ["scenario"]
    for i, pref in enumerate(p_prefixes):
        vals.extend(list(ecotracer_params.iloc[:, 2 + i]))
        col_names.extend(ewe_int.get_ecotracer_fg_param_names(pref))

    vals.extend([0.2, 0.1, 0.0002, 0.005])
    col_names.extend(
        ["env_init_c", "env_base_inflow_r", "env_decay_r", "base_vol_ex_loss"]
    )
    scen_df = pd.DataFrame([vals], columns=col_names)

    # Run scenarios
    res = ewe_int.run_scenarios(scen_df)

    ewe_int.reset_parameters()

    ewe_int._core_instance.Ecosim.load_scenario("test_outputs")
    ewe_int._core_instance.Ecotracer.load_scenario("test_outputs")
    scen_df = ewe_int.get_empty_scenarios_df([], [], 1)

    res_target = ewe_int.run_scenarios(scen_df)

    yield res, res_target

    ewe_int._core_instance.close_model()


def assert_arrays_close(expected, produced, rtol=1e-7, atol=1e-9, context=""):
    """
    Asserts that two numpy arrays are close element-wise.
    Provides detailed failure message if they are not.
    """
    if expected.shape != produced.shape:
        pytest.fail(
            f"Shape mismatch {context}: Expected {expected.shape}, Got {produced.shape}"
        )

    are_close = np.allclose(expected, produced, rtol=rtol, atol=atol)

    if not are_close:
        abs_diff = np.abs(expected - produced)
        max_abs_diff = np.max(abs_diff)
        max_abs_diff_idx = np.unravel_index(np.argmax(abs_diff), abs_diff.shape)

        num_diff = np.sum(~np.isclose(expected, produced, rtol=rtol, atol=atol))
        sum_abs_diff = np.sum(abs_diff)

        fail_msg = (
            f"Array comparison failed {context} (rtol={rtol}, atol={atol}).\n"
            f"  Max absolute difference: {max_abs_diff:.4g} at index {max_abs_diff_idx}\n"
            f"  Number of differing elements: {num_diff} / {expected.size}\n"
            f"  Total absolute difference sum: {sum_abs_diff:.4g}"
        )
        pytest.fail(fail_msg)

class TestScenarioInterface:

    def test_biomass_output(self, scenario_run_results):
        scen_index = {"Scenario": 0}
        expected = scenario_run_results[1]["Biomass"][scen_index].values
        produced = scenario_run_results[0]["Biomass"][scen_index].values
        # Remove timestep column from array
        assert_arrays_close(expected, produced, context="for biomass_monthly.csv")

    def test_catch_output(self, scenario_run_results):
        scen_index = {"Scenario": 0}
        expected = scenario_run_results[1]["Catch"][scen_index].values
        produced = scenario_run_results[0]["Catch"][scen_index].values
        # Remove timestep column from array
        assert_arrays_close(expected, produced, context="for catch_monthly.csv")

    def test_catch_fleet_output(self, scenario_run_results):
        scen_index = {"Scenario": 0}
        pytest.skip("Support fleet statistics.")
        expected = scenario_run_results[1]["todo"][scen_index].values
        produced = scenario_run_results[0]["todo"][scen_index].values
        assert_arrays_close(
            expected, produced, context="for catch-fleet-group_monthly.csv"
        )

    def test_mortality_output(self, scenario_run_results):
        scen_index = {"Scenario": 0}
        expected = scenario_run_results[1]["Mortality"][scen_index].values
        produced = scenario_run_results[0]["Mortality"][scen_index].values
        # Remove timestep column from array
        assert_arrays_close(expected, produced, context="for mortality_monthly.csv")

    def test_ecotracer_output(self, scenario_run_results):
        scen_index = {"Scenario": 0}
        expected = scenario_run_results[1]["Concentration"][scen_index].values
        produced = scenario_run_results[0]["Concentration"][scen_index].values
        # Remove timestep column from array
        assert_arrays_close(expected, produced, context="for ecotracer_res_scen_0.csv")
