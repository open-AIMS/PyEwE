from typing import Union, Dict, List
from math import nan

from decom_py import CoreInterface


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
        category_idx: Index into the type of function group parameter dictionary.
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
        value: float = nan,
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
        """Given a core instance, construct a Ecotracer parameter manager."""
        # The names of parameters are derived from the EwE model.
        fg_param_prefixes = [
            "init_c",
            "immig_c",
            "direct_abs_r",
            "phys_decay_r",
            "meta_decay_r",
            "excretion_r",
        ]
        # The name of the setters can be found the in the definitions of the EwE models in
        # core.models
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
            "env_inflow_forcing_idx",
        ]
        env_param_to_setter = {
            0: "set_initial_env_concentration",
            1: "set_base_inflow_rate",
            2: "set_env_decay_rate",
            3: "set_env_volume_exchange_loss",
            4: "set_contaminant_forcing_number",
        }
        return ParameterManager(
            core.get_functional_group_names(),
            fg_param_prefixes,
            fg_param_to_setter,
            env_param_names,
            env_param_to_setter,
        )

    def _initialize_params(self) -> None:
        """Create all possible parameters.

        Create a list of parameter objects based on the list of known functional group names
        and parameters prefixes. Includes environmental parameters.
        """
        # Create functional group parameters
        for prefix in self._fg_param_prefixes:
            for i, fg_name in enumerate(self.fg_names, 1):
                # n_chars padding the index in the name so the naming 
                # in alphabetical order follows the order of the ecopath model.
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
        """Get functional group parameter names for given prefixes.

        Arguments:
            param_prefixes (Union[str, List[str]]): List of parameter prefixes or 'all' to
                get parameter names for.

        Returns:
            list[str]: list of functinoal group parameter names.
        """
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
        """Set parameters as constant with given values.

        Sets given parameters as constants throughout scenario runs and stores the value in
        the parameter manager. This function does NOT write the value into the core EwE
        instance.
        """
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
        """Apply all constant parameters to the core interface.

        For all parameters in the parameter manager that is listed as constant, write the
        value contained in the parameter object into the given EwE core instance.

        Arguments:
            core (CoreInterface): Core instance to write to.
        """
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
        """Set parameters as variable with dataframe column indices."""
        for name, idx in zip(param_names, df_indices):
            if name not in self.params:
                raise ValueError(f"Unknown parameter: {name}")
            self.params[name].set_as_variable(idx)

        # Reset processed flag to ensure recalculation
        self._variable_params_processed = False

    def _process_variable_params(self) -> None:
        """Pre-calculate variable parameter information for efficient scenario runs.

        For each variable parameter, construct lists of indices indicating which parameters
        for which functional groups should be written to the EwE core instance. Furthermore,
        store the column index in the scenario dataframe that variables are store in. This
        is only calculated once, repeated calls will do nothing, until '_variable_params
        processed' is set to False.
        """
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
        """Apply variable parameters for a scenario to the core interface efficiently

        Given a list of parameter values for a given scenario, write them into the core
        instance prior to a model run. If the variable parameter datastructures to help with
        efficient writing have not been constructed, construct them.

        Arguments:
            scenario_values (list[float]): List of parameter values in the same order as the
                columns passed to the set_variable_params function.

        Returns:
            None
        """
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
