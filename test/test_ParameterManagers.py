import pytest
from unittest.mock import Mock, call

from decom_py import EwEScenarioInterace, ParameterManager, Parameter, ParameterType

# Test globals outputs
FG_NAMES = ["Detritus", "Phytoplankton", "Mackerel", "Baleen Whale"]
N_FG = len(FG_NAMES)
N_CHARS = len(str(N_FG))

# Ecotracer Functional Group Parameter Prefixes
ECOTRACER_FG_PARAM_PREFIXES = [
    "init_c",
    "immig_c",
    "direct_abs_r",
    "phys_decay_r",
    "meta_decay_r",
    "excretion_r",
]
ECOTRACER_FG_SETTER = {
    0: "set_initial_concentrations",
    1: "set_immigration_concentrations",
    2: "set_direct_absorption_rates",
    3: "set_physical_decay_rates",
    4: "set_metabolic_decay_rates",
    5: "set_excretion_rates",
}
ECOTRACER_ENV_PARAMS = [
    "env_init_c",
    "env_base_inflow_r",
    "env_decay_r",
    "base_vol_ex_loss",
]
ECOTRACER_ENV_SETTERS = {
    0: "set_initial_env_concentration",
    1: "set_base_inflow_rate",
    2: "set_env_decay_rate",
    3: "set_env_volume_exchange_loss",
}

# Mock core getter and setters


@pytest.fixture(scope="function")
def mock_ecotracer(mocker):
    """Mock the ecotracer interface to check if getters and setters are called correctly."""
    tracer_m = mocker.Mock(
        spec=[
            "set_initial_concentrations",
            "set_immigration_concentrations",
            "set_direct_absorption_rates",
            "set_physical_decay_rates",
            "set_metabolic_decay_rates",
            "set_excretion_rates",
        ]
    )

    return tracer_m


@pytest.fixture(scope="function")
def mock_core_interface(mocker, mock_ecotracer):
    """Mock the core interface."""
    core_m = mocker.Mock(spec=["get_functional_group_names", "Ecotracer"])
    core_m.get_functional_group_names.return_value = FG_NAMES
    core_m.Ecotracer = mock_ecotracer

    return core_m


@pytest.fixture(scope="function")
def ecotracer_manager(mock_core_interface):
    """Create a Ecotracer Manager with a  mocked core."""
    manager = ParameterManager.EcotracerManager(mock_core_interface)
    return manager


class TestParameterManager:

    def test_ecotracer_factory(self, mock_core_interface, ecotracer_manager):
        """Test the construction of the Ecotracer Factory method."""
        mock_core_interface.get_functional_group_names.assert_called_once()

        assert ecotracer_manager.fg_names == FG_NAMES
        assert ecotracer_manager._fg_param_prefixes == ECOTRACER_FG_PARAM_PREFIXES
        assert ecotracer_manager._fg_param_to_setters == ECOTRACER_FG_SETTER
        assert ecotracer_manager._env_param_names == ECOTRACER_ENV_PARAMS
        assert ecotracer_manager._env_param_to_setter == ECOTRACER_ENV_SETTERS

        all_param_names: list[str] = ecotracer_manager.get_all_param_names()
        assert f"init_c_1_{FG_NAMES[0]}" in all_param_names
        assert f"immig_c_3_{FG_NAMES[2]}" in all_param_names
        assert f"phys_decay_r_2_{FG_NAMES[1]}" in all_param_names
        assert f"excretion_r_4_{FG_NAMES[3]}" in all_param_names

        fg_param_name = f"meta_decay_r_1_{FG_NAMES[0]}"
        stored_param = ecotracer_manager.params[fg_param_name]
        assert stored_param.param_type == ParameterType.UNSET
        assert stored_param.is_env_param == False
        assert stored_param.name == fg_param_name
        assert stored_param.category_idx == 4
        assert stored_param.group_idx == 1

        env_param_name = "env_init_c"
        stored_param = ecotracer_manager.params[env_param_name]
        assert stored_param.param_type == ParameterType.UNSET
        assert stored_param.is_env_param == True
        assert stored_param.name == env_param_name
        assert stored_param.category_idx == 0

    def test_format_parameter_names(self):
        """Test the construction of parameter names used in scenario dataframe."""

        assert "param_name_1_squid" == ParameterManager._format_param_name(
            "param_name", 1, 1, "squid"
        )
        assert "_test_name_010_termite" == ParameterManager._format_param_name(
            "_test_name", 10, 3, "termite"
        )
        assert "testing_100_fishes" == ParameterManager._format_param_name(
            "testing", 100, 3, "fishes"
        )

    def test_get_fg_param_names(self, ecotracer_manager):
        """Test get_fg_param_names returns the correct subset of parameter names."""
        init_c_prefix = ECOTRACER_FG_PARAM_PREFIXES[0]
        init_c_names = ecotracer_manager.get_fg_param_names(init_c_prefix)
        for p_name in init_c_names:
            assert init_c_prefix == p_name[: len(init_c_prefix)]

        assert f"init_c_1_{FG_NAMES[0]}" in init_c_names

        init_c_immig_c = ecotracer_manager.get_fg_param_names(["init_c", "immig_c"])
        assert f"init_c_3_{FG_NAMES[2]}" in init_c_immig_c
        assert f"immig_c_4_{FG_NAMES[3]}" in init_c_immig_c

        all_fg_names = ecotracer_manager.get_fg_param_names("all")
        assert f"init_c_1_{FG_NAMES[0]}" in all_fg_names
        assert f"immig_c_3_{FG_NAMES[2]}" in all_fg_names
        assert f"direct_abs_r_4_{FG_NAMES[3]}" in all_fg_names
        assert f"meta_decay_r_1_{FG_NAMES[0]}" in all_fg_names
        assert f"excretion_r_4_{FG_NAMES[3]}" in all_fg_names
        assert f"phys_decay_r_4_{FG_NAMES[3]}" in all_fg_names

    def test_set_constant_params(self, ecotracer_manager):
        """Test constant parameter set is reflects internal state properly"""
        init_c_names = ecotracer_manager.get_fg_param_names("init_c")
        init_c_vals = [0] * len(init_c_names)

        ecotracer_manager.set_constant_params(init_c_names, init_c_vals)
        for p_name in init_c_names:
            assert ecotracer_manager.params[p_name].param_type == ParameterType.CONSTANT
            assert ecotracer_manager.params[p_name].value == 0

        ecotracer_manager.set_constant_params(["env_init_c"], [0.0])
        assert (
            ecotracer_manager.params["env_init_c"].param_type == ParameterType.CONSTANT
        )
        assert ecotracer_manager, params["env_init_c"].value == 0

    def test_set_variable_params(self, ecotracer_manager):
        """Test variable parameter set is reflects internal state properly"""
        init_c_names = ecotracer_manager.get_fg_param_names("init_c")
        init_c_vals = [0] * len(init_c_names)

        ecotracer_manager.set_variable_params(init_c_names, init_c_vals)
        for p_name in init_c_names:
            assert ecotracer_manager.params[p_name].param_type == ParameterType.VARIABLE

        ecotracer_manager.set_variable_params(["env_init_c"], [0.0])
        assert (
            ecotracer_manager.params["env_init_c"].param_type == ParameterType.VARIABLE
        )

    def test_apply_constant_params(self, ecotracer_manager, mock_core_interface):
        """Check apply constant params calls the correct setter functions"""
        const_param_names = [
            f"init_c_1_{FG_NAMES[0]}",
            f"immig_c_2_{FG_NAMES[1]}",
            f"direct_abs_r_3_{FG_NAMES[2]}",
            f"excretion_r_4_{FG_NAMES[3]}",
            f"meta_decay_r_4_{FG_NAMES[3]}",
            f"phys_decay_r_4_{FG_NAMES[3]}",
        ]
        const_param_values = [0, 0, 0, 0, 0, 0]
        ecotracer_manager.set_constant_params(const_param_names, const_param_values)
        ecotracer_manager.apply_constant_params(mock_core_interface)

        mock_core_interface.Ecotracer.set_initial_concentrations.assert_called_with(
            [0], [1]
        )
        mock_core_interface.Ecotracer.set_immigration_concentrations.assert_called_with(
            [0], [2]
        )
        mock_core_interface.Ecotracer.set_direct_absorption_rates.assert_called_with(
            [0], [3]
        )
        mock_core_interface.Ecotracer.set_excretion_rates.assert_called_with([0], [4])
        mock_core_interface.Ecotracer.set_metabolic_decay_rates.assert_called_with(
            [0], [4]
        )
        mock_core_interface.Ecotracer.set_physical_decay_rates.assert_called_with(
            [0], [4]
        )

    def test_apply_variable_params(self, ecotracer_manager, mock_core_interface):
        """Check apply variables params calls the correct setter functions"""
        var_param_names = [
            f"init_c_1_{FG_NAMES[0]}",
            f"immig_c_2_{FG_NAMES[1]}",
            f"direct_abs_r_3_{FG_NAMES[2]}",
            f"excretion_r_4_{FG_NAMES[3]}",
            f"meta_decay_r_4_{FG_NAMES[3]}",
            f"phys_decay_r_4_{FG_NAMES[3]}",
        ]
        var_param_df_idx = [5, 4, 3, 2, 1, 0]
        var_param_values = [1, 2, 3, 4, 5, 6]
        ecotracer_manager.set_variable_params(var_param_names, var_param_df_idx)
        ecotracer_manager.apply_variable_params(mock_core_interface, var_param_values)

        mock_core_interface.Ecotracer.set_initial_concentrations.assert_called_with(
            [6], [1]
        )
        mock_core_interface.Ecotracer.set_immigration_concentrations.assert_called_with(
            [5], [2]
        )
        mock_core_interface.Ecotracer.set_direct_absorption_rates.assert_called_with(
            [4], [3]
        )
        mock_core_interface.Ecotracer.set_excretion_rates.assert_called_with([3], [4])
        mock_core_interface.Ecotracer.set_metabolic_decay_rates.assert_called_with(
            [2], [4]
        )
        mock_core_interface.Ecotracer.set_physical_decay_rates.assert_called_with(
            [1], [4]
        )
