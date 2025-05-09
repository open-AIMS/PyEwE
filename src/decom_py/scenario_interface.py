from warnings import warn
from pandas import DataFrame
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Union, Dict, List, Optional
from tqdm.auto import tqdm

import numpy as np
import pandas as pd
import shutil
import os
import math
import atexit
import multiprocessing

from .core import CoreInterface
from .exceptions import EwEError, EcotracerError, EcosimError
from .results import ResultManager, ResultSet
from .parameter_management import ParameterManager
from .worker import worker_init, worker_run_scenario, worker_clean_up


def worker_run_scenario_wrapper(args):
    scen_idx, scen_params = args
    return worker_run_scenario(scen_idx, scen_params)


class EwEScenarioInterface:
    """Interface for running Ecopath with Ecosim scenarios.

    Attributes:
        _model_path (str): Path to EwE model database file.
        _temp_model_path (str): Path to temporary model database file.
        _param_manager (ParameterManager): Parameter manager object to manage variable and
            constant params.
    """

    def __init__(self, model_path: str, temp_model_path: Optional[str] = None):
        """Initialise a EwEScenarioInterface

        Given a path to the EwE model database, construct a EwEScenarioInterface object by
        copying the database to a temporar location so that the given database is not
        edited. When the interface is cleaned up or the python program exits, the object
        will close the temporary database and delete the temporary folder it was placed in.

        If the user supplies a temporary model path, then the model will copied to that
        location. Ther user is responsible for deleting the copied database when complete
        however. This is mainly for debugging purposes to check the underlying state.

        'EwEScenarioInterface.cleanup()' is registered at exit but it also good practice to
        manually call this function after completion.

        Arguments:
            model_path (str): Path to model database.
            temp_model_path (Optonal[str]): Path to where the model database should be
                copied, the user is responsible for cleaning up the copy.
        """
        self._model_path = model_path
        mod_path_obj = Path(model_path)
        if not mod_path_obj.exists():
            raise FileNotFoundError(model_path)

        self._debugged_model = not temp_model_path is None

        # The temporary directory should clean itself up
        if not self._debugged_model:
            self._temp_dir = TemporaryDirectory()
            self._temp_model_path = os.path.join(
                self._temp_dir.name, os.path.basename(model_path)
            )
        else:
            os.makedirs(
                os.path.dirname(os.path.abspath(temp_model_path)), exist_ok=True
            )
            self._temp_model_path = temp_model_path

        # Create a copy to avoid modifying the original model file
        shutil.copy2(model_path, self._temp_model_path)

        # Initialize core interface
        self._core_instance = CoreInterface()
        if not self._core_instance.load_model(self._temp_model_path):
            msg = "Failed to load EwE model. Check that the model file is loadable via the GUI."
            raise EwEError(self._core_instance.get_state(), msg)

        # Initialize scenarios
        if not self._core_instance.Ecosim.new_scenario(
            "tmp_ecosim_scen",
            "temporary ecosim scenario used by decom_py",
            "",  # author
            "",  # contact
        ):
            msg = "Failed to create and load temporary ecosim scenario."
            raise EcosimError(self._core_instance.get_state(), msg)

        if not self._core_instance.Ecotracer.new_scenario(
            "tmp_ecotracer_scen",
            "temporary ecosim scenario used by decom_py",
            "",  # author
            "",  # contact
        ):
            msg = "Failed to create and load temporary ecotracer scenario."
            raise EcotracerError(self._core_instance.get_state(), msg)

        # Initialize parameter manager
        self._param_manager = ParameterManager.EcotracerManager(self._core_instance)

        # Clean up in case the user doesn't clean up.
        atexit.register(self.cleanup)

    def reset_parameters(self):
        """Remove all saved constant and variable parameters names and values."""
        self._param_manager = ParameterManager.EcotracerManager(self._core_instance)

    def get_ecotracer_fg_param_names(
        self, param_names: Union[str, List[str]] = "all"
    ) -> List[str]:
        """Get functional group parameter names for given parameter prefixes"""
        return self._param_manager.get_fg_param_names(param_names)

    def set_simulation_duration(self, n_years: int):
        """Set the number of years to run ecosim for."""
        return self._core_instance.Ecosim.set_n_years(n_years)

    def set_constant_params(
        self, param_names: List[str], param_values: List[float]
    ) -> None:
        """Set parameters that are constant across scenarios"""
        self._param_manager.set_constant_params(param_names, param_values)

    def _warn_unset_params(self):
        # Check for unset parameters
        unset = self._param_manager.get_unset_params()
        if unset:
            msg = f"The parameters {unset} have not been set to constant or variable. "
            msg += "They will be the default EwE parameters."
            warn(msg)

    def run_scenarios(
        self,
        scenarios: DataFrame,
    ) -> ResultSet:
        """Run scenarios in given dataframe.

        Run all scenarios in the given dataframe and save results in the given formats to
        the given directory.

        Arguments:
            scenarios: Scenario dataframe listing parameter values for each scenario.

        Returns:
            results (ResultSet): Containing results
        """
        col_names = [str(nm) for nm in scenarios.columns]

        # Set variable parameters from dataframe columns (excluding scenario column)
        self._param_manager.set_variable_params(
            col_names[1:], list(range(1, len(col_names)))
        )

        # Apply constant parameters
        self._param_manager.apply_constant_params(self._core_instance)

        # Warn user about unset parameters if there are any
        self._warn_unset_params()

        # Setup result manager
        result_manager = ResultManager(
            self._core_instance,
            [
                "Concentration",
                "Concentration Biomass",
                "Biomass",
                "Catch",
                "Consumption Biomass",
                "Mortality",
                "Trophic Level",
                "Trophic Level Catch",
                "FIB",
                "KemptonsQ",
                "Shannon Diversity",
            ],
            scenarios,
        )

        # Run each scenario
        for idx, row in tqdm(
            scenarios.iterrows(), desc="Running scenarios", total=scenarios.shape[0]
        ):
            # Apply variable parameters for this scenario
            self._param_manager.apply_variable_params(self._core_instance, list(row))

            # Run the model
            self._core_instance.Ecotracer.run()

            # Save results
            result_manager.collect_results(idx)

        return result_manager.to_result_set()

    def run_scenarios_parallel(
        self, scenarios: DataFrame, n_workers: Optional[int] = None
    ):
        """Run scenarios in parallel.

        Arguments:
            scenarios (DataFrame): Dataframe containing parameters for each scenario.
            n_workers (Optional[int]): Number of processes to run in parallel

        Returns:
            ResultSet: results from scenario runs.
        """

        # Save scenarios so that when copied, new core instances have constant variables
        self._core_instance.Ecosim.save_scenario()
        self._core_instance.Ecotracer.save_scenario()

        if n_workers is None:
            n_workers = os.cpu_count()
            if n_workers is None:
                raise RuntimeError("Failed to get number of cpus for default workers.")
            warn(f"n_workers not specified, using default {n_workers}")

        save_vars = [
            "Concentration",
            "Concentration Biomass",
            "Biomass",
            "Catch",
            "Consumption Biomass",
            "Mortality",
            "Trophic Level",
            "Trophic Level Catch",
            "FIB",
            "KemptonsQ",
            "Shannon Diversity",
        ]
        # Result managers share the same result store but need different intermediate caches
        manager, mp_buffers = ResultManager.construct_mp_result_manager(
            self._core_instance, save_vars, scenarios
        )

        col_names = [str(nm) for nm in scenarios.columns]
        n_scenarios = len(scenarios)

        # Set variable parameters from dataframe columns (excluding scenario column)
        self._param_manager.set_variable_params(
            col_names[1:], list(range(1, len(col_names)))
        )

        worker_init_args = (
            self._temp_model_path,
            self._param_manager,
            mp_buffers,
            save_vars,
            scenarios,
        )

        parallel_arg_pack = [(i, list(vals)) for (i, vals) in scenarios.iterrows()]

        with multiprocessing.Pool(
            processes=n_workers, initializer=worker_init, initargs=worker_init_args
        ) as pool:
            chunksize = math.floor(len(parallel_arg_pack) / n_workers)
            results_iterator = pool.imap_unordered(
                worker_run_scenario_wrapper, parallel_arg_pack, chunksize=chunksize
            )

            for _ in tqdm(
                results_iterator, total=len(parallel_arg_pack), desc="Running scenarios"
            ):
                continue

            print("Finished runs. Cleaning up workers.")

        return manager.to_result_set()

    def set_ecosim_group_info(self, group_info: DataFrame) -> None:
        """Set Ecosim group information parameters.

        Set the parameterisation for ecosim group information (feeding parameters). The
        data frame should be in the same format with the same column names as the table in
        the EwE GUI.
        """
        # Implementation needed
        n_consumers = self._core_instance.n_consumers()
        cons_list = list(range(1, n_consumers + 1))

        n_producers = self._core_instance.n_producers()
        prod_list = list(range(n_consumers + 1, n_consumers + n_producers + 1))
        self._core_instance.Ecosim.set_density_dep_catchability(
            list(group_info["Density-dep. catchability: Qmax/Qo [>=1]"])[:n_consumers],
            cons_list,
        )
        self._core_instance.Ecosim.set_feeding_time_adj_rate(
            list(group_info["Feeding time adjust rate [0,1]"])[:n_consumers], cons_list
        )
        self._core_instance.Ecosim.set_max_rel_feeding_time(
            list(group_info["Max rel. feeding time"])[:n_consumers], cons_list
        )
        self._core_instance.Ecosim.set_pred_effect_feeding_time(
            list(group_info["Predator effect on feeding time [0,1]"])[:n_consumers],
            cons_list,
        )
        self._core_instance.Ecosim.set_other_mort_feeding_time(
            list(
                group_info[
                    "Fraction of other mortality sens. to changes in feeding time"
                ]
            )[:n_consumers],
            cons_list,
        )
        self._core_instance.Ecosim.set_qbmax_qbio(
            list(group_info["QBmax/QBo (for handling time) [>1]"])[:n_consumers],
            cons_list,
        )
        self._core_instance.Ecosim.set_switching_power(
            list(group_info["Switching power parameter [0,2]"])[:n_consumers], cons_list
        )
        self._core_instance.Ecosim.set_max_rel_pb(
            list(group_info["Max rel. P/B"])[n_consumers : n_consumers + n_producers],
            prod_list,
        )
        warn("Additive prop. of predation mortality [0, 1]. Not yet supported.")

        return None

    def add_forcing_function(self, name: str, values: list[float]):
        """Add/Register forcing function for use in scenario runs."""
        return self._core_instance.add_forcing_function(name, values)

    def set_ecosim_vulnerabilities(self, vulnerabilities: DataFrame) -> None:
        """Set Ecosim vulnerabilities to use for all scenario runs.

        Set the vulnerabilitiy coefficient used in the Ecosim model. The format for the
        input dataframe should be the same format as seen in the EwE GUI.
        """
        # Implementation needed
        fg_names: list[str] = self._core_instance.get_functional_group_names()
        if "Prey \\ predator" in vulnerabilities.columns:
            if list(vulnerabilities["Prey \\ predator"]) != fg_names:
                msg = "Functional group list in dataframe does not match model. "
                msg += f"Model list {fg_names}. "
                df_fg_list = list(vulnerabilities["Prey \\ predator"])
                msg += f"Dataframe list {df_fg_list}"
                raise ValueError(msg)
        else:
            raise ValueError("Unable to find Prey \\ Predator column in Dataframe.")

        first_col_idx = list(vulnerabilities.columns).index("1")
        arr_vuln = np.array(vulnerabilities.iloc[0:, first_col_idx:])

        n_groups = self._core_instance.n_groups()
        n_consumers = self._core_instance.n_consumers()

        if arr_vuln.shape != (n_groups, n_consumers):
            msg = (
                f"Expected vulnerabilities matrix of shape {(n_groups, n_consumers)}. "
            )
            msg += f"but got matrix of shape {arr_vuln.shape}."
            raise ValueError(msg)

        return self._core_instance.Ecosim.set_vulnerabilities(arr_vuln)

    def get_empty_scenarios_df(
        self,
        env_param_names: List[str],
        fg_param_names: List[str],
        n_scenarios: int = 1,
    ) -> DataFrame:
        """Create empty scenarios dataframe for specified parameters.

        Arguments:
            env_param_names (list[str]): List of environmental parameter names.
            fg_param_names (list[str]): List of functional group parameter names, (not
                combined parameter names and functional group names.)
            n_scenarios (int): Number of scenarios to create a dataframe for.
        """
        # Validate environmental parameter names
        for name in env_param_names:
            if name not in self._param_manager._env_param_names:
                msg = f"Invalid parameter name: {name}. Make sure all are "
                msg += f"elements of {ParameterManager._env_param_names}."
                raise ValueError(msg)

        # Get functional group parameter names
        cols = self.get_ecotracer_fg_param_names(fg_param_names)
        cols.extend(env_param_names)

        # Create empty dataframe
        empty = np.zeros((n_scenarios, len(cols) + 1))
        empty[:, 0] = np.arange(1, n_scenarios + 1)

        cols.insert(0, "scenario")
        return DataFrame(empty, columns=cols)

    def get_long_scen_dataframe(self):
        """Get the full scenario dataframe in a long format.

        Construct a scenario dataframe in a long format. Given four columns, 'Scenario',
        'Group', 'Parameter', and 'Value'.
        """
        col_names: list[str] = ["Scenario", "Group", "Parameter", "Value"]
        fg_names = self._core_instance.get_functional_group_names()
        fg_params = self._param_manager._fg_param_prefixes
        env_params = self._param_manager._env_param_names

        data = []

        for param in env_params:
            data.append({"Scenario": 0, "Group": "Environment", "Parameter": param, "Value": None})

        for group in fg_names:
            for param in fg_params:
                data.append({"Scenario": 0, "Group": group, "Parameter": param, "Value": None})

        scen_df = pd.DataFrame(data, columns=col_names)

        return scen_df

    def cleanup(self):
        """Clean up files and directoryies created by the interface.

        Close the model database and delete the temporary directory containing the model.
        """
        self._core_instance.close_model()
        print("Closed model.")
        if not self._debugged_model:
            self._temp_dir.cleanup()
            msg = f"Temporary directory and model file at {self._temp_dir.name}"
            msg += " has been removed."
            print(msg)

        # If the user cleans up, no need to run at exit.
        atexit.unregister(self.cleanup)
