from warnings import warn
from pandas import DataFrame
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Union, Tuple
import numpy as np
import shutil
import os
import math

from tqdm import tqdm

from decom_py import CoreInterface
from .Exceptions import EwEError, EcotracerError, EcosimError, EcopathError

def _list_index(lst: list, idxs: list[int]):
    return [lst[i] for i in idxs]

def _int_to_ordered_str(i: int, n_chars: int):
    """Convert an integer to a string but prepend zeros to guarentee n_chars.

    # Example:
        >>> _int_to_ordered_str(3, 4)
        "0003"
        >>> _int_to_ordered_str(10, 3)
        "010"
    """
    tmp_str: str = str(i)
    return tmp_str.rjust(n_chars - len(tmp_str), '0')

def _format_fg_param_names(prefix: str, index: int, n_chars: int, name: str) -> str:
    """Format functional group parameter names.

    Given the parameter prefix, functional group index and name format into string split
    by underscores.

    # Example:
        >>> _format_fg_param_names("prefix", 6, 3, "name")
        "prefix_006_name"
    """
    return "_".join([prefix, _int_to_ordered_str(index, n_chars), name])

def extract_integer(param_name: str) -> int:
    in_underscores = False
    out = ""
    for char in param_name:
        if char == "_":
            if in_underscores and out:
                break
            in_underscores = True
            out = ""
        elif char.isdigit() and in_underscores:
            out += char
        elif in_underscores and out:
            break
    return int(out)

def _extract_fg_param_indexs(prefixs: list[str], name: str) -> Tuple[int, int]:
    param_cat_idx: int = -1
    for (i, prefix) in enumerate(prefixs):
        if prefix == name[:len(prefix)]:
            param_cat_idx = i
            break

    if param_cat_idx == -1:
        raise ValueError(
            f"Invalid parameter name. Could not find prefixs: {prefixs} in {name}"
        )

    group_idx = extract_integer(name)
    return param_cat_idx, group_idx

def _construct_param_names(param_prefix, fg_names) -> list[str]:
    """Construct parameter names for a single param prefix."""
    n_fgs = len(fg_names)
    n_idx_chars = len(str(len(fg_names)))
    return [
        _format_fg_param_names(param_prefix, i, n_idx_chars, fg)
        for (i, fg) in zip(range(1, n_fgs + 1), fg_names)
    ]

def _construct_all_param_names(param_prefixes, fg_names) -> list[str]:
    """Construct all parameter names for a list of prefixes and functional groups."""
    names = []
    for prefix in param_prefixes:
        names.extend(_construct_param_names(prefix, fg_names))
    return names

def _is_valid_param_list(user_input: list[str], all_params: list[str]) -> bool:
    """Check that the first input contains unique elements and is a subet of the second."""
    user_set = set(user_input)
    param_set = set(all_params)

    return len(user_set) == len(user_input) and set(user_set).issubset(param_set)

class EwEScenarioInterface:

    # Ecotracer parameter name prefixes for use in the scenario dataframe
    ecotracer_fg_param_name_prefixes = [
        "init_c",
        "immig_c",
        "direct_abs_r",
        "phys_decay_r",
        "excretion_r",
        "meta_decay_r"
    ]

    # Ecotracer environmental parameter names
    ecotracer_env_param_names = [
        "env_init_c",
        "env_base_inflow_r",
        "env_decay_r",
        "base_vol_ex_loss"
    ]

    _all_possible_params = None

    def __init__(self, model_path: str):

        self._model_path = model_path
        mod_path_obj = Path(model_path)
        if not mod_path_obj.exists():
            raise FileNotFoundError(model_path)

        # The temporary directory should clean itself up.
        self._temp_dir = TemporaryDirectory()
        self._temp_model_path = os.path.join(self._temp_dir.name, os.path.basename(model_path))

        # to avoid modifying the original model file, create a copy
        shutil.copy2(model_path, self._temp_model_path)

        self._core_instance = CoreInterface()
        if not self._core_instance.load_model(model_path):
            msg = "Failed to load EwE model. "
            msg += "Check that the model file is loadable via the gui."
            raise EwEError(self._core_instance.get_state(), msg)

        if not self._core_instance.Ecosim.new_scenario(
            "tmp_ecosim_scen",
            "temporary ecosim scenario used by decom_py",
            "", # author
            ""  # contact
        ):
            msg = "Failed to create and load temporary ecosim scenario."
            raise EcosimError(self._core_instance.get_state(), msg)

        if not self._core_instance.Ecotracer.new_scenario(
            "tmp_ecotracer_scen",
            "temporary ecosim scenario used by decom_py",
            "", # author
            ""  # contact
        ):
            msg = "Failed to create and load temporary ecotracer scenario."
            raise EcotracerError(self._core_instance.get_state(), msg)

        self._constant_params = []
        self._variable_params = []

    def _init_constant_param_setup(self) -> None:
        self._constant_fg_param_idxs: list[list[int]] = [[]] * len(
            self.ecotracer_fg_param_name_prefixes
        )
        self._constant_fg_param_values: list[list[float]] = [[]] * len(
            self.ecotracer_fg_param_name_prefixes
        )
        self._constant_env_param_values: list[float] = [math.nan] * len(
            self.ecotracer_env_param_names
        )

    def _init_variable_param_setup(self) -> None:
        self._variable_fg_param_idxs: list[list[int]] = [[]] * len(
            self.ecotracer_fg_param_name_prefixes
        )
        self._variable_fg_param_df_idx: list[list[int]] = [[]] * len(
            self.ecotracer_fg_param_name_prefixes
        )
        self._variable_env_param_df_idxs: list[int] = [-1] * len(
            self.ecotracer_env_param_names
        )

    def _add_constant_param(self, name: str, value: float):
        env_idx = (
            self.ecotracer_env_param_names.index(name) if name in
                self.ecotracer_env_param_names else None
        )
        if not env_idx is None:
            self._constant_env_param_values[env_idx] = value
            return None

        param_category, group_idx = _extract_fg_param_indexs(
            self.ecotracer_fg_param_name_prefixes, name
        )

        self._constant_fg_param_idxs[param_category].append(group_idx)
        self._constant_fg_param_values[param_category].append(value)

    def _add_variable_param(self, name:str, df_col_idx: int):
        env_idx = (
            self.ecotracer_env_param_names.index(name) if name in
                self.ecotracer_env_param_names else None
        )
        if not env_idx is None:
            self._variable_env_param_df_idxs[env_idx] = df_col_idx
            return None

        param_category, group_idx = _extract_fg_param_indexs(
            self.ecotracer_fg_param_name_prefixes, name
        )

        self._variable_fg_param_idxs[param_category].append(group_idx)
        self._variable_fg_param_df_idx[param_category].append(df_col_idx)


    def get_ecotracer_fg_param_names(self, param_names: Union[str, list[str]]="all") -> list[str]:
        """Get list of all parameters names for a list of ecotracer names"""
        if isinstance(param_names, list):
            p_names = list(param_names)
            if not _is_valid_param_list(p_names, self.ecotracer_fg_param_name_prefixes):
                msg = "Invalid parameter names. Make sure all are "
                msg += f"elements of {self.ecotracer_fg_param_name_prefixes}"
                raise ValueError(msg)
            return _construct_all_param_names(
                param_names, self._core_instance.get_functional_group_names()
            )
        elif isinstance(param_names, str):
            if param_names == "all":
                return self.get_ecotracer_fg_param_names(self.ecotracer_fg_param_name_prefixes)
            else:
                return self.get_ecotracer_fg_param_names([param_names])

    def _get_unset_params(self):
        return list(
            self._all_possible_params -
            set(self._constant_params) -
            set(self._variable_params)
        )

    def _get_conflicting_params(self):
        return list(set(self._constant_params) & set(self._variable_params))

    def _check_parameters(self, params: list[str]):
        if self._all_possible_params is None:
            all_params = self.get_ecotracer_fg_param_names(
                self.ecotracer_fg_param_name_prefixes
            )
            all_params.extend(self.ecotracer_env_param_names)
            self._all_possible_params = set(all_params)
        if not set(params).issubset(self._all_possible_params):
            msg = "The following elements are not valid parameters: "
            msg += str(set(params).symmetric_difference(self._all_possible_params))
            raise ValueError(msg)

    def set_constant_params(self, param_names: list[str], param_values: list[float]):
        """Set parameters that are constant scenarios"""
        self._check_parameters(param_names)
        self._constant_params = param_names
        self._init_constant_param_setup()

        for (name, val) in zip(param_names, param_values):
            self._add_constant_param(name, val)

    def _set_variable_params(self, param_names: list[str], param_df_idxs: list[int]):
        """Set parameters that change between scenarios"""
        self._check_parameters(param_names)
        self._variable_params = param_names
        self._init_variable_param_setup()

        unset = self._get_unset_params()
        if len(unset) != 0:
            msg = f"The parameters {unset} have not been set to constant or variable. "
            msg += "They will be the default EwE parameters."
            warn(msg)

        conflicted = self._get_conflicting_params()
        if len(conflicted) != 0:
            msg = f"The parameters {unset} have been set to constant and variable. "
            msg += "They will be varied during execution."
            warn(msg)

        for (param_name, df_col_idx) in zip(param_names, param_df_idxs):
            self._add_variable_param(param_name, df_col_idx)

    def _load_env_params(self, values):
        setters = [
            self._core_instance.Ecotracer.set_initial_env_concentration,
            self._core_instance.Ecotracer.set_base_inflow_rate,
            self._core_instance.Ecotracer.set_env_decay_rate,
            self._core_instance.Ecotracer.set_env_volume_exchange_loss,
        ]

        for (v, f) in zip(values, setters):
            if math.isnan(v):
                continue
            f(v)

    def _load_constant_params(self):
        cat_idx = 0
        if len(self._constant_fg_param_idxs[cat_idx]) != 0:
            self._core_instance.Ecotracer.set_initial_concentrations(
                self._constant_fg_param_values[cat_idx],
                self._constant_fg_param_idxs[cat_idx]
            )
        cat_idx = 1
        if len(self._constant_fg_param_idxs[cat_idx]) != 0:
            self._core_instance.Ecotracer.set_immigration_concentrations(
                self._constant_fg_param_values[cat_idx],
                self._constant_fg_param_idxs[cat_idx]
            )
        cat_idx = 2
        if len(self._constant_fg_param_idxs[cat_idx]) != 0:
            self._core_instance.Ecotracer.set_direct_absorption_rates(
                self._constant_fg_param_values[cat_idx],
                self._constant_fg_param_idxs[cat_idx]
            )
        cat_idx = 3
        if len(self._constant_fg_param_idxs[cat_idx]) != 0:
            self._core_instance.Ecotracer.set_physical_decay_rates(
                self._constant_fg_param_values[cat_idx],
                self._constant_fg_param_idxs[cat_idx]
            )
        cat_idx = 4
        if len(self._constant_fg_param_idxs[cat_idx]) != 0:
            self._core_instance.Ecotracer.set_metabolic_decay_rates(
                self._constant_fg_param_values[cat_idx],
                self._constant_fg_param_idxs[cat_idx]
            )
        cat_idx = 5
        if len(self._constant_fg_param_idxs[cat_idx]) != 0:
            self._core_instance.Ecotracer.set_excretion_rates(
                self._constant_fg_param_values[cat_idx],
                self._constant_fg_param_idxs[cat_idx]
            )

        self._load_env_params(self._constant_env_param_values)

    def _load_variable_params(self, scen_params: list[float]):
        cat_idx = 0
        if len(self._variable_fg_param_idxs[cat_idx]) != 0:
            self._core_instance.Ecotracer.set_initial_concentrations(
                _list_index(scen_params, self._variable_fg_param_df_idx[cat_idx]),
                self._variable_fg_param_idxs[cat_idx]
            )
        cat_idx = 1
        if len(self._variable_fg_param_idxs[cat_idx]) != 0:
            self._core_instance.Ecotracer.set_immigration_concentrations(
                _list_index(scen_params, self._variable_fg_param_df_idx[cat_idx]),
                self._variable_fg_param_idxs[cat_idx]
            )
        cat_idx = 2
        if len(self._variable_fg_param_idxs[cat_idx]) != 0:
            self._core_instance.Ecotracer.set_direct_absorption_rates(
                _list_index(scen_params, self._variable_fg_param_df_idx[cat_idx]),
                self._variable_fg_param_idxs[cat_idx]
            )
        cat_idx = 3
        if len(self._variable_fg_param_idxs[cat_idx]) != 0:
            self._core_instance.Ecotracer.set_physical_decay_rates(
                _list_index(scen_params, self._variable_fg_param_df_idx[cat_idx]),
                self._variable_fg_param_idxs[cat_idx]
            )
        cat_idx = 4
        if len(self._variable_fg_param_idxs[cat_idx]) != 0:
            self._core_instance.Ecotracer.set_metabolic_decay_rates(
                _list_index(scen_params, self._variable_fg_param_df_idx[cat_idx]),
                self._variable_fg_param_idxs[cat_idx]
            )
        cat_idx = 5
        if len(self._variable_fg_param_idxs[cat_idx]) != 0:
            self._core_instance.Ecotracer.set_excretion_rates(
                _list_index(scen_params, self._variable_fg_param_df_idx[cat_idx]),
                self._variable_fg_param_idxs[cat_idx]
            )

        env_values = [
            scen_params[idx] if idx > 0 else math.nan
            for idx in self._variable_env_param_df_idxs
        ]

        self._load_env_params(env_values)

    def run_scenarios(self, scenarios: DataFrame, save_dir: str):
        col_names: list[str] = [str(nm) for nm in scenarios.columns]
        self._load_constant_params()
        self._set_variable_params(col_names[1:], list(range(len(col_names))))

        for idx, row in tqdm(scenarios.iterrows()):
            self._load_variable_params(list(row[1:]))
            self._core_instance.Ecotracer.run()
            self._core_instance.save_ecotracer_results(
                os.path.join(save_dir, f"ecotracer_res_scen_{idx}")
            )
        return None

    def set_ecosim_group_info(self, group_info):
        return None

    def set_vulnerabilities(self, vulnerabilities):
        """Set Ecosim vulnerabilities to use for all scenario runs."""
        return None

    def set_fishing_effort(self, fishing_effort):
        return None

    def get_empty_scenarios_df(
            self, env_param_names: list[str], fg_param_names: list[str], n_scenarios: int=1
    ):
        """Given a list of ecotracer fg parameter names"""
        if not _is_valid_param_list(env_param_names, self.ecotracer_env_param_names):
            msg = "Invalid parameter names. Make sure all are "
            msg += f"elements of {self.ecotracer_env_param_names}."
            raise ValueError(msg)

        cols = self.get_ecotracer_fg_param_names(fg_param_names)
        cols.extend(env_param_names)
        empty = np.zeros((n_scenarios, len(cols) + 1))
        empty[:, 0] = np.arange(1, n_scenarios + 1)
        return DataFrame(empty, columns=["scenario_idx"].extend(cols))
