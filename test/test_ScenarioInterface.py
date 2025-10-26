import pytest
import pandas as pd
import numpy as np
from io import StringIO
from math import isclose
import itertools

from pyewe import EwEScenarioInterface

from .utils import (
    ECOTRACER_GROUP_INFO_PATH,
    ECOSIM_GROUP_INFO_PATH,
    VULNERABILITIES_PATH,
    CONTAMINANT_FORCING_PATH,
    assert_arrays_close,
)

BLACK_SEA_FG_NAMES = [
    "01_Large pelagics",
    "02_Large demersal",
    "03_Merlangius",
    "04_Mullus and Spicara",
    "05_Small pelagics",
    "06_Belone and Scomber",
    "07_Zoobenthos",
    "08_Mesozooplankton",
    "09_Ciliates",
    "10_Chaetognaths",
    "11_Jellies",
    "12_Appendicularians",
    "13_Noctituca",
    "14_Bacteria",
    "15_Phytoplankton",
    "16_Detritus"
]

ECOSIM_FG_PARAM_NAMES = [
    "density_dep_catchability",
    "feeding_time_adj_rate",
    "max_rel_feeding_time",
    "max_rel_pb",
    "pred_effect_feeding_time",
    "other_mort_feeding_time",
    "qbmax_qbio",
    "switching_power"
]

ECOSIM_ENV_PARAM_NAMES = [
]

ECOTRACER_FG_PARAM_NAMES = [
    "init_c",
    "immig_c",
    "direct_abs_r",
    "phys_decay_r",
    "meta_decay_r",
    "excretion_r"
]

ECOTRACER_ENV_PARAM_NAMES = [
    "env_init_c",
    "env_base_inflow_r",
    "env_decay_r",
    "base_vol_ex_loss",
    "env_inflow_forcing_idx"
]

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
        col_names.extend(ewe_int.parameter_manager.get_available_parameter_names(
            model_type="ecotracer",
            param_types="fg",
            prefixes=pref
        ))

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
    scen_df = ewe_int.get_empty_scenarios_df([], 1)

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
        col_names.extend(ewe_int.parameter_manager.get_available_parameter_names(
            model_type="ecotracer",
            param_types="fg",
            prefixes=pref
        ))

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
    scen_df = ewe_int.get_empty_scenarios_df([], 1)

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

class TestParamNameRetrieval:

    def test_ecosim_fg_retrieval(self, scenario_interface):
        """Test retrieval of functional group parameter names in ecosim."""
        param_names = set(scenario_interface.parameter_manager.get_available_parameter_names("ecosim", "fg"))
        fg_prefixes = [pn + "_" for pn in ECOSIM_FG_PARAM_NAMES]
        expected = set(''.join(s) for s  in itertools.product(fg_prefixes, BLACK_SEA_FG_NAMES))

        assert (expected == param_names)


    def test_ecotracer_fg_retrieval(self, scenario_interface):
        """Test retrieval of functional group parameter names in ecotracer."""
        param_names = set(scenario_interface.parameter_manager.get_available_parameter_names("ecotracer", "fg"))
        fg_prefixes = [pn + "_" for pn in ECOTRACER_FG_PARAM_NAMES]
        expected = set(''.join(s) for s  in itertools.product(fg_prefixes, BLACK_SEA_FG_NAMES))

        assert (expected == param_names)

    def test_ecosim_env_retrieval(self, scenario_interface):
        """Test retrieval of environmental parmeter names in ecosim."""
        param_names = set(scenario_interface.parameter_manager.get_available_parameter_names("ecosim", "env"))
        assert (set(ECOSIM_ENV_PARAM_NAMES) == param_names)

    def test_ecotracer_env_retrieval(self, scenario_interface):
        """Test retrieval of environmental parameter names in  ecotracer."""
        param_names = set(scenario_interface.parameter_manager.get_available_parameter_names("ecotracer", "env"))
        assert (set(ECOTRACER_ENV_PARAM_NAMES) == param_names)

    def test_all_ecosim(self, scenario_interface):
        """test retrieval of all ecotracer parameter names."""
        param_names = set(scenario_interface.parameter_manager.get_available_parameter_names("ecosim"))
        fg_prefixes = [pn + "_" for pn in ECOSIM_FG_PARAM_NAMES]
        expected = set(''.join(s) for s  in itertools.product(fg_prefixes, BLACK_SEA_FG_NAMES))

        assert (expected == param_names)

    def test_all_ecotracer(self, scenario_interface):
        """Test retrieval of all ecotracer parameter names."""
        param_names = set(scenario_interface.parameter_manager.get_available_parameter_names("ecotracer"))
        fg_prefixes = [pn + "_" for pn in ECOTRACER_FG_PARAM_NAMES]
        fg_expected = set(''.join(s) for s  in itertools.product(fg_prefixes, BLACK_SEA_FG_NAMES))
        env_expected = set(ECOTRACER_ENV_PARAM_NAMES)
        expected = fg_expected.union(env_expected)

        assert (expected == param_names)

    def test_all_parameters(self, scenario_interface):
        """Test retrieval of all parameters (ecosim + ecotracer)."""
        param_names = set(scenario_interface.parameter_manager.get_available_parameter_names())
        tracer_fg_prefixes = [pn + "_" for pn in ECOTRACER_FG_PARAM_NAMES]
        tracer_fg_expected = set(''.join(s) for s  in itertools.product(tracer_fg_prefixes, BLACK_SEA_FG_NAMES))
        tracer_env_expected = set(ECOTRACER_ENV_PARAM_NAMES)
        tracer_expected = tracer_fg_expected.union(tracer_env_expected)

        sim_fg_prefixes = [pn + "_" for pn in ECOSIM_FG_PARAM_NAMES]
        sim_expected = set(''.join(s) for s  in itertools.product(sim_fg_prefixes, BLACK_SEA_FG_NAMES))
        expected = tracer_expected.union(sim_expected)

        assert (expected == param_names)
