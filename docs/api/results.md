# Results Handling

This section describes how results are managed and can be accessed or saved. The primary way to interact with results is through the `ResultSet` object returned by `EwEScenarioInterface.run_scenarios()` or `run_scenarios_parallel()`.

## `ResultSet` Object

The `ResultSet` object (class `decom_py.results.ResultSet`) holds all the outputs from your scenario runs. You can access individual variables as `xarray.DataArray` objects.

```python
# Assuming 'results' is a ResultSet object from ewe_int.run_scenarios(scen_df)

# Access Biomass results
biomass_data = results["Biomass"]

# Access Concentration results
concentration_data = results["Concentration"]

# 'biomass_data' and 'concentration_data' are xarray.DataArrays
# You can use xarray's powerful indexing and computation features
# For example, get biomass for the first scenario, first group, all time steps:
# specific_biomass = biomass_data.sel(Scenario=0, Group='NameOfFirstGroup')
