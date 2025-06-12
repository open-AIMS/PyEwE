# High Level Interface

EwE-py provides a high level interface where users can execute a large number of scenarios
runs and execute in parallel. EwE-py exports this functionality through the
`EwEScenarioInterface` class.

## Usage

Before preceeding see the [Setup Instructions](index.md#setup) for how to install
requirements and link the EwE binaries.

### Initialisation

```python
from decom_py import EwEScenarioInterface 

model_path = "<Path to Model Database>"

ewe_int = EwEScenarioInterface(model_path)
```

### Setting up Ecosim

EwE-py does not currently support changing ecosim parameters between scenario runs. Ecosim
scenario parameters can be set via two methods. Using the same csv formats as the EwE GUI
exports, dataframes can be passed to the scenario interface

```python
vulnerabilities = pd.read_csv("Path to Vulnerabilities")
ecosim_group_info = pd.read_csv("Path to Ecosim Group Info")

ewe_int.set_ecosim_group_info(ecosim_group_info)
ewe_int.set_ecosim_vulnerabilities(vulnerabilities)
```

The EwE GUI can also be used. Simply edit an ecosim scenario with the EwE GUI and pass the
name of the ecosim scenario during the initialisation of the interface object.

```python
ewe_int = EwEScenarioInterface(model_path, "name of ecosim scenario")
```
**The name of the ecosim scenario must be unique.**

### Setting up Ecotracer Scenarios

Before preceeding see [Parameter Management](parameter_management.md#Parameter-naming) for 
naming conventions.

#### Constants

EwE-py will set the constant parameters prior to scenario runs and not change them.

```python
param_names = ["list of param names"]
param_values = [list, of, param, values]

ewe_int.set_constant_params(param_names, param_values)
```

#### Running Scenarios

Parameters that are varied during execution must be passed to the `run_scenarios` or
`run_scenarios_parallel` function as the columns of a dataframe.

```python
varied_param_names = ["list of parameter names"]


scenario_dataframe = ...

# The Scenario DataFrame must have the following column names
assert scenario_dataframe.columns[0] = "Scenario"
assert scenario_dataframe.columns[1:] = varied_param_names
```

Then scenario runs can be executed as follows,

```python
results = ewe_int.run_scenarios(
    scenario_dataframe, 
    save_vars=["Concentration", "Biomass", ...],
    show_progress=True
)

# Or with parallel processing
results = ewe_int.run_scenarios_parallel(
    scenario_dataframe, 
    n_workers=22,
    save_vars=["Concentration", "Biomass", ...],
    show_progress=True
)

results.save_results("path to save dir", formats=["netcdf"])
```
See the [Results Section](api/results.md) for more information on interacting with results.

## API

See [API](api/reference.md#API-reference) for a complete documentation for class fields and
methods.
