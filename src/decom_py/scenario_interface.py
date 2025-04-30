from warnings import warn
from pandas import DataFrame
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Union, Tuple, Dict, List, Optional, Any
import numpy as np
import shutil
import os
import math
from tqdm.auto import tqdm

from decom_py import CoreInterface
from .exceptions import EwEError, EcotracerError, EcosimError, EcopathError
from .results import ResultManager


class ParameterType:
    """Enum-like class for parameter types"""

    CONSTANT = "constant"
    VARIABLE = "variable"
    UNSET = "unset"


class Parameter:
    """Representation of a single parameter.

    Attributes:
        name: name of parameter.
        param_types: Constant, Varialbe or Unset.
        value: Parameter value. If variable the parameter value will be nan if constant it will be set.
        df_idx: Column index of parameter in scenario dataframe. If
        is_env_param: A boolean indicating if it in environmental parameter.
        group_idx: The index of the group in the underlying core instance. If the
            parameter is an environmental parameter,this will be -1.
    """

    def __init__(
        self,
        name: str,
        category_idx: int,
        is_env_param: bool,
        group_idx: int = -1,
        param_type: str = ParameterType.UNSET,
        value: float = math.nan,
        df_idx: int = -1,
    ):
        self.name = name
        self.param_type = param_type
        self.value = value
        self.df_idx = df_idx

        # Parse parameter information
        self.is_env_param = is_env_param
        self.category_idx = category_idx
        self.group_idx = group_idx

    def set_as_constant(self, value: float) -> None:
        self.param_type = ParameterType.CONSTANT
        self.value = value

    def set_as_variable(self, df_idx: int) -> None:
        self.param_type = ParameterType.VARIABLE
        self.df_idx = df_idx

    @property
    def is_set(self) -> bool:
        return self.param_type != ParameterType.UNSET


class ParameterManager:
    """Class to manage all parameters for an EwE model module.

    Attributes:
        fg_names: List of functional group names extracted from the core instance.
        params: Dictionary of all parameters underer management.
        _fg_param_prefixes: List of parameter names that are set for each functional group.
        _fg_param_to_setters: Dictionary of indices to name of function setters.
        _env_param_names: List of environmental parameter names.
        _env_param_to_setters: Dictionary of indices to names of function setters.

    """

    # Mapping from param category to setter function name
    def __init__(
        self,
        fg_names: List[str],
        fg_param_prefixes: List[str],
        fg_param_to_setters: Dict[int, str],
        env_param_names: List[str],
        env_param_to_setters: Dict[int, str],
    ):
        """Initialize parameter manager with functional group names"""
        self.fg_names = fg_names
        self.params: Dict[str, Parameter] = {}
        self._variable_params_processed = False

        self._fg_param_prefixes = fg_param_prefixes
        self._fg_param_to_setters = fg_param_to_setters
        self._env_param_names = env_param_names
        self._env_param_to_setter = env_param_to_setters
        self._initialize_params()

        self._variable_fg_indices = [[] for _ in range(len(fg_param_prefixes))]
        self._variable_fg_df_indices = [[] for _ in range(len(fg_param_prefixes))]
        self._variable_env_params = []

    @staticmethod
    def EcotracerManager(core):
        fg_param_prefixes = [
            "init_c",
            "immig_c",
            "direct_abs_r",
            "phys_decay_r",
            "meta_decay_r",
            "excretion_r",
        ]
        fg_param_to_setter = {
            0: "set_initial_concentrations",
            1: "set_immigration_concentrations",
            2: "set_direct_absorption_rates",
            3: "set_physical_decay_rates",
            4: "set_metabolic_decay_rates",
            5: "set_excretion_rates",
        }
        env_param_names = [
            "env_init_c",
            "env_base_inflow_r",
            "env_decay_r",
            "base_vol_ex_loss",
        ]
        env_param_to_setter = {
            0: "set_initial_env_concentration",
            1: "set_base_inflow_rate",
            2: "set_env_decay_rate",
            3: "set_env_volume_exchange_loss",
        }
        return ParameterManager(
            core.get_functional_group_names(),
            fg_param_prefixes,
            fg_param_to_setter,
            env_param_names,
            env_param_to_setter,
        )

    def _initialize_params(self) -> None:
        """Create all possible parameters"""
        # Create functional group parameters
        for prefix in self._fg_param_prefixes:
            for i, fg_name in enumerate(self.fg_names, 1):
                n_chars = len(str(len(self.fg_names)))
                param_name = self._format_param_name(prefix, i, n_chars, fg_name)
                cat_idx = self._fg_param_prefixes.index(prefix)
                param = Parameter(param_name, cat_idx, False, i)
                self.params[param_name] = param

        # Create environmental parameters
        for env_param in self._env_param_names:
            cat_idx = self._env_param_names.index(env_param)
            param = Parameter(env_param, cat_idx, True)
            self.params[env_param] = param

    @staticmethod
    def _format_param_name(prefix: str, index: int, n_chars: int, name: str) -> str:
        """Format functional group parameter names"""
        idx_str = str(index).rjust(n_chars, "0")
        return f"{prefix}_{idx_str}_{name}"

    def get_all_param_names(self) -> List[str]:
        """Get list of all parameter names"""
        return list(self.params.keys())

    def get_fg_param_names(
        self, param_prefixes: Union[str, List[str]] = "all"
    ) -> List[str]:
        """Get functional group parameter names for given prefixes"""
        if isinstance(param_prefixes, str) and param_prefixes == "all":
            param_prefixes = self._fg_param_prefixes
        elif isinstance(param_prefixes, str):
            param_prefixes = [param_prefixes]

        names = []
        for prefix in param_prefixes:
            if prefix not in self._fg_param_prefixes:
                raise ValueError(f"Invalid parameter prefix: {prefix}")
            names.extend(
                [name for name in self.params.keys() if name.startswith(prefix + "_")]
            )
        return names

    def set_constant_params(
        self, param_names: List[str], param_values: List[float]
    ) -> None:
        """Set parameters as constant with given values"""
        for name, value in zip(param_names, param_values):
            if name not in self.params:
                raise ValueError(f"Unknown parameter: {name}")
            self.params[name].set_as_constant(value)

    def get_unset_params(self) -> List[str]:
        """Get names of parameters that haven't been set"""
        return [
            name
            for name, param in self.params.items()
            if param.param_type == ParameterType.UNSET
        ]

    def get_conflicting_params(self) -> List[str]:
        """Get empty list - this implementation prevents conflicts"""
        return []

    def apply_constant_params(self, core: CoreInterface) -> None:
        """Apply all constant parameters to the core interface"""
        # Group parameters by category for batch application
        for cat_idx in range(len(self._fg_param_prefixes)):
            values = []
            group_indices = []

            for param in self.params.values():
                if (
                    param.param_type == ParameterType.CONSTANT
                    and not param.is_env_param
                    and param.category_idx == cat_idx
                ):
                    values.append(param.value)
                    group_indices.append(param.group_idx)

            if group_indices:
                setter_name = self._fg_param_to_setters[cat_idx]
                setter = getattr(core.Ecotracer, setter_name)
                setter(values, group_indices)

        # Apply environmental parameters
        for param in self.params.values():
            if param.param_type == ParameterType.CONSTANT and param.is_env_param:
                setter_name = self._env_param_to_setter[param.category_idx]
                setter = getattr(core.Ecotracer, setter_name)
                setter(param.value)

    def set_variable_params(
        self, param_names: List[str], df_indices: List[int]
    ) -> None:
        """Set parameters as variable with dataframe column indices"""
        for name, idx in zip(param_names, df_indices):
            if name not in self.params:
                raise ValueError(f"Unknown parameter: {name}")
            self.params[name].set_as_variable(idx)

        # Reset processed flag to ensure recalculation
        self._variable_params_processed = False

    def _process_variable_params(self) -> None:
        """Pre-calculate variable parameter information for efficient scenario runs"""
        if self._variable_params_processed:
            return

        # Reset existing calculations
        self._variable_fg_indices = [[] for _ in range(len(self._fg_param_prefixes))]
        self._variable_fg_df_indices = [[] for _ in range(len(self._fg_param_prefixes))]
        self._variable_env_params = []

        # Process functional group parameters
        for param in self.params.values():
            if param.param_type == ParameterType.VARIABLE:
                if param.is_env_param:
                    # Store (env_param_index, df_index, setter_name)
                    setter_name = self._env_param_to_setter[param.category_idx]
                    self._variable_env_params.append(
                        (param.category_idx, param.df_idx, setter_name)
                    )
                else:
                    # Group by category
                    self._variable_fg_indices[param.category_idx].append(
                        param.group_idx
                    )
                    self._variable_fg_df_indices[param.category_idx].append(
                        param.df_idx
                    )

        self._variable_params_processed = True

    def apply_variable_params(
        self, core: CoreInterface, scenario_values: List[float]
    ) -> None:
        """Apply variable parameters for a scenario to the core interface efficiently"""
        # Process variable params if not already done
        self._process_variable_params()

        # Apply functional group parameters
        for cat_idx in range(len(self._fg_param_prefixes)):
            if self._variable_fg_indices[cat_idx]:
                values = [
                    scenario_values[df_idx]
                    for df_idx in self._variable_fg_df_indices[cat_idx]
                ]
                setter_name = self._fg_param_to_setters[cat_idx]
                setter = getattr(core.Ecotracer, setter_name)
                setter(values, self._variable_fg_indices[cat_idx])

        # Apply environmental parameters
        for env_idx, df_idx, setter_name in self._variable_env_params:
            setter = getattr(core.Ecotracer, setter_name)
            setter(scenario_values[df_idx])


class EwEScenarioInterface:
    """Interface for running Ecopath with Ecosim scenarios.

    Attributes:
        _model_path (str): Path to EwE model database file.
        _temp_model_path (str): Path to temporary model database file.
        _param_manager (ParameterManager): Parameter manager object to manage variable and
            constant params.
    """

    def __init__(self, model_path: str, temp_model_path: Optional[str] = None):
        self._model_path = model_path
        mod_path_obj = Path(model_path)
        if not mod_path_obj.exists():
            raise FileNotFoundError(model_path)

        # The temporary directory should clean itself up
        if temp_model_path is None:
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
    ) -> ResultManager:
        """Run scenarios in given dataframe.

        Run all scenarios in the given dataframe and save results in the given formats to
        the given directory.

        Arguments:
            scenarios: Scenario dataframe listing parameter values for each scenario.

        Returns: 
            results (ResultManager): Containing results
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
            ["Concentration", "Concentration Biomass"],
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

        return result_manager

    def set_ecosim_group_info(self, group_info: DataFrame) -> None:
        """Set Ecosim group information"""
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

    def set_ecosim_vulnerabilities(self, vulnerabilities: DataFrame) -> None:
        """Set Ecosim vulnerabilities to use for all scenario runs"""
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
        """Create empty scenarios dataframe for specified parameters"""
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
