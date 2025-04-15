from pandas import DataFrame

from decom_py import CoreInterface
from pathlib import Path

from Exceptions import EwEError

class EwEScenarioInterface:

    def __init__(self, model_path: str):

        if not Path(model_path).exists():
            raise FileNotFoundError(model_path)

        self._core_instance = CoreInterface()
        if not self._core_instance.load_model(model_path):
            msg = "Failed to load EwE model. "
            msg += "Check that the model file is loadable via the gui."
            raise EwEError(self._core_instance.get_state(), msg)

    def run_scenarios(self, scenarios: DataFrame):
        return None

    def set_vulnerabilities(self, vulnerabilities):
        return None

    def set_fishing_effort(self, fishing_effort):
        return None

    def get_all_parameter_names(self):
        return None

    def get_empty_scenarios_df(self, n_scenarios: int=1):
        return None
