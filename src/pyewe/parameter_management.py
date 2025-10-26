from typing import Union, Dict, List, Tuple, Set, Optional
from math import nan

from pyewe import CoreInterface
from pyewe.core.models import EwEParameterManager as EwEModelParameterManager


def _full_name_to_abbrev(nm: str) -> str:
    """Map ecotracer parameter column names to abbreviated names."""
    name_map = {
        "Initial conc. (t/t)": "init_c",
        "Conc. in immigrating biomass (t/t)": "immig_c",
        "Direct absorption rate": "direct_abs_r",
        "Physical decay rate": "phys_decay_r",
        "Prop. of contaminant excreted": "excretion_r",
        "Metabolic decay rate": "meta_decay_r",
    }
    return name_map[nm]


class ParameterType:
    """Enum-like class for parameter types"""

    CONSTANT = "constant"
    VARIABLE = "variable"
    VULNERABILITY = "vulnerability"
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
            parameter is an environmental parameter,this will be -1. For vulnerability
            parameters, this will be a tuple of (prey_idx, pred_idx).
    """

    def __init__(
        self,
        name: str,
        category_idx: int,
        is_env_param: bool,
        group_idx: Union[int, Tuple[int, int]] = -1,
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
        model_name: str,
        fg_names: List[str],
        fg_param_prefixes: List[str],
        fg_param_to_setters: Dict[int, str],
        env_param_names: List[str],
        env_param_to_setters: Dict[int, str],
    ):
        """Initialize parameter manager with functional group names"""
        self.model_name = model_name

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
        self._variable_vuln_params = []

    @staticmethod
    def EcotracerManager(core: CoreInterface):
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
            "Ecotracer",
            core.get_functional_group_names(),
            fg_param_prefixes,
            fg_param_to_setter,
            env_param_names,
            env_param_to_setter,
        )

    @staticmethod
    def EcosimManager(core: CoreInterface):
        """Given a core instance, construct an Ecosim parameter manager."""
        fg_param_prefixes = [
            "density_dep_catchability",
            "feeding_time_adj_rate",
            "max_rel_feeding_time",
            "max_rel_pb",
            "pred_effect_feeding_time",
            "other_mort_feeding_time",
            "qbmax_qbio",
            "switching_power",
        ]
        fg_param_to_setter = {
            0: "set_density_dep_catchability",
            1: "set_feeding_time_adj_rate",
            2: "set_max_rel_feeding_time",
            3: "set_max_rel_pb",
            4: "set_pred_effect_feeding_time",
            5: "set_other_mort_feeding_time",
            6: "set_qbmax_qbio",
            7: "set_switching_power",
        }
        env_param_names = []
        env_param_to_setter = {}

        manager = ParameterManager(
            "Ecosim",
            core.get_functional_group_names(),
            fg_param_prefixes,
            fg_param_to_setter,
            env_param_names,
            env_param_to_setter,
        )

        # Create vulnerability parameters
        fg_names = core.get_functional_group_names()
        n_chars = len(str(len(fg_names)))
        for prey_idx, prey_name in enumerate(fg_names, 1):
            prey_idx_str = str(prey_idx).rjust(n_chars, "0")
            for pred_idx, pred_name in enumerate(fg_names, 1):
                pred_idx_str = str(pred_idx).rjust(n_chars, "0")
                param_name = f"vuln_{prey_idx_str}_{prey_name}_{pred_idx_str}_{pred_name}"
                # Category index is not used for vulnerabilities, set to -1
                param = Parameter(
                    param_name, -1, False, group_idx=(prey_idx, pred_idx)
                )
                param.param_type = ParameterType.VULNERABILITY
                manager.params[param_name] = param

        return manager

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

    @staticmethod
    def format_param_names(
        full_param_names: List[str], functional_groups: List[str], core: CoreInterface
    ):
        prefixes = [_full_name_to_abbrev(full_nms) for full_nms in full_param_names]
        idxs = core.get_functional_group_indices(functional_groups)
        n_chars = len(str(len(core.get_functional_group_names())))
        return [
            ParameterManager._format_param_name(p, i, n_chars, n)
            for (p, i, n) in zip(prefixes, idxs, functional_groups)
        ]

    @staticmethod
    def format_param_name(
        full_param_name: str, functional_group: str, core: CoreInterface
    ):
        """Given a functional group and full parameter name. Create the abbreviated name."""
        return _full_param_format([full_param_name], [functional_group], core)[0]

    def get_all_param_names(self) -> List[str]:
        """Get list of all parameter names"""
        return list(self.params.keys())

    def get_env_param_names(self) -> List[str]:
        """Get list of all parameter names."""
        return self._env_param_names

    def get_fg_param_names(
        self,
        param_prefixes: Optional[Union[str, List[str]]] = None,
        functional_groups: Optional[Union[str, int, List[Union[str, int]]]] = None,
    ) -> List[str]:
        """Get functional group parameter names for given prefixes and functional groups.

        Arguments:
            param_prefixes (Optional[Union[str, List[str]]]): List of parameter prefixes or a single prefix string.
                If None, all prefixes are used.
            functional_groups (Optional[Union[str, int, List[Union[str, int]]]]): A single functional group name (str) or
                1-based index (int), or a list of names or indices. If None, all functional groups are used.

        Returns:
            list[str]: list of functional group parameter names.
        """
        # Handle param_prefixes
        if param_prefixes is None:
            prefix_list = self._fg_param_prefixes
        elif isinstance(param_prefixes, str):
            prefix_list = [param_prefixes]
        else:
            prefix_list = param_prefixes

        # Handle functional_groups
        target_fg_names = set()
        if functional_groups is None:
            target_fg_names = set(self.fg_names)
        else:
            if not isinstance(functional_groups, list):
                functional_groups = [functional_groups]

            for fg_identifier in functional_groups:
                if isinstance(fg_identifier, int):
                    # 1-based index
                    if 1 <= fg_identifier <= len(self.fg_names):
                        target_fg_names.add(self.fg_names[fg_identifier - 1])
                    else:
                        raise ValueError(f"Invalid functional group index: {fg_identifier}")
                elif isinstance(fg_identifier, str):
                    if fg_identifier in self.fg_names:
                        target_fg_names.add(fg_identifier)
                    else:
                        raise ValueError(f"Invalid functional group name: {fg_identifier}")
                else:
                    raise TypeError(f"Unsupported type in functional_groups: {type(fg_identifier)}")

        names = []
        for prefix in prefix_list:
            if prefix not in self._fg_param_prefixes:
                raise ValueError(f"Invalid parameter prefix: {prefix}")

            for fg_name in target_fg_names:
                # Need to get the index for the name
                fg_index = self.fg_names.index(fg_name) + 1
                n_chars = len(str(len(self.fg_names)))
                param_name = self._format_param_name(prefix, fg_index, n_chars, fg_name)
                if param_name in self.params:  # Check if the parameter actually exists
                    names.append(param_name)

        return sorted(names)

    def set_constant_params(
        self, param_names: List[str], param_values: List[float]
    ) -> Set[str]:
        """Set parameters as constant with given values.

        Sets given parameters as constants throughout scenario runs and stores the value in
        the parameter manager. This function does NOT write the value into the core EwE
        instance.
        """
        ignored_params = set()
        for name, value in zip(param_names, param_values):
            if name not in self.params:
                ignored_params.add(name)
                continue
            self.params[name].set_as_constant(value)

        return ignored_params

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
            core (CoreInterface): Core object to write to.
        """
        # Group parameters by category for batch application
        model = getattr(core, self.model_name)
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
                setter = getattr(model, setter_name)
                setter(values, group_indices)

        # Apply environmental and vulnerability parameters (which are not batched)
        for param in self.params.values():
            if param.param_type == ParameterType.CONSTANT:
                if param.is_env_param:
                    setter_name = self._env_param_to_setter[param.category_idx]
                    setter = getattr(model, setter_name)
                    setter(param.value)
                elif param.param_type == ParameterType.VULNERABILITY:
                    prey_idx, pred_idx = param.group_idx
                    model.set_vulnerability(prey_idx, pred_idx, param.value)

    def set_variable_params(
        self, param_names: List[str], df_indices: List[int]
    ) -> Set[str]:
        """Set parameters as variable with dataframe column indices."""
        ignored_params = set()
        for name, idx in zip(param_names, df_indices):
            if name not in self.params:
                ignored_params.add(name)
                continue
            self.params[name].set_as_variable(idx)

        # Reset processed flag to ensure recalculation
        self._variable_params_processed = False

        return ignored_params

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
        self._variable_vuln_params = []

        # Process functional group parameters
        for param in self.params.values():
            if param.param_type == ParameterType.VARIABLE:
                if param.is_env_param:
                    # Store (env_param_index, df_index, setter_name)
                    setter_name = self._env_param_to_setter[param.category_idx]
                    self._variable_env_params.append(
                        (param.category_idx, param.df_idx, setter_name)
                    )
                elif param.param_type == ParameterType.VULNERABILITY:
                    prey_idx, pred_idx = param.group_idx
                    self._variable_vuln_params.append(
                        (prey_idx, pred_idx, param.df_idx)
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
            core (CoreInterface): Core object to write to.
            scenario_values (list[float]): List of parameter values in the same order as the
                columns passed to the set_variable_params function.

        Returns:
            None
        """
        # Process variable params if not already done
        self._process_variable_params()

        model = getattr(core, self.model_name)

        # Apply functional group parameters
        for cat_idx in range(len(self._fg_param_prefixes)):
            if self._variable_fg_indices[cat_idx]:
                values = [
                    scenario_values[df_idx]
                    for df_idx in self._variable_fg_df_indices[cat_idx]
                ]
                setter_name = self._fg_param_to_setters[cat_idx]
                setter = getattr(model, setter_name)
                setter(values, self._variable_fg_indices[cat_idx])

        # Apply environmental parameters
        for _, df_idx, setter_name in self._variable_env_params:
            setter = getattr(model, setter_name)
            setter(scenario_values[df_idx])

        # Apply vulnerability parameters
        for prey_idx, pred_idx, df_idx in self._variable_vuln_params:
            value = scenario_values[df_idx]
            model.set_vulnerability(prey_idx, pred_idx, value)

class ParentParameterManager:

    def __init__(
        self,
        core: CoreInterface,
        ecosim: bool=True,
        ecotracer: bool=True
    ):
        self._managers = []
        if ecosim:
            self._managers.append(ParameterManager.EcosimManager(core))

        if ecotracer:
            self._managers.append(ParameterManager.EcotracerManager(core))

    def set_constant_params(self, param_names: List[str], param_values: List[float]):
        unused_params = set(param_names)
        for manager in self._managers:
            unused_params = unused_params.intersection(
                manager.set_constant_params(param_names, param_values)
            )

        if unused_params:
            ValueError(f"Unrecognised parameters: {unused_params}")

        return None

    def apply_constant_params(self, core: CoreInterface):
        for manager in self._managers:
            manager.apply_constant_params(core)

        return None

    def set_variable_params(self, param_names: List[str], param_idxs: List[int]):
        unused_params = set(param_names)
        for manager in self._managers:
            unused_params = unused_params.intersection(
                manager.set_variable_params(param_names, param_idxs)
            )

        if unused_params:
            ValueError(f"Unrecognised parameters: {unused_params}")

        return None

    def apply_variable_params(self, core: CoreInterface, param_values: List[float]):
        for manager in self._managers:
            manager.apply_variable_params(core, param_values)

        return None

    def get_fg_param_names(self, param_names):
        param_names = []
        for manager in self._managers:
            param_names.extend(manager.get_fg_param_names(param_names))

        return param_names

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
            model_types = [m.model_name.lower() for m in self._managers]
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

        for manager in self._managers:
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
