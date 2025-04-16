from pandas import DataFrame
from pathlib import Path
from tempfile import TemporarDirectory, TemporaryDirectory
import shutil
import os

from decom_py import CoreInterface
from Exceptions import EwEError, EcotracerError, EcosimError, EcopathError

class EwEScenarioInterface:

    def __init__(self, model_path: str):

        self._model_path = model_path
        mod_path_obj = Path(model_path)
        if not mod_path_obj.exists():
            raise FileNotFoundError(model_path)

        # The temporary directory should clean itself up.
        self._temp_dir = TemporaryDirectory()
        self._temp_model_path = os.path.join(self._temp_dir.name, os.path.basename(model_path))

        # to avoid modifying the original model file, create a copy
        shutil.copy2(model_path, self._temp_model_path)

        self._core_instance = CoreInterface()
        if not self._core_instance.load_model(model_path):
            msg = "Failed to load EwE model. "
            msg += "Check that the model file is loadable via the gui."
            raise EwEError(self._core_instance.get_state(), msg)

        if not self._core_instance.new_ecosim_scenario(
            "tmp_ecosim_scen",
            "temporary ecosim scenario used by decom_py",
            "", # author
            ""  # contact
        ):
            msg = "Failed to create and load temporary ecosim scenario."
            raise EcosimError(self._core_instance.get_state(), msg)

        if not self._core_instance.new_ecotracer_scenario(
            "tmp_ecotracer_scen",
            "temporary ecosim scenario used by decom_py",
            "", # author
            ""  # contact
        ):
            msg = "Failed to create and load temporary ecotracer scenario."
            raise EcotracerError(self._core_instance.get_state(), msg)

    def get_temp_model_path(self):
        return self._temp_model_path

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
