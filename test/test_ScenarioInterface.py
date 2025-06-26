import pytest
import pandas as pd
import numpy as np
from io import StringIO
from math import isclose

from pyewe import EwEScenarioInterface

from .utils import (
    ECOTRACER_GROUP_INFO_PATH,
    ECOSIM_GROUP_INFO_PATH,
    VULNERABILITIES_PATH,
    CONTAMINANT_FORCING_PATH,
    assert_arrays_close,
)


@pytest.fixture(scope="class")
def scenario_run_results(model_path):
    """Runs the scenario once and provides two result sets that should be equal."""
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

    ewe_int.cleanup()


@pytest.fixture(scope="class")
def scenario_run_results_w_forcing(model_path):
    """
    Runs the scenario once with ecotracer contaminant forcing and returns two results sets
    that should be equal.
    """
    ewe_int = EwEScenarioInterface(model_path)  # , "temporary.eweaccdb")

    ecosim_group_info = pd.read_csv(ECOSIM_GROUP_INFO_PATH)
    ecosim_vuln = pd.read_csv(VULNERABILITIES_PATH)
    ecotracer_params = pd.read_csv(ECOTRACER_GROUP_INFO_PATH)
    contaminant_forcing = pd.read_csv(CONTAMINANT_FORCING_PATH)
    forcing_vals = list(contaminant_forcing["Y"])

    # Set up ecosim parameters
    ewe_int.set_ecosim_group_info(ecosim_group_info)
    ewe_int.set_ecosim_vulnerabilities(ecosim_vuln)
    ewe_int.set_simulation_duration(75)

    # Add available forcing function.
    forcing_idx = ewe_int.add_forcing_function("testing", forcing_vals)

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

    vals.extend([0.2, 0.1, 0.0002, 0.005, forcing_idx])
    col_names.extend(
        [
            "env_init_c",
            "env_base_inflow_r",
            "env_decay_r",
            "base_vol_ex_loss",
            "env_inflow_forcing_idx",
        ]
    )
    scen_df = pd.DataFrame([vals], columns=col_names)

    # Run scenarios
    res = ewe_int.run_scenarios(scen_df)

    ewe_int.reset_parameters()

    ewe_int._core_instance.Ecosim.load_scenario("test_outputs")
    ewe_int._core_instance.Ecotracer.load_scenario("test_outputs")
    # Make sure
    ewe_int._core_instance.Ecotracer.set_contaminant_forcing_number(1)
    scen_df = ewe_int.get_empty_scenarios_df([], [], 1)

    res_target = ewe_int.run_scenarios(scen_df)

    yield res, res_target

    ewe_int.cleanup()


@pytest.fixture(scope="class")
def scenario_interface(model_path):
    ewe_int = EwEScenarioInterface(model_path)
    yield ewe_int
    ewe_int.cleanup()


class TestScenarioInterface:

    @pytest.mark.parametrize(
        "scen_results", ["scenario_run_results", "scenario_run_results_w_forcing"]
    )
    def test_biomass_output(self, request, scen_results):
        results = request.getfixturevalue(scen_results)
        scen_index = {"Scenario": 0}
        expected = results[1]["Biomass"][scen_index].values
        produced = results[0]["Biomass"][scen_index].values
        # Remove timestep column from array
        assert_arrays_close(expected, produced, context="for biomass_monthly.csv")

    @pytest.mark.parametrize(
        "scen_results", ["scenario_run_results", "scenario_run_results_w_forcing"]
    )
    def test_catch_output(self, request, scen_results):
        results = request.getfixturevalue(scen_results)
        scen_index = {"Scenario": 0}
        expected = results[1]["Catch"][scen_index].values
        produced = results[0]["Catch"][scen_index].values
        # Remove timestep column from array
        assert_arrays_close(expected, produced, context="for catch_monthly.csv")

    @pytest.mark.parametrize(
        "scen_results", ["scenario_run_results", "scenario_run_results_w_forcing"]
    )
    def test_catch_fleet_output(self, request, scen_results):
        results = request.getfixturevalue(scen_results)
        scen_index = {"Scenario": 0}
        pytest.skip("Support fleet statistics.")
        expected = results[1]["todo"][scen_index].values
        produced = results[0]["todo"][scen_index].values
        assert_arrays_close(
            expected, produced, context="for catch-fleet-group_monthly.csv"
        )

    @pytest.mark.parametrize(
        "scen_results", ["scenario_run_results", "scenario_run_results_w_forcing"]
    )
    def test_mortality_output(self, request, scen_results):
        results = request.getfixturevalue(scen_results)
        scen_index = {"Scenario": 0}
        expected = results[1]["Mortality"][scen_index].values
        produced = results[0]["Mortality"][scen_index].values
        # Remove timestep column from array
        assert_arrays_close(expected, produced, context="for mortality_monthly.csv")

    @pytest.mark.parametrize(
        "scen_results", ["scenario_run_results", "scenario_run_results_w_forcing"]
    )
    def test_ecotracer_output(self, request, scen_results):
        results = request.getfixturevalue(scen_results)
        scen_index = {"Scenario": 0}
        expected = results[1]["Concentration"][scen_index].values
        produced = results[0]["Concentration"][scen_index].values
        # Remove timestep column from array
        assert_arrays_close(expected, produced, context="for ecotracer_res_scen_0.csv")


class TestFormatParamNames:

    def test_format_param_names(self, scenario_interface):
        """Test th3e format param names helper functions."""

        # Test Inputs
        full_p_names = [
            "Initial conc. (t/t)",
            "Conc. in immigrating biomass (t/t)",
            "Direct absorption rate",
            "Physical decay rate",
            "Prop. of contaminant excreted",
            "Metabolic decay rate",
        ]
        fg_names = [
            "Large pelagics",  # 1
            "Large demersal",  # 2
            "Small pelagics",  # 5
            "Belone and Scomber",  # 6
            "Chaetognaths",  # 10
            "Noctituca",  # 13
        ]

        # Expected Outputs
        expected = [
            "init_c_01_Large pelagics",
            "immig_c_02_Large demersal",
            "direct_abs_r_05_Small pelagics",
            "phys_decay_r_06_Belone and Scomber",
            "excretion_r_10_Chaetognaths",
            "meta_decay_r_13_Noctituca",
        ]

        # Outputs
        returned = scenario_interface.format_param_names(full_p_names, fg_names)
        assert all([ret == ex for (ret, ex) in zip(returned, expected)])
