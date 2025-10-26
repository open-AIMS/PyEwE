from pyewe.results.manager import construct_extraction_objects
import pytest
import numpy as np
import pandas as pd

from pyewe import EwEScenarioInterface

from test.utils import (
    ECOTRACER_GROUP_INFO_PATH,
    ECOTRACER_GROUP_INFO_PATH2,
    ECOSIM_GROUP_INFO_PATH,
    VULNERABILITIES_PATH,
    assert_arrays_close,
)


def construct_ecotracer_df(ewe_int, filepath: str):
    """Construct a vector of params and names from a ecotracer group input file.

    Arguments:
        filepath (str): path to ecotracer group input file

    Returns:
        list[str]: list of names of parameters for columns.
        list[float]: list of values of parameters for dataframe.
    """
    ecotracer_params = pd.read_csv(filepath)

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
    return col_names, vals


@pytest.fixture(scope="class")
def multi_scen_res(model_path):
    """Runs the scenario once and provides two result sets that should be equal."""
    ewe_int = EwEScenarioInterface(model_path, constant_ecosim=True)

    ecosim_group_info = pd.read_csv(ECOSIM_GROUP_INFO_PATH)
    ecosim_vuln = pd.read_csv(VULNERABILITIES_PATH)
    col_names1, vals1 = construct_ecotracer_df(ewe_int, ECOTRACER_GROUP_INFO_PATH)
    _, vals2 = construct_ecotracer_df(ewe_int, ECOTRACER_GROUP_INFO_PATH2)

    rows = np.tile([vals1, vals2], (20, 1))
    scen_df = pd.DataFrame(rows, columns=col_names1)

    # Set up ecosim parameters
    ewe_int.set_ecosim_group_info(ecosim_group_info)
    ewe_int.set_ecosim_vulnerabilities(ecosim_vuln)
    ewe_int.set_simulation_duration(75)

    # Run scenarios
    res = ewe_int.run_scenarios_parallel(scen_df, 4)
    yield res

    ewe_int.cleanup()


@pytest.fixture(scope="class")
def test_outputs_res(model_path):
    ewe_int = EwEScenarioInterface(model_path, constant_ecosim=True)
    ewe_int._core_instance.Ecosim.load_scenario("test_outputs")
    ewe_int._core_instance.Ecotracer.load_scenario("test_outputs")
    scen_df = ewe_int.get_empty_scenarios_df([], 1)
    res = ewe_int.run_scenarios(scen_df)
    yield res

    ewe_int.cleanup()


@pytest.fixture(scope="class")
def test_outputs_2_res(model_path):
    ewe_int = EwEScenarioInterface(model_path, constant_ecosim=True)
    ewe_int._core_instance.Ecosim.load_scenario("test_outputs")
    ewe_int._core_instance.Ecotracer.load_scenario("test_outputs_2")
    scen_df = ewe_int.get_empty_scenarios_df([], 1)
    res = ewe_int.run_scenarios(scen_df)
    yield res

    ewe_int.cleanup()


class TestParallelExecution:

    @pytest.mark.parametrize(
        "variable", ["Biomass", "Catch", "Mortality", "Concentration"]
    )
    def test_output(
        self, variable, multi_scen_res, test_outputs_res, test_outputs_2_res
    ):
        scen_index = {"Scenario": 0}
        expected1 = test_outputs_res[variable][scen_index].values
        expected2 = test_outputs_2_res[variable][scen_index].values

        for i in range(20):
            produced1 = multi_scen_res[variable][{"Scenario": 2 * i}].values
            produced2 = multi_scen_res[variable][{"Scenario": 2 * i + 1}].values
            assert_arrays_close(expected1, produced1, context=f"{variable} scenario 1")
            assert_arrays_close(expected2, produced2, context=f"{variable} scenario 2")
        return None
