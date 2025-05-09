# Usage Guide

`decom_py` is a tool designed to interface with [Ecopath with Ecosim](https://ecopath.org/), enabling the exploration of various decommissioning and contaminant release scenarios.

## Example

Here's a typical workflow for using `decom_py`:

```python
import pandas as pd
from decom_py import EwEScenarioInterface, initialise

# If EWE_BIN_PATH is not set as an environment variable, or to override it:
# You must call initialise() with the path to the EwE binaries directory.
# initialise(r'path/to/your/EwE/binaries/directory')
# If EWE_BIN_PATH is set, initialisation happens automatically on import.

# Path to your EwE model file (e.g., .EwEaccdb)
model_file = r'path/to/your/model/file.EwEaccdb' # IMPORTANT: Replace with your actual model file path

# Initialize the scenario interface with your model
ewe_int = EwEScenarioInterface(model_file)

# --- Optional: Configure Ecosim Parameters ---
# If your scenarios involve changes to standard Ecosim parameters, set them here.
# Example: Load Ecosim group info and vulnerabilities from CSV files
# ecosim_group_info = pd.read_csv('path/to/your/ecosim_group_info.csv')
# ecosim_vulnerabilities = pd.read_csv('path/to/your/ecosim_vulnerabilities.csv')
# ewe_int.set_ecosim_group_info(ecosim_group_info)
# ewe_int.set_ecosim_vulnerabilities(ecosim_vulnerabilities)

# Set simulation duration (e.g., 75 years)
ewe_int.set_simulation_duration(n_years=75)

# --- Define Scenario Parameters ---
# Specify the Ecotracer environmental parameters to include in your scenario DataFrame
ecotracer_env_params = [
    "env_init_c",          # Initial environmental concentration
    "env_base_inflow_r",   # Base environmental inflow rate
    "env_decay_r",         # Environmental decay rate
    "base_vol_ex_loss"     # Base volume exchange loss
]

# Specify Ecotracer functional group parameter *prefixes* for the scenario DataFrame
# These prefixes correspond to different types of parameters for each functional group.
# For example, to vary initial concentrations and direct absorption rates:
ecotracer_fg_prefixes = ["init_c", "direct_abs_r"]
# To include all available Ecotracer functional group parameters, use "all":
# ecotracer_fg_prefixes = "all"

# Create an empty DataFrame structured for your scenarios
num_scenarios = 100
scen_df = ewe_int.get_empty_scenarios_df(
    env_param_names=ecotracer_env_params,
    fg_param_names=ecotracer_fg_prefixes, # List of prefixes or "all"
    n_scenarios=num_scenarios
)

# --- Populate Scenario DataFrame ---
# Fill `scen_df` with the actual parameter values for each scenario.
# The columns will be 'scenario' (index), followed by your specified env_param_names,
# and then the full functional group parameter names generated from fg_param_names (e.g., 'init_c_01_GroupName').

# Example: Set a constant value for 'env_init_c' across all scenarios
# scen_df['env_init_c'] = 0.1

# Example: Set 'init_c' for the first functional group (assuming its name is known or indexed)
# Adjust column name based on your model's actual functional group names.
# You can inspect `scen_df.columns` to see the generated parameter names.
# if 'init_c_01_Phytoplankton' in scen_df.columns: # Replace with actual FG name
#     scen_df['init_c_01_Phytoplankton'] = 0.05
# else:
#     print("Warning: Example FG parameter column not found. Populate scen_df manually.")

# Make sure your scenario DataFrame is correctly populated.
# For demonstration, let's assume it's filled appropriately.
# Replace this with your actual scenario setup logic.
for col in scen_df.columns:
    if col == 'scenario':
        scen_df[col] = range(num_scenarios)
    elif pd.api.types.is_numeric_dtype(scen_df[col]):
        scen_df[col] = pd.Series(index=scen_df.index, data=[(i % 10) * 0.01 for i in range(num_scenarios)])


# --- Run Scenarios ---
# Run scenarios sequentially
print("Running scenarios sequentially...")
results = ewe_int.run_scenarios(scen_df)

# Alternatively, run scenarios in parallel
# num_workers = os.cpu_count() # Or a specific number
# print(f"Running scenarios in parallel with {num_workers} workers...")
# results = ewe_int.run_scenarios_parallel(scen_df, n_workers=num_workers)

# --- Save and Access Results ---
# Define where to save the output files
results_output_dir = "path/to/save/your/results" # IMPORTANT: Replace with your desired output directory
import os
os.makedirs(results_output_dir, exist_ok=True)

# Save results to NetCDF and CSV formats
results.save_results(results_output_dir, ["netcdf", "csv"])
print(f"Results saved to {results_output_dir}")

# Access specific result variables (as xarray.DataArray)
# biomass_results = results["Biomass"]
# concentration_results = results["Concentration"]
# print("\nBiomass results (first 5 time steps, first group, first scenario):")
# print(biomass_results.isel(Time=slice(0, 5), Group=0, Scenario=0))

# --- Cleanup ---
# Clean up temporary directory and model file copy
ewe_int.cleanup()
print("Cleanup complete.")
