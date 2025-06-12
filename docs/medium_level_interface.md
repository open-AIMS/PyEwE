# Medium Level Interface

EwE-py wraps the underlying core library to allow the a tighter control of the core EwE
object. This wrapper more closely follows the object structures defined in the underlying
EwE libraries with some slight restructuring for added convenience. The class is called
`CoreInterface` and contains `Ecosim` and `Ecotracer` State Managers to control the current
parameterisation of the model. This object is useful when being have to setup
parallelisation scripts or more custom computations.

**Using this interface will potentially alter the underlying database.**

## Initilisation

The core object does not accept a model path as a constructor input and instead
initialisation generic instance that can load any model. However, a model should be loaded
to access the functionality of the model.

```python
from ewe_py import CoreInterface
core = CoreInterface()

core.load_model("path to model database")
```

## Loading scenarios

Scenario can be added, loaded and deleted using the model state managers.

```python
core.Ecosim.new_scenario("name", "description", "author", "contact")
core.Ecosim.remove_scenario("<Name or index of scenario>")
core.Ecosim.load_scenario("<Name or index of scenario>")
core.Ecosim.save_scenario()
core.Ecosim.save_scenario_as()

# Save scenario as and description are broken for ecotracer.
core.Ecotracer.new_scenario("name", "description", "author", "contact")
...
```

## Parameter Setting

Setters and getters for parameter are generated for the state managers. For functional group
parameters, you set the parameterisation by passing the index of the groups you want to set
and the value of the groups.

```python
core.Ecotracer.set_initial_concentrations([list, of, values], [index, of, groups])
core.Ecotracer.get_initial_concentrations()
```

**To do: List all possible getters and setters.**

## Parameter Management

Parameter setting for Ecotracer is much easier to do using the Parameter Manager. Following
the naming conventions as documented in the [Parameter Management
Section](parameter_management.md#parameter-naming), users can setup a parameter manager as
follows.

```python
from ewe_py import ParameterManager
manager = EcotracerManager(core)

# Define which params will stay constant
manager.set_constant_params(["list of names"], [list, of, values])
# Write constant params to core object.
manager.apply_constant_params()

# The set variable params accepts indexes into a future list of parameters
manager.set_variable_params(["list of names"], [list, of, indexes])

# changing params in the future.
manager.apply_variable_params([list, of, values])
```
