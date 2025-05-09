"""
Define the worker initialisation function and run scenario function for multiprocess
execution. This is required because the underling core object must be initialised by a
process as it is not 'picklable'.

Parameters passed to workers are assumed to be have been created a the top-level scenario
interface.
"""

import os
import shutil
import atexit
from typing import Optional
from pandas import DataFrame

from .core.module import initialise, get_ewe_bin_path
from .parameter_management import ParameterManager
from .core.interface import CoreInterface
from .results.manager import ResultManager

# globals to be reused between scenarios by the worker.
worker_core: Optional[CoreInterface] = None
worker_param_manager: Optional[ParameterManager] = None
worker_result_manager: Optional[ResultManager] = None
worker_model_path: Optional[str] = None


def worker_init(
    source_model_path: str,
    param_manager: ParameterManager,
    mp_buffers: dict,
    var_names: list[str],
    scenarios: DataFrame,
):
    """Initialise a worker, constructors the required globals.

    All variables passed to the initialiser are assumed to be constructed by the
    EwEScenarioInterface object. Its assumed the scenario interface has saved constant
    parameters to the 'tmp_ecosim_scenario' in the model database before this worker copies
    the database.

    Arguments:
        source_model_path (str): Path to the temporary model database created by the
            scenario interface.
        param_manager (ParameterManager): ParameterManager used to set parameters between
            scenarios.
        mp_buffers (dict): Dictionary of multiprocess array buffers to write results to.
        var_names (list[str]): List of result names to save.
        scenarios (DataFrame): Data frame containing parameters for each scenario.
    """
    global worker_core, worker_param_manager, worker_result_manager, worker_model_path

    # Initialise the EwE core module for the worker.
    initialise(get_ewe_bin_path())

    # For debugging identification
    worker_pid = os.getpid()
    print(f"Initialising worker with pid: {worker_pid}")

    # Construct the new file name for the temporary model database.
    mod_path_struct = os.path.splitext(source_model_path)
    mod_path_stem = mod_path_struct[0]
    mod_path_ext = mod_path_struct[1]

    worker_model_path = mod_path_stem + f"_tmp_{worker_pid}" + mod_path_ext
    if worker_model_path is None:
        raise ValueError("Worker model path failed to initialise")

    shutil.copy2(source_model_path, worker_model_path)

    # Initialise a core object that is not shared between workers.
    worker_core = CoreInterface()
    worker_core.load_model(worker_model_path)

    # The scenario should have already setup constant parameters
    worker_core.Ecosim.load_scenario("tmp_ecosim_scen")
    worker_core.Ecotracer.load_scenario("tmp_ecotracer_scen")

    worker_param_manager = param_manager
    worker_result_manager = ResultManager(
        worker_core, var_names, scenarios, shared_store=mp_buffers
    )

    # In case there were constant parameters that do not get saved to the database.
    worker_param_manager.apply_constant_params(worker_core)

    # Make sure workers close and delete database files.
    atexit.register(worker_clean_up)
    return None


def worker_run_scenario(scenario_idx: int, scenario_params: list[float]) -> None:
    """Run a scenario with the worker."""
    global worker_core, worker_param_manager, worker_result_manager
    if (
        worker_core is None
        or worker_param_manager is None
        or worker_result_manager is None
    ):
        raise RuntimeError("Worker globals have not been initialised yet.")

    worker_param_manager.apply_variable_params(worker_core, scenario_params)
    worker_core.Ecotracer.run()
    worker_result_manager.collect_results(scenario_idx)

    return None


def worker_clean_up() -> None:
    """Close model and delete model file."""
    global worker_core, worker_model_path
    if worker_core is None or worker_model_path is None:
        raise RuntimeError("Worker globals have not been initialised yet.")

    worker_core.close_model()
    os.remove(worker_model_path)
