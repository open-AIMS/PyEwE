from abc import abstractmethod
from typing import Union
from warnings import warn
from .Exceptions import EwEError, EcopathError, EcosimError, EcotracerError

class EwEModel:

    def __init__(self, core, state):
        self._core = core
        self._state = state

class EwEScenarioModel(EwEModel):
    """Abstract class to represent EwE Models that implement scenarios.
    """

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
    def _remove_scenario(self, index:int) -> bool:
        """Remove scenario with given index from core."""
        pass

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
    def new_scenario(self, name: str, description: str, author: str, contact: str) -> bool:
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

class EcosimStateManager(EwEScenarioModel):
    """Ecosim Model State Wrapper

    This should be the interface at which Ecosim information is set and retrieved.
    Parameter setting, results extraction and scenario loading should be controlled via this
    class.
    """

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

class EcotracerStateManager(EwEScenarioModel):
    """Ecotracer Model State Wrapper

    This should be the interface at which Ecotracer information is set and retrieved.
    Parameter setting, results extraction, scenario loading and ecotracer execution should
    be controlled via this class.
    """

    def __init__(self, core, state):
        super().__init__(core, state)

    def scenario_count(self) -> int:
        return self._core.nEcotracerScenarios

    def _get_scenario(self, index: int):
        return self._core.get_EcotracerScenarios(index)

    def _load_scenario(self, index: int):
        return self._core.LoadEcotracerScenario(index)

    def _remove_scenario(self, index: int):
        return self._core.RemoveEcotracerScenario(index)

    def new_scenario(self, name: str, description: str, author: str, contact: str):
        """Create a new EcoTracer scenario."""
        print(description)
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
