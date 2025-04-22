from decom_py.Exceptions.EwEExceptions import EcotracerNoScenarioError
import pytest
from random import random, randint
from warnings import warn
from math import isclose

from decom_py import CoreInterface, EcotracerStateManager, EcosimStateManager
from decom_py.Exceptions import EwEError, EcopathError, EcosimError, EcotracerError
from decom_py.Exceptions import EcotracerNoScenarioError, EcosimNoScenarioError

N_GROUPS = 16
N_DETRITUS = 1
N_PRODUCERS = 1
N_CONSUMERS = N_GROUPS - N_PRODUCERS - N_DETRITUS

class TestScenarioAddRemove:

    def test_ecosim_load_scenario(self, model_path, ewe_module):

        core = CoreInterface()
        core.load_model(model_path)
        # Keep reference to internal core to test state directly
        internal_core = core.get_core()

        core.Ecosim.load_scenario("default_test")

        assert internal_core.get_EcosimScenarios(
            internal_core.ActiveEcosimScenarioIndex
        ).Name == "default_test"

        # save index to test loading with index
        scenario_index: int = internal_core.ActiveEcosimScenarioIndex

        core.Ecosim.close_scenario()
        assert (not internal_core.get_StateMonitor().HasEcosimLoaded())

        core.Ecosim.load_scenario(scenario_index)
        assert internal_core.get_EcosimScenarios(
            internal_core.ActiveEcosimScenarioIndex
        ).Name == "default_test"

        core.close_model()

    def test_ecosim_add_scenarios(self, model_path, ewe_module):

        core = CoreInterface()
        core.load_model(model_path)
        # Keep reference to internal core to test state directly
        internal_core = core.get_core()

        # record number of scenario before addition
        n_scenarios_before = core._core.nEcosimScenarios
        core.Ecosim.new_scenario("name", "description", "author", "contact")

        active_scenario = internal_core.get_EcosimScenarios(
            internal_core.ActiveEcosimScenarioIndex
        )

        assert internal_core.nEcosimScenarios == n_scenarios_before + 1
        assert active_scenario.Name == "name"
        assert active_scenario.Author == "author"
        assert active_scenario.Description == "description"
        assert active_scenario.Contact == "contact"

        core.close_model()

    def test_ecosim_remove_scenarios(self, model_path, ewe_module):

        core = CoreInterface()
        core.load_model(model_path)
        # Keep reference to internal core to test state directly
        internal_core = core.get_core()

        n_scenarios_before = internal_core.nEcosimScenarios
        is_loaded = core.Ecosim.load_scenario("remove_test")
        if not is_loaded:
            raise RuntimeError("Unable to load test scenario remove_test.")
        else:
            core.Ecosim.close_scenario()

        core.Ecosim.remove_scenario("remove_test")
        with pytest.raises(LookupError) as excinfo:
            core.Ecosim.load_scenario("remove_test")

        assert internal_core.nEcosimScenarios == n_scenarios_before - 1
        assert str(excinfo.value) == "Unable to find scenario named: remove_test"

        core.close_model()

    def test_ecotracer_load_scenarios(self, model_path, ewe_module):

        core = CoreInterface()
        core.load_model(model_path)
        # Keep reference to internal core to test state directly
        internal_core = core.get_core()

        core.Ecosim.load_scenario("default_test")
        core.Ecotracer.load_scenario("default_test")

        assert internal_core.get_EcotracerScenarios(
            internal_core.ActiveEcotracerScenarioIndex
        ).Name == "default_test"

        # save index to test loading with index
        scenario_index: int = internal_core.ActiveEcotracerScenarioIndex

        core.Ecotracer.close_scenario()
        assert (not core._state.HasEcotracerLoaded())

        core.Ecotracer.load_scenario(scenario_index)
        assert internal_core.get_EcotracerScenarios(
            internal_core.ActiveEcotracerScenarioIndex
        ).Name == "default_test"

        core.close_model()

    def test_ecotracer_add_scenarios(self, model_path, ewe_module):

        core = CoreInterface()
        core.load_model(model_path)
        # Keep reference to internal core to test state directly
        internal_core = core.get_core()

        # Load ecosim scenario before ecotracer
        core.Ecosim.load_scenario("default_test")

        # record number of scenario before addition
        n_scenarios_before = core._core.nEcotracerScenarios
        if not core.Ecotracer.new_scenario("name", "description", "author", "contact"):
            raise RunTimeError("Failed to create new scenario for testing.")

        active_scenario = internal_core.get_EcotracerScenarios(
            internal_core.ActiveEcotracerScenarioIndex
        )

        assert internal_core.nEcotracerScenarios == n_scenarios_before + 1
        assert active_scenario.Name == "name"
        assert active_scenario.Author == "author"
        assert active_scenario.Contact == "contact"

        if active_scenario.Description == "":
            msg = "Ecotracer empty description bug is still present in EwE software. "
            msg += "Skipping description test assertion"
            warn(msg)
        else:
            assert active_scenario.Description == "description"

        core.close_model()


    def test_ecotracer_remove_scenarios(self, model_path, ewe_module):

        core = CoreInterface()
        core.load_model(model_path)
        # Keep reference to internal core to test state directly
        internal_core = core.get_core()

        # Load ecosim scenario before ecotracer
        core.Ecosim.load_scenario("default_test")

        n_scenarios_before = internal_core.nEcotracerScenarios
        is_loaded = core.Ecotracer.load_scenario("remove_test")
        if not is_loaded:
            raise RuntimeError("Unable to load test scenario remove_test.")
        else:
            # Close scenario before trying to delete.
            core.Ecotracer.close_scenario()

        core.Ecotracer.remove_scenario("remove_test")
        with pytest.raises(LookupError) as excinfo:
            # Trying to load scenario that doesn't exist should fail.
            core.Ecotracer.load_scenario("remove_test")

        assert internal_core.nEcotracerScenarios == n_scenarios_before - 1
        assert str(excinfo.value) == "Unable to find scenario named: remove_test"

        core.close_model()

class TestCoreProperties:

    def test_get_functional_group_names(self, model_path, ewe_module):

        core = CoreInterface()
        core.load_model(model_path)

        expected_names = [
            "Large pelagics",
            "Large demersal",
            "Merlangius",
            "Mullus and Spicara",
            "Small pelagics",
            "Belone and Scomber",
            "Zoobenthos",
            "Mesozooplankton",
            "Ciliates",
            "Chaetognaths",
            "Jellies",
            "Appendicularians",
            "Noctituca",
            "Bacteria",
            "Phytoplankton",
            "Detritus",
        ]

        fg_names = core.get_functional_group_names()

        assert all(
            [expected == output for (expected, output) in zip(expected_names, fg_names)]
        )

        core.close_model()

class TestEcosimProperties:

    def test_ecosim_get_property_exceptions(self, model_path, ewe_module):
        """
        Test that accessing Ecosim properties raises an error
        if no Ecosim scenario is loaded.
        """
        core = CoreInterface()
        core.load_model(model_path)

        expected_error_msg = "No Ecosim scenario loaded.*"

        # Test Group Parameters
        group_params = EcosimStateManager._GROUP_PARAM_NAMES.keys()
        for param_name in group_params:
            getter_method_name = f"get_{param_name}"
            with pytest.raises(EcosimNoScenarioError, match=expected_error_msg):
                getattr(core.Ecosim, getter_method_name)()

            setter_method_name = f"set_{param_name}"
            dummy_data = [0.0] * (N_GROUPS - N_DETRITUS)
            with pytest.raises(EcosimNoScenarioError, match=expected_error_msg):
                 getattr(core.Ecosim, setter_method_name)(dummy_data)


        # Test Environment Parameters
        env_params = EcosimStateManager._ENV_PARAM_NAMES.keys()
        for param_name in env_params:
            getter_method_name = f"get_{param_name}"
            with pytest.raises(EcosimNoScenarioError, match=expected_error_msg):
                getattr(core.Ecosim, getter_method_name)()

            setter_method_name = f"set_{param_name}"
            dummy_data = 0.0
            with pytest.raises(EcosimNoScenarioError, match=expected_error_msg):
                 getattr(core.Ecosim, setter_method_name)(dummy_data)


        core.close_model()

    def test_ecosim_getters(self, model_path, ewe_module):
        """
        Test the Ecosim property getters after loading a scenario.
        """
        core = CoreInterface()
        core.load_model(model_path)

        # Expected values in ecosim scenario
        expected_0_1 = [i / 100 for i in range(1, N_GROUPS + 1)]
        expected_1_2 = [v + 1 for v in expected_0_1]

        # producer and detritus values are not used and the getter will return default
        expected_0_1[-2:] = [1.0] * 2
        expected_1_2[-2:] = [1.0] * 2

        core.Ecosim.load_scenario("property_get_test")

        # --- Test Group Parameters ---
        retrieved = core.Ecosim.get_density_dep_catchability()
        assert len(retrieved) == N_GROUPS
        assert all(
            isclose(exp, out, rel_tol=1e-7)
            for exp, out in zip(expected_1_2, retrieved)
        )

        expected_0_1[-2:] = [0.5] * 2
        retrieved = core.Ecosim.get_feeding_time_adj_rate()
        assert len(retrieved) == N_GROUPS
        assert all(
            isclose(exp, out, rel_tol=1e-7)
            for exp, out in zip(expected_0_1, retrieved)
        )

        retrieved = core.Ecosim.get_max_rel_feeding_time()
        assert len(retrieved) == N_GROUPS
        assert all(
            isclose(exp, out, rel_tol=1e-7)
            for exp, out in zip(expected_1_2, retrieved)
        )

        retrieved = core.Ecosim.get_max_rel_pb()
        expected_max_rel_pb = [2.0] * N_GROUPS
        assert len(retrieved) == N_GROUPS
        assert all(
            isclose(exp, out, rel_tol=1e-7)
            for exp, out in zip(expected_max_rel_pb, retrieved)
        )

        # update the expected defaults
        expected_0_1[-2:] = [0.0] * 2
        retrieved = core.Ecosim.get_pred_effect_feeding_time()
        assert len(retrieved) == N_GROUPS
        assert all(
            isclose(exp, out, rel_tol=1e-7)
            for exp, out in zip(expected_0_1, retrieved)
        )

        expected_0_1[-2:] = [1.0] * 2
        retrieved = core.Ecosim.get_other_mort_feeding_time()
        assert len(retrieved) == N_GROUPS
        assert all(
            isclose(exp, out, rel_tol=1e-7)
            for exp, out in zip(expected_0_1, retrieved)
        )

        expected_1_2[-2:] = [1000.0] * 2
        retrieved = core.Ecosim.get_qbmax_qbio()
        assert len(retrieved) == N_GROUPS
        assert all(
            isclose(exp, out, rel_tol=1e-7)
            for exp, out in zip(expected_1_2, retrieved)
        )

        expected_1_2[-2:] = [0.0] * 2
        retrieved = core.Ecosim.get_switching_power()
        assert len(retrieved) == N_GROUPS
        assert all(
            isclose(exp, out, rel_tol=1e-7)
            for exp, out in zip(expected_1_2, retrieved)
        )


        # Test Environment Parameters
        expected_nyears = 42
        retrieved = core.Ecosim.get_n_years()
        assert retrieved == expected_nyears

        core.close_model()

    def test_ecosim_setters(self, model_path, ewe_module):

        """Test the Ecosim property setters."""
        core = CoreInterface()
        core.load_model(model_path)

        core.Ecosim.load_scenario("property_set_test")

        to_set_0_1 = [i / 100 for i in range(1, N_CONSUMERS + 1)]
        to_set_1_2 = [v + 1 for v in to_set_0_1]

        set_idx = [i for i in range(1, N_CONSUMERS + 1)]

        between_0_1 = [
            "feeding_time_adj_rate", "other_mort_feeding_time", "pred_effect_feeding_time"
        ]

        # Test Group Parameters
        group_params = EcosimStateManager._GROUP_PARAM_NAMES.keys()
        for param_name in group_params:
            if param_name == "max_rel_pb":
                # max rel pb applies only to produces, test separately.
                continue

            setter_method_name = f"set_{param_name}"
            getter_method_name = f"get_{param_name}"

            to_set = to_set_0_1 if param_name in between_0_1 else to_set_1_2

            getattr(core.Ecosim, setter_method_name)(to_set, set_idx)
            retrieved = getattr(core.Ecosim, getter_method_name)()

            assert all(
                isclose(exp, ret, rel_tol=1e-7)
                for exp, ret in zip(to_set, retrieved[:-2])
            )

        # test max rel pb
        core.Ecosim.set_max_rel_pb([1.5], [15])
        retrieved = core.Ecosim.get_max_rel_pb()[14]
        assert isclose(retrieved, retrieved, rel_tol=1e-7)

        # --- Test Environment Parameters ---
        env_params = EcosimStateManager._ENV_PARAM_NAMES.keys()
        for param_name in env_params:
            setter_method_name = f"set_{param_name}"
            getter_method_name = f"get_{param_name}"

            if param_name == "n_years":
                to_set = randint(1, 200)
            else:
                to_set = random() * 10

            getattr(core.Ecosim, setter_method_name)(to_set)
            retrieved = getattr(core.Ecosim, getter_method_name)()

            if isinstance(to_set, int):
                assert retrieved == to_set
            else:
                assert isclose(to_set, retrieved, rel_tol=1e-7)

        core.close_model()

class TestEcotracerProperties:

    def test_ecotracer_get_property_exceptions(self, model_path, ewe_module):

        core = CoreInterface()
        core.load_model(model_path)
        # Keep reference to internal core to test state directly
        internal_core = core.get_core()

        core.Ecosim.load_scenario("default_test")

        expected_error_msg = "No Ecotracer scenario loaded. .*"
        with pytest.raises(EcotracerNoScenarioError, match=expected_error_msg):
            core.Ecotracer.get_initial_concentrations()

        with pytest.raises(EcotracerNoScenarioError, match=expected_error_msg):
            core.Ecotracer.get_immigration_concentrations()

        with pytest.raises(EcotracerNoScenarioError, match=expected_error_msg):
            core.Ecotracer.get_direct_absorption_rates()

        with pytest.raises(EcotracerNoScenarioError, match=expected_error_msg):
            core.Ecotracer.get_physical_decay_rates()

        with pytest.raises(EcotracerNoScenarioError, match=expected_error_msg):
            core.Ecotracer.get_excretion_rates()

        with pytest.raises(EcotracerNoScenarioError, match=expected_error_msg):
            core.Ecotracer.get_metabolic_decay_rates()

    def test_ecotracer_getters(self, model_path, ewe_module):

        core = CoreInterface()
        core.load_model(model_path)

        core.Ecosim.load_scenario("default_test")
        core.Ecotracer.load_scenario("property_test")

        expected_property = [
            i / 10 for i in range(1, 16) # 0.1, 0.2...
        ]

        retrieved = core.Ecotracer.get_initial_concentrations()
        assert all([
            isclose(expected, out, rel_tol=1e-7)
            for (expected, out) in zip(expected_property, retrieved)
        ])

        retrieved = core.Ecotracer.get_immigration_concentrations()
        assert all([
            isclose(expected, out, rel_tol=1e-7)
            for (expected, out) in zip(expected_property, retrieved)
        ])

        expected_property = [
            i / 100 for i in range(1, 16) # 0.01, 0.02...
        ]

        retrieved = core.Ecotracer.get_direct_absorption_rates()
        assert all([
            isclose(expected, out, rel_tol=1e-7)
            for (expected, out) in zip(expected_property, retrieved)
        ])

        retrieved = core.Ecotracer.get_physical_decay_rates()
        assert all([
            isclose(expected, out, rel_tol=1e-7)
            for (expected, out) in zip(expected_property, retrieved)
        ])

        retrieved = core.Ecotracer.get_excretion_rates()
        assert all([
            isclose(expected, out, rel_tol=1e-7)
            for (expected, out) in zip(expected_property, retrieved)
        ])

        retrieved = core.Ecotracer.get_metabolic_decay_rates()
        assert all([
            isclose(expected, out, rel_tol=1e-7)
            for (expected, out) in zip(expected_property, retrieved)
        ])

        core.close_model()

    def test_ecotracer_setters(self, model_path, ewe_module):

        core = CoreInterface()
        core.load_model(model_path)

        core.Ecosim.load_scenario("default_test")
        core.Ecotracer.load_scenario("property_set_test")

        to_set = [random() / 10 for i in range(16)]
        core.Ecotracer.set_initial_concentrations(to_set)
        retrieved = core.Ecotracer.get_initial_concentrations()
        assert all([isclose(exp, ret, rel_tol=1e-7) for (exp, ret) in zip(to_set, retrieved)])

        to_set = [random() / 10 for i in range(16)]
        core.Ecotracer.set_immigration_concentrations(to_set)
        retrieved = core.Ecotracer.get_immigration_concentrations()
        assert all([isclose(exp, ret, rel_tol=1e-7) for (exp, ret) in zip(to_set, retrieved)])

        to_set = [random() / 10 for i in range(16)]
        core.Ecotracer.set_direct_absorption_rates(to_set)
        retrieved = core.Ecotracer.get_direct_absorption_rates()
        assert all([isclose(exp, ret, rel_tol=1e-7) for (exp, ret) in zip(to_set, retrieved)])

        to_set = [random() / 10 for i in range(16)]
        core.Ecotracer.set_physical_decay_rates(to_set)
        retrieved = core.Ecotracer.get_physical_decay_rates()
        assert all([isclose(exp, ret, rel_tol=1e-7) for (exp, ret) in zip(to_set, retrieved)])

        to_set = [random() / 10 for i in range(16)]
        core.Ecotracer.set_excretion_rates(to_set)
        retrieved = core.Ecotracer.get_excretion_rates()
        assert all([isclose(exp, ret, rel_tol=1e-7) for (exp, ret) in zip(to_set, retrieved)])

        to_set = [random() / 10 for i in range(16)]
        core.Ecotracer.set_metabolic_decay_rates(to_set)
        retrieved = core.Ecotracer.get_metabolic_decay_rates()
        assert all([isclose(exp, ret, rel_tol=1e-7) for (exp, ret) in zip(to_set, retrieved)])
