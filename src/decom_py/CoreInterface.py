import os
from pathlib import Path

from .EwEState import EwEState
from .EwEModule import get_ewe_core_module

class CoreInterface:
    """Interface to update the state of the underlying EwECore.

    Attributes:
        _core (cCore): Visual Basic cCore object describing the state of the program.
        _ecopath_result_writer (cEcopathResultWriter): Object the handles writing ecopath results
        _ecosim_result_writer (cEcosimResultWriter): Object the handles writing ecosim results
        _ecotracer_result_writer (cEcotracerResultWriter): Object the handles writing ecotracer results
        _state (cStateMonitor): Object handling high level state information bout _core
    """

    def __init__(self):
        
        core_module = get_ewe_core_module()

        self._core = core_module.cCore()
        self._ecopath_result_writer = core_module.cEcopathResultWriter(self._core)
        self._ecosim_result_writer = core_module.Ecosim.cEcosimResultWriter(self._core)
        self._ecotracer_result_writer = core_module.cEcotracerResultWriter(self._core)
        self._state = EwEState(self._core)

    def get_core(self):
        return self._core

    def load_model(self, path: str):
        return self._core.LoadModel(path)

    def load_ecosim_scenario(self, idx: int):
        """Load an ecosim scenario into the core object.
        
        Args:
            idx (int): Index of already existing ecosim scenario

        Returns:
            bool: success or failure

        Raises: 
            IndexError: The provided idx was out of bounds.
        """
        n_ecosim_scens: int = self._core.nEcosimScenarios
        if idx > n_ecosim_scens or idx < 1:
            msg = "Given index, {}".format(idx)
            msg += " but there are {} scenarios".format(n_ecosim_scens)
            raise IndexError(msg)

        return self._core.LoadEcosimScenario(idx)

    def load_ecotracer_scenario(self, idx: int):
        """Load an ecotracer scenario into the core object.
        
        Args:
            idx (int): Index of already existing ecotracer scenario

        Returns:
            bool: success or failure

        Raises: 
            IndexError: The provided idx was out of bounds.
        """
        n_ecotracer_scens: int = self._core.nEcotracerScenarios
        if idx > n_ecotracer_scens or idx < 1:
            msg = "Given index, {}".format(idx)
            msg += " but there are {} scenarios".format(n_ecotracer_scens)
            raise IndexError(msg)

        return self._core.LoadEcotracerScenario(idx)

    def run_ecopath(self):
        """Run the ecopath model and return whether it was successful"""
        is_balanced: bool = self._core.IsModelBalanced
        if not is_balanced:
            warn("Ecopath model is not balanced.")

        results = self._core.RunEcopath()

        return results

    def run_ecosim_wo_ecotracer(self) -> bool:
        """Run the ecosim model without ecotracer and return whether it was successful"""

        self._core.EcotracerModelParameters.ContaminantTracing = False
        self.run_ecopath()
        successful: bool = self._core.RunEcosim()

        return successful

    def run_ecosim_w_ecotracer(self) -> bool:
        """Run the ecosim model with ecotracer and return whether it was successful"""

        if not self._state.HasEcotracerLoaded():
            raise Exception("Ecotracer scenario is not loaded.")

        self._core.EcotracerModelParameters.ContaminantTracing = True
        self.run_ecopath()
        successful: bool = self._core.RunEcosim()

        return successful

    def save_ecopath_results(self):
        # Missing use monthly enum type to pass to write results.
        return self._ecopath_result_writer.WriteResults()

    def save_ecosim_results(self, dir: str):
        # Missing use monthly enum type to pass to write results.
        if not self._ecosim_result_writer.WriteResults(dir):
            warn("Failed to save ecosim results. Make sure target directory is empty.")
            return False

        return True

    def save_ecotracer_results(self):
        return self._ecotracer_result_writer.WriteEcosimResults()

    def set_default_save_dir(self, save_dir: str):
        """Set the default save directory in underlying core object."""
        self._core.OutputPath = save_dir

    def close_model(self):
        return self._core.CloseModel()
