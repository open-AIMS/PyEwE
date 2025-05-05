# Usage

A tool using [Ecopath with Ecosim](https://ecopath.org/), to explore a wide range of
decomissioning scenarios.

## Example

```python
from decom_py import EwEScenarioInterface

initialise(r'path/to/EwE/binaries/directory')

model_file = r'path/to/model/file'
ewe_int = EwEScenarioInterface(model_file)

ecosim_group_info = pd.read_csv('path to ecosim group info.csv')
ecosim_vulnerabilities = pd.read_csv('path to ecosim vulnerabilities.csv')

ewe_int.set_ecosim_group_info(ecosim_group_info)
ewe_int.set_ecosim_vulnerabilities(ecosim_vulnerabilities)

ecotracer_param_names = ewe_int.get_fg_param_names()
ecotracer_env_params = [
    "env_init_c",
    "env_base_inflow_r",
    "env_decay_r",
    "base_vol_ex_loss"
]
scen_df = ewe_int.get_empty_scenarios_df(
    ecotracer_env_params, # environmental parameters
    ecotracer_param_names # functional group parameters
    100, # number of scenarios
)

# ... setup scenarios

res = ewe_int.run_scenarios(scen_df)

# Save results to a given directory given the list of formats.
res.save_dir("path to save dir", ["netcdf", "csv"])

# Access result variables
res["Biomass"]

res["Concentration"]

# Clean up temporary directory and model file
ewe_int.cleanup()
```
