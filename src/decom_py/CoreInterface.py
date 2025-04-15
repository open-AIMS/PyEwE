import os
from warnings import warn
from pathlib import Path
from typing import Iterable, Union, Union

from warnings import warn
from .EwEState import EwEState
from .Results import XarrayCSV
from .EwEModule import get_ewe_core_module, result_type_enum_array, py_bool_to_ewe_tristate


class CoreInterface():
    """Interface to update the state of the underlying EwECore.

    CoreInterface provides a thin wrapper over the original cCore object defined in the EwE
    binaries. It should provide convenience functions to carry out operations already
    defined in the cCore object. Larger scale manipulations should not occur in this class.

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

    def get_state(self):
        return self._state

    def get_functional_group_names(self) -> list[str]:
        """Get the name of all functional groups in the EwE model."""
        n_groups: int = self._core.nGroups
        fg_names: list[str] = [""] * n_groups
        for i in range(1, n_groups + 1):
            fg_names[i - 1] = self._core.get_EcopathGroupInputs(i).Name
            print(fg_names[i - 1])

        return fg_names

    def load_model(self, path: str) -> bool:
        """"Load model from a EwE database file into the EwE core."""
        return self._core.LoadModel(path)

    def _load_named_ecosim_scenario(self, name: str) -> bool:
        """Load an ecosim scenario with the given name."""
        for index in range(1, self._core.nEcosimScenarios + 1):
            if self._core.get_EcosimScenarios(index).Name == name:
                return self._core.LoadEcosimScenario(index)

        raise LookupError(f"Unable to find scenario named: {name}")

    def _load_indexed_ecosim_scenario(self, index: int) -> bool:
        """Load an ecosim scenario for the given one-based index."""
        n_ecosim_scens: int = self._core.nEcosimScenarios
        if index > n_ecosim_scens or index < 1:
            msg = "Given index, {}".format(index)
            msg += " but there are {} scenarios".format(n_ecosim_scens)
            raise IndexError(msg)

        return self._core.LoadEcosimScenario(index)

    def load_ecosim_scenario(self, identifier: Union[str, int]):
        """Load an ecosim scenario into the core object.

        Args:
            identifier (Union[str, int]): Index or name of already existing ecosim scenario

        Returns:
            bool: success or failure

        Raises:
            IndexError: The provided idx was out of bounds.
        """
        if isinstance(identifier, str):
            return self._load_named_ecosim_scenario(identifier)
        elif isinstance(identifier, int):
            return self._load_indexed_ecosim_scenario(identifier)
        else:
            raise TypeError(f"Unsupported type: {type(identifier)}")

        return False

    def load_ecotracer_scenario(self, idx: int) -> bool:
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

        success = self._core.LoadEcotracerScenario(idx)
        if not success:
            print("Loading Ecotracer failed.")

        return success

    def new_ecosim_scenario(
            self,
            name: str,
            description: str,
            author: str,
            contact: str
    ) -> bool:
        return self._core.NewEcosimScenario(name, description, author, contact)

    def _remove_named_ecosim_scenario(self, name: str) -> bool:
        """Remove a ecosim scenario with the given a name."""

        for index in range(1, self._core.nEcosimScenarios + 1):
            if self._core.get_EcosimScenarios(index).Name == name:
                return self._core.RemoveEcosimScenario(index)

        raise LookupError(f"Unable to find scenario named {name}.")

    def _remove_indexed_ecosim_scenario(self, index: int) -> bool:
        """Remove ecosim scenario given a one-based index."""

        n_ecosim_scens: int = self._core.nEcotracerScenarios
        if index > n_ecosim_scens:
            msg = "Given index, {}".format(index)
            msg += " but there are {} scenarios".format(n_ecosim_scens)
            raise IndexError(msg)

        if index == self._core.ActiveEcosimScenarioIndex:
            warn("Removing active ecosim scenario.")

        return self._core.RemoveEcosimScenario(index)

    def remove_ecosim_scenario(self, identifier: Union[str, int]) -> bool:
        """Remove scenario from core."""
        if isinstance(identifier, str):
            self._remove_named_ecosim_scenario(identifier)
        elif isinstance(identifier, int):
            self._remove_indexed_ecosim_scenario(identifier)
        else:
            raise TypeError(f"Unsupported type: {type(identifier)}")

        return False

    def new_ecotracer_scenario(
            self,
            name: str,
            description: str,
            author: str,
            contact: str
    ) -> bool:
        """Add new ecotracer scenario."""
        return self._core.NewEcotracerScenario(name, description, author, contact)

    def _remove_named_ecotracer_scenario(self, name: str) -> bool:
        """Remove ecotracer scenario with the given name."""

        for index in range(1, self._core.nEcosimScenarios + 1):
            if self._core.get_EcotracerScenarios(index).Name == name:
                return self._core.RemoveEcotracerScenario(index)

        raise LookupError(f"Unable to find scenario named {name}.")

    def _remove_indexed_ecotracer_scenario(self, index: int) -> bool:
        """Remove a ecotracer scenario given a one based index."""

        n_ecotracer_scens: int = self._core.nEcotracerScenarios
        if index > n_ecotracer_scens:
            msg = "Given index, {}".format(index)
            msg += " but there are {} scenarios".format(n_ecotracer_scens)
            raise IndexError(msg)

        if index == self._core.ActiveEcosimScenarioIndex:
            warn("Removing active ecotracer scenario.")

        return self._core.RemoveEcotracerScenario(index)

    def remove_ecotracer_scenario(self, identifier: Union[str, int]) -> bool:
        """Remove scenario from core."""
        if isinstance(identifier, str):
            self._remove_named_ecotracer_scenario(identifier)
        elif isinstance(identifier, int):
            self._remove_indexed_ecotracer_scenario(identifier)
        else:
            raise TypeError(f"Unsupported type: {type(identifier)}")

        return False

    def close_ecosim_scenario(self):
        self._core.CloseEcosimScenario()

    def close_ecotracer_scenario(self):
        self._core.CloseEcotracerScenario()

    def run_ecopath(self):
        """Run the ecopath model and return whether it was successful"""
        is_balanced: bool = self._core.IsModelBalanced
        if not is_balanced:
            warn("Ecopath model is not balanced.")

        results = self._core.RunEcopath()

        return results

    def run_ecosim_wo_ecotracer(self) -> bool:
        """Run the ecosim model without ecotracer and return whether it was successful"""

        self._core.EcosimModelParameters.ContaminantTracing = False
        self.run_ecopath()
        successful: bool = self._core.RunEcosim()

        return successful

    def run_ecosim_w_ecotracer(self) -> bool:
        """Run the ecosim model with ecotracer and return whether it was successful"""

        if not self._state.HasEcotracerLoaded():
            raise Exception("Ecotracer scenario is not loaded.")

        self.run_ecopath()
        self._core.EcosimModelParameters.ContaminantTracing = True
        successful: bool = self._core.RunEcosim()

        if not successful:
            print("EcoSim with Ecotracer run failed.")

        return successful

    def save_ecopath_results(self):
        # Missing use monthly enum type to pass to write results.
        return self._ecopath_result_writer.WriteResults()

    def save_ecosim_results(
            self,
            dir: str,
            result_types: Iterable[str],
            monthly: bool=True,
            quiet: bool=True
    ) -> bool:
        """Save ecosim results for a given setup of result variables.

        Args:
            dir (str): Directory to save csv files to.
            result_types (str): Names of variables to save.
            monthly (bool): flag to save monthly or yearly values.
            quiet (bool): flag to print information.

        Returns:
            bool: True if successful
        """
        if not os.path.isdir(dir):
            raise FileNotFoundError(dir)

        res_type = result_type_enum_array(result_types)
        monthly_flag = py_bool_to_ewe_tristate(monthly)
        is_success = self._ecosim_result_writer.WriteResults(
            dir, res_type, monthly_flag, quiet
        )

        return is_success

    def save_all_ecosim_results(self, dir: str):
        """Save all ecosim result variables to the given directory."""
        # Missing use monthly enum type to pass to write results.
        self._core.m_EcoSimData
        if not self._ecosim_result_writer.WriteResults(dir):
            warn("Failed to save ecosim results. Make sure target directory is empty.")
            return False

        return True

    def save_ecotracer_results(self, filepath: str) -> None:
        """Save ecotracer results to a given file

        Args:
            filepath (str): Path to save file

        Returns:
            successful save
        """

        file_stream = self._ecotracer_result_writer.OpenWriter(filepath)
        if file_stream is None:
            msg = "Unable to open new file at {}".format(filepath)
            msg += " Check that directory exists and there is no pre-existing file."
            raise RuntimeError(msg)

        # EwE writes directly to the file and does not construct intermediate arrays
        self._ecotracer_result_writer.WriteHeader(file_stream, False)
        self._ecotracer_result_writer.WriteBody(file_stream)
        self._ecotracer_result_writer.CloseWriter(file_stream, filepath)

        return None

    def set_default_save_dir(self, save_dir: str):
        """Set the default save directory in underlying core object."""
        self._core.OutputPath = save_dir
        self.results = XarrayCSV(save_dir)

    def close_model(self):
        return self._core.CloseModel()

    def print_summary(self):
        """Print summary on the state of the EwE core."""
        return self._state.print_summary()
