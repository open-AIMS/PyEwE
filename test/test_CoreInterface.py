import pytest
from random import random
from warnings import warn
from math import isclose

from decom_py import CoreInterface
from decom_py.Exceptions import EwEError, EcopathError, EcosimError, EcotracerError

class TestScenarioAddRemove:

    def test_ecosim_load_scenario(self, model_path, ewe_module):

        core = CoreInterface()
        core.load_model(model_path)
        # Keep reference to internal core to test state directly
        internal_core = core.get_core()

        core.Ecosim.load_scenario("default_test")

        print(internal_core.ActiveEcosimScenarioIndex)
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

        print(internal_core.ActiveEcotracerScenarioIndex)
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
        print(fg_names)

        assert all(
            [expected == output for (expected, output) in zip(expected_names, fg_names)]
        )

        core.close_model()

    def test_get_property_exceptions(self, model_path, ewe_module):

        core = CoreInterface()
        core.load_model(model_path)
        # Keep reference to internal core to test state directly
        internal_core = core.get_core()

        core.Ecosim.load_scenario("default_test")

        expected_error_msg = "No Ecotracer scenario loaded. .*"
        with pytest.raises(EcotracerError, match=expected_error_msg):
            core.Ecotracer.get_initial_concentrations()

        core.Ecotracer.load_scenario("property_test")


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
