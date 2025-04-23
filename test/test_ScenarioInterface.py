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
    TARGET_ECOSIM_DIR, "test_catch_fleet-group_annual.csv"
)
TARGET_MORTALITY_PATH = os.path.join(TARGET_ECOSIM_DIR, "test_mortality_annual.csv")


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


class TestScenarioInterface:
    @pytest.mark.filterwarnings("ignore:Additive prop")
    def test_single_scenario_run(self, model_path, ewe_module, cleanup):

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

        # Run scenarios and check outputs
        ewe_int.run_scenarios(scen_df, OUTDIR)

        expected = ewe_df_to_arr(TARGET_BIOMASS_PATH)
        produced = ewe_df_to_arr(os.path.join(OUTDIR, "biomass_annual.csv"))
        assert isclose(np.sum(np.abs(expected - produced)), 0.0, rel_tol=1e-7)

        expected = ewe_df_to_arr(TARGET_CATCH_PATH)
        produced = ewe_df_to_arr(os.path.join(OUTDIR, "catch_annual.csv"))
        assert isclose(np.sum(np.abs(expected - produced)), 0.0, rel_tol=1e-7)

        expected = ewe_df_to_arr(TARGET_CATCH_FLEET_PATH)
        produced = ewe_df_to_arr(os.path.join(OUTDIR, "catch_fleet-group_annual.csv"))
        assert isclose(np.sum(np.abs(expected - produced)), 0.0, rel_tol=1e-7)

        expected = ewe_df_to_arr(TARGET_MORTALITY_PATH)
        produced = ewe_df_to_arr(os.path.join(OUTDIR, "mortality_annual.csv"))
        assert isclose(np.sum(np.abs(expected - produced)), 0.0, rel_tol=1e-7)
