from warnings import warn
from pandas import DataFrame
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Union, Dict, List, Optional
from tqdm.auto import tqdm

import time
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
from .parameter_management import ParentParameterManager, ParameterManager
from .worker import worker_init, worker_run_scenario, worker_clean_up


def worker_run_scenario_wrapper(args):
    scen_idx, scen_params = args
    return worker_run_scenario(scen_idx, scen_params)


def _check_scenario_column(col_names: list[str]):
    """Check if the scenario dataframe has a scenario column. Throw if not."""
    if col_names[0] != "scenario":
        msg = 'The first column of the scenario dataframe must be "scenario".'
        msg += f"The first column name received was {col_names[0]}"
        raise ValueError(msg)


class EwEScenarioInterface:
    """Interface for running Ecopath with Ecosim scenarios.

    Attributes:
        _model_path (str): Path to EwE model database file.
        _temp_model_path (str): Path to temporary model database file.
        _param_manager (ParameterManager): Parameter manager object to manage variable and
            constant params.
    """

    def __init__(
        self,
        model_path: str,
        temp_model_path: Optional[str] = None,
        ecosim_scenario: Optional[str] = None,
        constant_ecosim: bool = False
    ):
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
        self._core_instance.disable_logging()
        if not self._core_instance.load_model(self._temp_model_path):
            msg = "Failed to load EwE model. Check that the model file is loadable via the GUI."
            raise EwEError(self._core_instance.get_state(), msg)

        # Initialize scenarios
        if ecosim_scenario is None:
            self._ecosim_scenario = "tmp_ecosim_scen"
            if not self._core_instance.Ecosim.new_scenario(
                "tmp_ecosim_scen",
                "temporary ecosim scenario used by PyEwE",
                "",  # author
                "",  # contact
            ):
                msg = "Failed to create and load temporary ecosim scenario."
                raise EcosimError(self._core_instance.get_state(), msg)
        else:
            self._ecosim_scenario = ecosim_scenario
            if not self._core_instance.Ecosim.load_scenario(ecosim_scenario):
                msg = f"Failed to load ecosim scenario {ecosim_scenario}."
                raise EcosimError(self._core_instance.get_state(), msg)

        if not self._core_instance.Ecotracer.new_scenario(
            "tmp_ecotracer_scen",
            "temporary ecosim scenario used by PyEwE",
            "",  # author
            "",  # contact
        ):
            msg = "Failed to create and load temporary ecotracer scenario."
            raise EcotracerError(self._core_instance.get_state(), msg)

        # Initialize parameter managers
        self._constant_ecosim = constant_ecosim
        self._param_manager = ParentParameterManager(self._core_instance, ecosim=not constant_ecosim)

        # Clean up in case the user doesn't clean up.
        atexit.register(self.cleanup)

    def reset_parameters(self):
        """Remove all saved constant and variable parameters names and values."""
        self._param_manager = ParentParameterManager(self._core_instance, ecosim=not self._constant_ecosim)

    def format_param_names(
        self, full_param_names: List[str], functional_groups: List[str]
    ) -> List[str]:
        return ParameterManager.format_param_names(
            full_param_names, functional_groups, self._core_instance
        )

    def get_available_parameter_names(
        self,
        model_type: Optional[Union[str, List[str]]] = None,
        param_types: Optional[Union[str, List[str]]] = None,
        prefixes: Optional[Union[str, List[str]]] = None,
        functional_groups: Optional[Union[str, int, List[Union[str, int]]]] = None,
    ) -> List[str]:
        """
        Get a list of available parameter names based on specified criteria.

        Args:
            model_type (Optional[Union[str, List[str]]]): 'ecosim', 'ecotracer', or a list of them.
                If None, parameters for all models are returned.
            param_types (Optional[Union[str, List[str]]]): 'fg' for functional group parameters,
                'env' for environmental parameters. If None, all parameter types are returned.
            prefixes (Optional[Union[str, List[str]]]): List of functional group parameter prefixes
                (e.g., 'init_c', 'immig_c'). If None, includes all.
            functional_groups (Optional[Union[str, int, List[Union[str, int]]]]): List of specific functional group
                names or 1-based indices. If None, includes all functional groups.

        Returns:
            List[str]: A sorted list of unique parameter names matching the criteria.
        """
        all_param_names = set()

        # Normalize model_type to a list
        if model_type is None:
            model_types = [m.model_name.lower() for m in self._param_manager._managers]
        elif isinstance(model_type, str):
            model_types = [model_type.lower()]
        else:
            model_types = [m.lower() for m in model_type]

        # Normalize param_types to a list
        if param_types is None:
            param_type_list = ["fg", "env"]
        elif isinstance(param_types, str):
            param_type_list = [param_types]
        else:
            param_type_list = param_types

        for manager in self._param_manager._managers:
            if manager.model_name.lower() in model_types:
                if "fg" in param_type_list:
                    fg_params = manager.get_fg_param_names(
                        param_prefixes=prefixes,
                        functional_groups=functional_groups,
                    )
                    all_param_names.update(fg_params)

                if "env" in param_type_list:
                    # Assuming get_env_param_names exists as per user's information
                    env_params = manager.get_env_param_names()
                    all_param_names.update(env_params)

        return sorted(list(all_param_names))

    def set_simulation_duration(self, n_years: int):
        """Set the number of years to run ecosim for."""
        return self._core_instance.Ecosim.set_n_years(n_years)

    def set_constant_params(
        self, param_names: List[str], param_values: List[float]
    ) -> None:
        """Set parameters that are constant across scenarios"""
        self._param_manager.set_constant_params(param_names, param_values)

    def run_scenarios(
        self,
        scenarios: DataFrame,
        save_vars=[
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
        show_progress=True,
        verbose=True,
    ) -> ResultSet:
        """Run scenarios in given dataframe.

        Run all scenarios in the given dataframe and save results in the given formats to
        the given directory.

        Arguments:
            scenarios: Scenario dataframe listing parameter values for each scenario.

        Returns:
            results (ResultSet): Containing results
        """
        col_names = [str(cl) for cl in scenarios.columns]
        _check_scenario_column(col_names)

        # Set variable parameters from dataframe columns (excluding scenario column)
        self._param_manager.set_variable_params(
            col_names[1:], list(range(1, len(col_names)))
        )

        # Apply constant parameters
        self._param_manager.apply_constant_params(self._core_instance)

        # Setup result manager
        result_manager = ResultManager(
            self._core_instance,
            save_vars,
            scenarios,
        )

        # Run each scenario
        for idx, row in tqdm(
            scenarios.iterrows(),
            desc="Running scenarios",
            total=scenarios.shape[0],
            disable=not show_progress,
        ):
            # Apply variable parameters for this scenario
            self._param_manager.apply_variable_params(self._core_instance, list(row))

            # Run the model
            self._core_instance.Ecotracer.run()

            # Save results
            result_manager.collect_results(idx)

        return result_manager.to_result_set()

    def run_scenarios_parallel(
        self,
        scenarios: DataFrame,
        n_workers: Optional[int] = None,
        save_vars=[
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
        show_progress=True,
    ):
        """Run scenarios in parallel.

        Arguments:
            scenarios (DataFrame): Dataframe containing parameters for each scenario.
            n_workers (Optional[int]): Number of processes to run in parallel

        Returns:
            ResultSet: results from scenario runs.
        """
        col_names = [str(cl) for cl in scenarios.columns]
        _check_scenario_column(col_names)

        if n_workers is None:
            n_workers = os.cpu_count()
            if n_workers is None:
                raise RuntimeError("Failed to get number of cpus for default workers.")
            warn(f"n_workers not specified, using default {n_workers}")

        # Result managers share the same result store but need different intermediate caches
        manager, mp_buffers = ResultManager.construct_mp_result_manager(
            self._core_instance, save_vars, scenarios
        )
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
            self._ecosim_scenario,
        )

        parallel_arg_pack = [(i, list(vals)) for (i, vals) in scenarios.iterrows()]
        self._core_instance.close_model()

        with multiprocessing.Pool(
            processes=n_workers, initializer=worker_init, initargs=worker_init_args
        ) as pool:
            results_iterator = pool.imap_unordered(
                worker_run_scenario_wrapper, parallel_arg_pack, chunksize=1
            )

            for _ in tqdm(
                results_iterator,
                total=len(parallel_arg_pack),
                desc="Running scenarios",
                disable=not show_progress,
            ):
                continue

            print("Finished runs. Cleaning up workers.")

        self._core_instance.load_model(self._temp_model_path)
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
        param_names: List[str],
        n_scenarios: int = 1,
    ) -> DataFrame:
        """Create empty scenarios dataframe for specified parameters.

        Arguments:
            param_names (list[str]): List of parameter names (environmental or functional group).
                                     These can be obtained using get_available_parameter_names().
            n_scenarios (int): Number of scenarios to create a dataframe for.
        """
        # Validate parameter names
        for name in param_names:
            if name not in self._param_manager.params:
                raise ValueError(f"Invalid parameter name: {name}. Use get_available_parameter_names() to get valid names.")

        cols = ["scenario"] + param_names

        # Create empty dataframe
        empty = np.zeros((n_scenarios, len(cols)))
        empty[:, 0] = np.arange(1, n_scenarios + 1)

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
            data.append(
                {
                    "Scenario": 0,
                    "Group": "Environment",
                    "Parameter": param,
                    "Value": None,
                }
            )

        for group in fg_names:
            for param in fg_params:
                data.append(
                    {"Scenario": 0, "Group": group, "Parameter": param, "Value": None}
                )

        scen_df = pd.DataFrame(data, columns=col_names)

        return scen_df

    def cleanup(self):
        """Clean up files and directoryies created by the interface.

        Close the model database and delete the temporary directory containing the model.
        """
        self._core_instance.close_model()
        print("Closed model.")
        if not self._debugged_model:
            max_retries = 10  # Try for 5 seconds (10 * 0.5s)
            for i in range(max_retries):
                try:
                    # The operation we expect to fail
                    self._temp_dir.cleanup()

                    # If it succeeds, print message and break the loop
                    msg = f"Temporary directory and model file at {self._temp_dir.name} has been removed."
                    print(msg)
                    break
                except (PermissionError, OSError) as e:
                    if i < max_retries - 1:
                        print(
                            f"File is still locked, retrying... ({i+1}/{max_retries})"
                        )
                        time.sleep(0.5)  # Wait half a second before trying again
                    else:
                        print(
                            "ERROR: File lock was not released in time. Cleanup failed."
                        )

        # If the user cleans up, no need to run at exit.
        atexit.unregister(self.cleanup)
