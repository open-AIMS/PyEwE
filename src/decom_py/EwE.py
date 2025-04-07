import clr
import sys
import os
from pathlib import Path
from warnings import warn
from importlib import import_module

class EwE:

    def __init__(self, ewe_dir: str, result_save_dir: str):

        self._ewe_dir = Path(ewe_dir)
        if not self._ewe_dir.exists():
            raise FileNotFoundError(self._ewe_dir)

        self._ewe_core_path = self._ewe_dir.joinpath('EwECore.dll')
        if not self._ewe_core_path.exists():
            raise FileNotFoundError(self._ewe_core_path)

        clr.AddReference(str(self._ewe_core_path))

        self._ewe_core = import_module('EwECore')
        self._core = self._ewe_core.cCore()
        self._ecopath_result_writer = self._ewe_core.cEcopathResultWriter(self._core)
        self._ecosim_result_writer = self._ewe_core.Ecosim.cEcosimResultWriter(self._core)
        self._core.OutputPath = result_save_dir

    def load_model(self, path: str):
        return self._core.LoadModel(path)

    def load_ecosim_scenario(self, idx: int):
        n_ecosim_scens: int = self._core.nEcosimScenarios
        if idx > n_ecosim_scens or idx < 1:
            msg = "Given index, {}".format(idx)
            msg += " but there are {} scenarios".format(n_ecosim_scens)
            raise IndexError(msg)

        return self._core.LoadEcosimScenario(idx)

    def load_ecotracer_scenario(self, idx: int):
        n_ecotracer_scens: int = self._core.nEcotracerScenarios
        if idx > n_ecotracer_scens or idx < 1:
            msg = "Given index, {}".format(idx)
            msg += " but there are {} scenarios".format(n_ecotracer_scens)
            raise IndexError(msg)

        return self._core.LoadEcotracerScenario(idx)

    def core(self):
        return self._core

    def run_ecopath(self):
        is_balanced: bool = self._core.IsModelBalanced
        if not is_balanced:
            warn("Ecopath model is not balanced.")

        results = self._core.RunEcopath()

        return results

    def run_ecosim(self):
    
        self.run_ecopath()
        successful: bool = self._core.RunEcosim()

        return successful

    def save_ecopath_results(self):
        # Missing use monthly enum type to pass to write results.
        return self._ecopath_result_writer.WriteResults()

    def save_ecosim_results(self, dir: str):
        # Missing use monthly enum type to pass to write results.
        return self._ecosim_result_writer.WriteResults(dir)
