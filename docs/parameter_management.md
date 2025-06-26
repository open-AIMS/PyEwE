# Parameter Management

Currently, the parameter management object only supports Ecotracer. However, can be extended
by defining an Ecosim factory method similar to the Ecotracer implementation. The parameter
managers using the naming of parameters passed to the managers to decide which setter
functions to call and for which functional group it shoould be set.

## Parameter Naming

Ecotracer parameters are split into two groups, environmental parameters and group
parameters. EwE-py using different naming conventions for each with environmantal parameters
being much simpler.

### Environmental Parameters

Environmantal Parameters are named as follows,

- `env_init_c`: Initial environmental contaminant concentration.
- `env_base_inflow_r`: Base contaminant infrow rate.
- `env_decay_r`: Environmental contaminant decay rate.
- `base_vol_ex_loss`: Base environmental volume exchange loss.
- `env_inflow_forcing_idx`: Index of the inflow forcing function to use.

### Group Ecotracer Parameters

There are six types of ecotracer group parameters with the following prefixes,

- `init_c`: Group initial contaminant concentration.
- `immig_c`: Group immigration contaminant concentration
- `direct_abs_r`: Group direct absorption rate.
- `phys_decay_rate`: Physical decay rate.
- `meta_decay_r`: Metabolic decay rate.
- `excretion_r`: Excretion rate.

Then the full name of a ecotracer is structered as follows,

`<prefix>_<group_index>_<group_name>`.

For example, if `Baleen Whale` is the first functional group in the model and there is
between 10 and 99 functional groups, then the parameter for the Baleen Whale's initial 
contaminant concentration would be `init_c_01_Baleen Whale`.

## Management

The Ecotracer Parameter manager provides a simpler way to set parameter other then using the
getter and setters in the Ecotracer object. The manager provides two ways to set parameters
within the core. **Constant** parameters need to be set with the name of the parameter and
the values, whilst **variable** parameters accept names of parameters and indices of
parameter values into any future list that may be passed. The idea being that strings don't
need to parsed everytime parameters are set.

### Initialisation

```julia
core = CoreInterface()
# A model must be loaded before the parameter manager is initialised.
core.load_model("path/to/model/database")

parameter_manager = EcotracerManager(core)
```

### Setting Parameters

```julia
const_param_names = ["name", "of", "params"]
const_param_values = [value, of, params]
# Configure the constant params within the parameter manager.
parameter_manager.set_constant_params(const_param_names, cosnt_param_values)
# Write the parameter into the core model.
parameter_manager.apply_constant_params(core)
```

Variable parameters are intended for parameters that will changed frequently. Consider the
situation where the parameter for different scenario are contained in a data frame, where
the columns are the data frame.

```julia
import pandas as pd
# Params has columns ["scenario", "param_1", "param_2", ...]
params = pd.read_csv("scenario_params.csv")

# Remove scenario columns
param_names = list(params.columns)[1:]
param_idxs = list(range(len(param_names)))
parameter_manager.set_variable_params(param_names, param_idxs)

for (i, row) in params.iterrows():
    # Set parameters without processing strings in each iteration.
    parameter_manager.apply_variable_params(core, list(row[1:]))
    # Run model ...
    # Collect results ...
```
