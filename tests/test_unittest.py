import unittest
from pathlib import Path

from decom_py import CoreInterface
from decom_py.EwEModule import initialise

class TestUnitTest(unittest.TestCase):

    def test_load_scen(self):
        ecopath_app_path = Path(r'c:\Program Files\Ecopath with Ecosim 40 years 6.7.0.18865_64-bit')

        model_path = Path(__file__).parent.parent/'test'/'resources'/'BlackSea.EwEaccdb'
        self.assertTrue(model_path.is_file())

        initialise(str(ecopath_app_path))

        core = CoreInterface()
        core.load_model(str(model_path))
        # Keep reference to internal core to test state directly
        internal_core = core.get_core()

        # core.Ecosim.load_scenario(1)
        # self.assertEqual(internal_core.ActiveEcosimScenarioIndex, 1)

        core.Ecosim.load_scenario("default_test")

        print(internal_core.ActiveEcosimScenarioIndex)
        current_scen_name = internal_core.get_EcosimScenarios(
            internal_core.ActiveEcosimScenarioIndex
        ).Name
        self.assertEqual(current_scen_name, "default_test")

        # save index to test loading with index
        scenario_index: int = internal_core.ActiveEcosimScenarioIndex

        core.Ecosim.close_scenario()
        self.assertFalse(internal_core.get_StateMonitor().HasEcosimLoaded())

        core.Ecosim.load_scenario(scenario_index)
        scen_name = internal_core.get_EcosimScenarios(
            internal_core.ActiveEcosimScenarioIndex
        ).Name
        self.assertEqual(scen_name, "default_test")

        core.close_model()

if __name__ == '__main__':
    unittest.main()
