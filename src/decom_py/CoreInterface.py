import os
from warnings import warn
from pathlib import Path
from typing import Iterable, Union, Union

from warnings import warn
from .EwEState import EwEState
from .Results import XarrayCSV
from .EwEModule import (
    get_ewe_core_module,
    result_type_enum_array,
    py_bool_to_ewe_tristate,
)
from .EwEModels import EcosimStateManager, EcotracerStateManager


class CoreInterface:
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

        Ecosim (EcosimStateManager): object that manages scenario loading, model runs and results for Ecosim
        Ecotracer (EcotracerStateManager): object that manages scenario loading, model runs and results for Ecotracer
    """

    def __init__(self):
        core_module = get_ewe_core_module()

        self._core = core_module.cCore()
        self._ecopath_result_writer = core_module.cEcopathResultWriter(self._core)
        self._ecosim_result_writer = core_module.Ecosim.cEcosimResultWriter(self._core)
        self._ecotracer_result_writer = core_module.cEcotracerResultWriter(self._core)
        self._state = EwEState(self._core)

        self.Ecosim = EcosimStateManager(self._core, self._state)
        self.Ecotracer = EcotracerStateManager(self._core, self._state)

    def get_core(self):
        return self._core

    def get_state(self):
        return self._state

    def load_model(self, path: str):
        """Load model from a EwE access database file into the EwE core."""
        return self._core.LoadModel(path)

    def get_functional_group_names(self):
        """Get the name of all functional groups in the EwE model."""
        n_groups: int = self._core.nGroups
        fg_names: list[str] = [""] * n_groups
        for i in range(1, n_groups + 1):
            fg_names[i - 1] = self._core.get_EcopathGroupInputs(i).Name

        return fg_names

    def get_first_year(self):
        """Get the first year for which ecosim is run."""
        return self._core.get_EcosimFirstYear()

    def n_groups(self) -> int:
        """Get the number of functional groups in the loaded model."""
        return self._core.nGroups

    def n_detritus_groups(self) -> int:
        """Get the number of detritus groups in the loaded model."""
        return self._core.nDetritusGroups

    def n_living_groups(self) -> int:
        """Get the number of living groups in the loaded models."""
        return self._core.nLivingGroups

    def n_producers(self) -> int:
        """Get the number of producers in the loaded model"""
        return sum(
            [
                self._core.get_EcopathGroupInputs(i).IsProducer
                for i in range(1, self.n_groups() + 1)
            ]
        )

    def n_consumers(self) -> int:
        """Get the number of consumers in the loaded model."""
        return sum(
            [
                self._core.get_EcopathGroupInputs(i).IsConsumer
                for i in range(1, self.n_groups() + 1)
            ]
        )

    def save_ecopath_results(self):
        # Missing use monthly enum type to pass to write results.
        return self._ecopath_result_writer.WriteResults()

    def save_ecosim_results(
        self,
        dir: str,
        result_types: Iterable[str],
        monthly: bool = True,
        quiet: bool = True,
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
