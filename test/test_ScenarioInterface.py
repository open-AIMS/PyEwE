import pytest
import shutil
import os
import pandas as pd
import numpy as np
from io import StringIO
from math import isclose

from decom_py import EwEScenarioInterface

RESOURCES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources")
OUTDIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "resources", "test_outputs", "tmp"
)

ECOTRACER_GROUP_INFO_PATH = os.path.join(
    RESOURCES, "test_inputs", "BlackSea-Ecotracer input.csv"
)
ECOSIM_GROUP_INFO_PATH = os.path.join(
    RESOURCES, "test_inputs", "BlackSea-Group info.csv"
)
VULNERABILITIES_PATH = os.path.join(
    RESOURCES, "test_inputs", "BlackSea-Vulnerabilities.csv"
)

TARGET_ECOSIM_DIR = os.path.join(RESOURCES, "test_outputs", "ecosim")
TARGET_ECOTRACER_DIR = os.path.join(RESOURCES, "test_outputs", "ecotracer")
TARGET_BIOMASS_PATH = os.path.join(TARGET_ECOSIM_DIR, "test_biomass_annual.csv")
TARGET_CATCH_PATH = os.path.join(TARGET_ECOSIM_DIR, "test_catch_annual.csv")
TARGET_CATCH_FLEET_PATH = os.path.join(
    TARGET_ECOSIM_DIR, "test_catch-fleet-group_annual.csv"
)
TARGET_MORTALITY_PATH = os.path.join(TARGET_ECOSIM_DIR, "test_mortality_annual.csv")

TARGET_ECOTRACER_OUT_PATH = os.path.join(
    TARGET_ECOTRACER_DIR, "target_ecotracer_outputs.csv"
)

def ewe_df_to_arr(df_path):
    with open(df_path, "r") as file:
        # Skip lines until you reach the CSV header
        lines = file.readlines()
        matches = [
            i for i, line in enumerate(lines) if "year" in line or "time" in line
        ][0]

        csv_data = pd.read_csv(StringIO("".join(lines[matches:])))

    return csv_data.to_numpy()


def remove_csv_files(directory_path):
    # Iterate through files in the directory (excluding nested directories)
    for file_name in os.listdir(directory_path):
        # Get the full path of the file
        file_path = os.path.join(directory_path, file_name)

        # Check if it's a file (not a directory) and ends with '.csv'
        if os.path.isfile(file_path) and file_name.endswith(".csv"):
            # Remove the file using shutil
            shutil.os.remove(file_path)
            print(f"Removed: {file_name}")


@pytest.fixture(scope="session")
def cleanup():
    # Setup code (runs before the test)
    print("Setting up resources")

    yield  # The test runs after this point

    # Cleanup code (runs after the test)
    remove_csv_files(OUTDIR)

@pytest.fixture(scope="class")
def scenario_run_results(model_path, ewe_module, cleanup):
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
    print(f"Running scenario once for fixture in {OUTDIR}...")
    ewe_int.run_scenarios(scen_df, OUTDIR) # Run into the dedicated fixture dir

    return OUTDIR # Provide the output directory to tests

def assert_arrays_close(expected, produced, rtol=1e-7, atol=1e-9, context=""):
    """
    Asserts that two numpy arrays are close element-wise.
    Provides detailed failure message if they are not.
    """
    if expected.shape != produced.shape:
        pytest.fail(f"Shape mismatch {context}: Expected {expected.shape}, Got {produced.shape}")

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


@pytest.mark.filterwarnings("ignore:Additive prop")
class TestScenarioInterface:

    def test_biomass_output(self, scenario_run_results):
        expected = ewe_df_to_arr(TARGET_BIOMASS_PATH)
        produced = ewe_df_to_arr(os.path.join(OUTDIR, "biomass_annual.csv"))
        assert_arrays_close(expected, produced, context="for biomass_annual.csv")

    def test_catch_output(self, scenario_run_results):
        expected = ewe_df_to_arr(TARGET_CATCH_PATH)
        produced = ewe_df_to_arr(os.path.join(OUTDIR, "catch_annual.csv"))
        assert_arrays_close(expected, produced, context="for catch_annual.csv")

    def test_catch_fleet_output(self, scenario_run_results):
        expected = ewe_df_to_arr(TARGET_CATCH_FLEET_PATH)
        produced = ewe_df_to_arr(os.path.join(OUTDIR, "catch-fleet-group_annual.csv"))
        assert_arrays_close(expected, produced, context="for catch-fleet-group_annual.csv")

    def test_mortality_output(self, scenario_run_results):
        expected = ewe_df_to_arr(TARGET_MORTALITY_PATH)
        produced = ewe_df_to_arr(os.path.join(OUTDIR, "mortality_annual.csv"))
        assert_arrays_close(expected, produced, context="for mortality_annual.csv")

    def test_ecotracer_output(self, scenario_run_results):
        expected = ewe_df_to_arr(TARGET_ECOTRACER_OUT_PATH)
        produced = ewe_df_to_arr(os.path.join(OUTDIR, "ecotracer_res_scen_0.csv"))
        assert_arrays_close(expected, produced, context="for ecotracer_res_scen_0.csv")
