import pytest
from warnings import warn
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
