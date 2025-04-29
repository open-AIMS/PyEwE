from abc import abstractmethod
import numpy as np
from math import isnan
from typing import Union
from warnings import warn

from ..exceptions import (
    EcopathError,
    EcosimError,
    EcotracerError,
    EcosimNoScenarioError,
    EcotracerNoScenarioError,
)


def _generate_group_getter(param_container_name: str, name: str):
    """Generate getter functions for EwEParameterManager for group parameters."""

    def getter(self: EwEScenarioModel):
        self._assert_scenario_loaded()
        return [
            getattr(getattr(self._core, param_container_name)(i), name)()
            for i in range(1, self._core.nGroups + 1)
        ]

    # For Debugging
    getter.__name__ = f"set_{param_container_name}_{name}"
    getter.__qualname__ = f"<generated>.{getter.__name__}"
    return getter


def _generate_group_setter(param_container_name, name):
    """Generate getter functions for EwEParameterManager for group parameters."""

    def setter(self: EwEScenarioModel, values, idxs=None):
        self._assert_scenario_loaded()
        if idxs is None:
            self._assert_setter_list_length(list(values))
        else:
            if len(idxs) != len(values):
                msg = "Length of idxs and values should be equal. "
                msg += f"Received lengths of {len(idxs)} and {len(values)}."
                raise ValueError(msg)

        idx_range = range(1, self._core.nGroups + 1) if idxs is None else idxs
        for i, val in zip(idx_range, values):
            param_container = getattr(self._core, param_container_name)(i)
            getattr(param_container, name)(val)

    # For debugging
    setter.__name__ = f"set_{param_container_name}_{name}"
    setter.__qualname__ = f"<generated>.{setter.__name__}"
    return setter


def _generate_env_getter(param_container_name: str, name: str):
    def getter(self: EwEScenarioModel):
        self._assert_scenario_loaded()
        param_container = getattr(self._core, param_container_name)()
        return getattr(param_container, name)()

    getter.__name__ = f"get_{param_container_name}_{name}"
    getter.__qualname__ = f"<generated>.{getter.__name__}"
    return getter


def _generate_env_setter(param_container_name: str, name: str):
    def setter(self: EwEScenarioModel, value):
        self._assert_scenario_loaded()
        param_container = getattr(self._core, param_container_name)()
        return getattr(param_container, name)(value)

    # For debugging
    setter.__name__ = f"set_{param_container_name}_{name}"
    setter.__qualname__ = f"<generated>.{setter.__name__}"
    return setter


class EwEParameterManager:
    """Generic parameter manager to manage EwE Model parameters."""

    # _GROUP_PARAM_CONTAINER_NAME
    # _GROUP_PARAM_NAMES
    # _ENV_PARAM_CONTAINER_NAME
    # _ENV_PARAM_NAMES

    def __init_subclass__(cls):

        group_param_container_name = getattr(cls, "_GROUP_PARAM_CONTAINER_NAME")
        group_param_names = getattr(cls, "_GROUP_PARAM_NAMES")
        env_param_container_name = getattr(cls, "_ENV_PARAM_CONTAINER_NAME")
        env_param_names = getattr(cls, "_ENV_PARAM_NAMES")

        for param_name, (getter_name, setter_name) in group_param_names.items():
            setattr(
                cls,
                f"get_{param_name}",
                _generate_group_getter(group_param_container_name, getter_name),
            )
            setattr(
                cls,
                f"set_{param_name}",
                _generate_group_setter(group_param_container_name, setter_name),
            )

        for param_name, (getter_name, setter_name) in env_param_names.items():
            setattr(
                cls,
                f"get_{param_name}",
                _generate_env_getter(env_param_container_name, getter_name),
            )
            setattr(
                cls,
                f"set_{param_name}",
                _generate_env_setter(env_param_container_name, setter_name),
            )


class EwEModel:

    def __init__(self, core, state):
        self._core = core
        self._state = state


class EwEScenarioModel(EwEModel):
    """Abstract class to represent EwE Models that implement scenarios."""

    def __init__(self, core, state):
        super().__init__(core, state)

    @abstractmethod
    def scenario_count(self) -> int:
        """Get the number of scenarios contained in the model."""
        pass

    @abstractmethod
    def _get_scenario(self, index: int):
        """Get internal scenario object."""
        pass

    @abstractmethod
    def _load_scenario(self, index: int) -> bool:
        """Load scenario with given index into core."""
        pass

    @abstractmethod
    def _remove_scenario(self, index: int) -> bool:
        """Remove scenario with given index from core."""
        pass

    @abstractmethod
    def _assert_scenario_loaded(self):
        """Check that a scenario is loaded. Throw error is not loaded."""
        pass

    def _assert_setter_list_length(self, property: list):
        if len(property) != self._core.nGroups:
            msg = f"Expected list of length {self._core.nGroups} "
            msg += f"but received {len(property)}"
            raise EcopathError(self._state, msg)

    def _load_named_scenario(self, name: str) -> bool:
        """Load a scenario with the given name."""
        for index in range(1, self.scenario_count() + 1):
            if self._get_scenario(index).Name == name:
                return self._load_scenario(index)
        raise LookupError(f"Unable to find scenario named: {name}")

    def _load_indexed_scenario(self, index: int) -> bool:
        """Load a scenario for the given one-based index."""
        if index > self.scenario_count() or index < 1:
            msg = f"Given index {index} but there are {self.scenario_count()} scenarios"
            raise IndexError(msg)

        return self._load_scenario(index)

    def load_scenario(self, identifier: Union[str, int]) -> bool:
        """Load a scenario into the core object.

        Args:
            identifier (Union[str, int]): Index or name of already existing scenario

        Returns:
            bool: success or failure

        Raises:
            IndexError: The provided index was out of bounds.
            TypeError: The provided identifier was not a string or integer.
        """
        if isinstance(identifier, str):
            return self._load_named_scenario(identifier)
        elif isinstance(identifier, int):
            return self._load_indexed_scenario(identifier)
        else:
            raise TypeError(f"Unsupported type: {type(identifier)}")

    @abstractmethod
    def new_scenario(
        self, name: str, description: str, author: str, contact: str
    ) -> bool:
        """Add a new scenario"""
        pass

    @abstractmethod
    def close_scenario(self):
        """Close current ecotracer scenario."""
        pass

    def _remove_named_scenario(self, name: str) -> bool:
        """Load a scenario with the given name."""
        for index in range(1, self.scenario_count() + 1):
            if self._get_scenario(index).Name == name:
                return self._remove_scenario(index)
        raise LookupError(f"Unable to find scenario named: {name}")

    def _remove_indexed_scenario(self, index: int) -> bool:
        """Load a scenario for the given one-based index."""
        if index > self.scenario_count() or index < 1:
            msg = f"Given index {index} but there are {self.scenario_count()} scenarios"
            raise IndexError(msg)

        return self._remove_scenario(index)

    def remove_scenario(self, identifier: Union[str, int]) -> bool:
        """Remove a scenario from the core object.

        Args:
            identifier (Union[str, int]): Index or name of already existing scenario

        Returns:
            bool: success or failure

        Raises:
            IndexError: The provided index was out of bounds.
            TypeError: The provided identifier was not a string or integer.
        """
        if isinstance(identifier, str):
            return self._remove_named_scenario(identifier)
        elif isinstance(identifier, int):
            return self._remove_indexed_scenario(identifier)
        else:
            raise TypeError(f"Unsupported type: {type(identifier)}")

    @abstractmethod
    def run(self) -> bool:
        """Run the model."""
        pass


class EcosimStateManager(EwEScenarioModel, EwEParameterManager):
    """Ecosim Model State Wrapper

    This should be the interface at which Ecosim information is set and retrieved.
    Parameter setting, results extraction and scenario loading should be controlled via this
    class.
    """

    _GROUP_PARAM_CONTAINER_NAME = "get_EcosimGroupInputs"
    _GROUP_PARAM_NAMES = {
        "density_dep_catchability": (
            "get_DenDepCatchability",
            "set_DenDepCatchability",
        ),
        "feeding_time_adj_rate": (
            "get_FeedingTimeAdjustRate",
            "set_FeedingTimeAdjustRate",
        ),
        "max_rel_feeding_time": ("get_MaxRelFeedingTime", "set_MaxRelFeedingTime"),
        "max_rel_pb": ("get_MaxRelPB", "set_MaxRelPB"),
        "pred_effect_feeding_time": (
            "get_PredEffectFeedingTime",
            "set_PredEffectFeedingTime",
        ),
        "other_mort_feeding_time": (
            "get_OtherMortFeedingTime",
            "set_OtherMortFeedingTime",
        ),
        "qbmax_qbio": ("get_QBMaxQBio", "set_QBMaxQBio"),
        "switching_power": ("get_SwitchingPower", "set_SwitchingPower"),
    }
    _ENV_PARAM_CONTAINER_NAME = "get_EcosimModelParameters"
    _ENV_PARAM_NAMES = {
        "n_years": ("get_NumberYears", "set_NumberYears"),
    }

    def __init__(self, core, state):
        super().__init__(core, state)

    def scenario_count(self):
        return self._core.nEcosimScenarios

    def _get_scenario(self, index: int):
        return self._core.get_EcosimScenarios(index)

    def _load_scenario(self, index: int) -> bool:
        return self._core.LoadEcosimScenario(index)

    def _remove_scenario(self, index: int) -> bool:
        return self._core.RemoveEcosimScenario(index)

    def _assert_scenario_loaded(self):
        if not self._state.HasEcosimLoaded():
            raise EcosimNoScenarioError(self._state)

    def new_scenario(self, name: str, description: str, author: str, contact: str):
        """Create a new Ecosim scenario."""
        return self._core.NewEcosimScenario(name, description, author, contact)

    def close_scenario(self):
        return self._core.CloseEcosimScenario()

    def run(self):
        """Run the ecosim model without ecotracer and return whether it was successful."""
        is_balanced: bool = self._core.IsModelBalanced
        if not is_balanced:
            warn("Ecopath model is not balanced.")

        if not self._core.RunEcopath():
            warn("Ecopath failed to run.")
            return False

        if not self._state.HasEcosimLoaded():
            raise EcosimError(self._state, "Ecosim scenario is not loaded")

        successful: bool = self._core.RunEcosim()

        if not successful:
            print("EcoSim with Ecotracer run failed.")

        return successful

    def set_vulnerabilities(self, vulnerabilities: np.ndarray):
        """Set ecosim vulnerabilites from a vulnerability matrix."""
        # Assume correct shape is checked before hand.
        for prey_idx in range(1, self._core.nGroups + 1):
            prey_ecosim_input = self._core.get_EcosimGroupInputs(prey_idx)
            for pred_idx, val in enumerate(vulnerabilities[prey_idx - 1, :]):
                if isnan(val):
                    continue

                prey_ecosim_input.set_VulMult(pred_idx + 1, val)


class EcotracerStateManager(EwEScenarioModel, EwEParameterManager):
    """Ecotracer Model State Wrapper

    This should be the interface at which Ecotracer information is set and retrieved.
    Parameter setting, results extraction, scenario loading and ecotracer execution should
    be controlled via this class.
    """

    # See file gridEcotracerInput.vb in the ScientificInterface directory of Ecopath6.
    # Direct Absorption rates -> CEnvironment
    # excretion rates -> AssimilationProp
    _GROUP_PARAM_CONTAINER_NAME = "get_EcotracerGroupInputs"
    _GROUP_PARAM_NAMES = {
        "initial_concentrations": ("get_CZero", "set_CZero"),
        "immigration_concentrations": ("get_CImmig", "set_CImmig"),
        "direct_absorption_rates": ("get_CEnvironment", "set_CEnvironment"),
        "physical_decay_rates": ("get_CDecay", "set_CDecay"),
        "metabolic_decay_rates": ("get_CMetablismRate", "set_CMetablismRate"),
        "excretion_rates": ("get_CAssimilationProp", "set_CAssimilationProp"),
    }

    _ENV_PARAM_CONTAINER_NAME = "get_EcotracerModelParameters"
    _ENV_PARAM_NAMES = {
        "initial_env_concentration": ("get_CZero", "set_CZero"),
        "base_inflow_rate": ("get_CInflow", "set_CInflow"),
        "env_decay_rate": ("get_CDecay", "set_CDecay"),
        "env_volume_exchange_loss": ("get_COutflow", "set_COutflow"),
    }

    def __init__(self, core, state):
        super().__init__(core, state)

    def scenario_count(self) -> int:
        return self._core.nEcotracerScenarios

    def _get_scenario(self, index: int):
        return self._core.get_EcotracerScenarios(index)

    def _load_scenario(self, index: int):
        # Make sure ecosim scenario is loaded before ecotracer.
        if not self._state.HasEcosimLoaded():
            raise EcosimNoScenarioError(self._state)
        return self._core.LoadEcotracerScenario(index)

    def _remove_scenario(self, index: int):
        return self._core.RemoveEcotracerScenario(index)

    def _assert_scenario_loaded(self):
        if not self._state.HasEcotracerLoaded():
            raise EcotracerNoScenarioError(self._state)

    def new_scenario(self, name: str, description: str, author: str, contact: str):
        """Create a new EcoTracer scenario."""
        return self._core.NewEcotracerScenario(name, description, author, contact)

    def close_scenario(self):
        return self._core.CloseEcotracerScenario()

    def run(self) -> bool:
        """Run the ecosim model with ecotracer and return whether it was successful"""
        is_balanced: bool = self._core.IsModelBalanced
        if not is_balanced:
            warn("Ecopath model is not balanced.")

        if not self._core.RunEcopath():
            warn("Ecopath failed to run.")
            return False

        if not self._state.HasEcosimLoaded():
            raise EcosimError(self._state, "Ecosim scenario is not loaded")

        if not self._state.HasEcotracerLoaded():
            raise EcotracerError(self._state, "Ecotracer scenario is not loaded.")

        self._core.EcosimModelParameters.ContaminantTracing = True
        successful: bool = self._core.RunEcosim()

        if not successful:
            print("EcoSim with Ecotracer run failed.")

        return successful
