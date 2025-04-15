import pytest
from decom_py import CoreInterface

class TestScenarioAddRemove:

    def test_load_scenario(self, model_path, ewe_module):

        core = CoreInterface()
        core.load_model(model_path)
        # Keep reference to internal core to test state directly
        internal_core = core.get_core()

        core.load_ecosim_scenario("default_test")

        print(internal_core.ActiveEcosimScenarioIndex)
        assert internal_core.get_EcosimScenarios(
            internal_core.ActiveEcosimScenarioIndex
        ).Name == "default_test"

        # save index to test loading with index
        scenario_index: int = internal_core.ActiveEcosimScenarioIndex

        core.close_ecosim_scenario()
        assert (not core._state.HasEcotracerLoaded())

        core.load_ecosim_scenario(scenario_index)
        assert internal_core.get_EcosimScenarios(
            internal_core.ActiveEcosimScenarioIndex
        ).Name == "default_test"

    def test_ecosim_add_scenarios(self, model_path, ewe_module):

        core = CoreInterface()
        core.load_model(model_path)
        # Keep reference to internal core to test state directly
        internal_core = core.get_core()

        # record number of scenario before addition
        n_scenarios_before = core._core.nEcosimScenarios
        core.new_ecosim_scenario("name", "description", "author", "contact")

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
        is_loaded = core.load_ecosim_scenario("remove_test")
        if not is_loaded:
            raise RuntimeError("Unable to load test scenario remove_test.")
        else:
            core.close_ecosim_scenario()

        core.remove_ecosim_scenario("remove_test")
        with pytest.raises(LookupError) as excinfo:
            core.load_ecosim_scenario("remove_test")

        assert internal_core.nEcosimScenarios == n_scenarios_before - 1
        assert str(excinfo.value) == "Unable to find scenario named: remove_test"

        core.close_model()
