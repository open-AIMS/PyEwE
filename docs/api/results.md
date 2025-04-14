# Results

## Ecosim

Ecosim results can be saved using the `CoreInterface` object.

```
# ... imports

initialise('path/to/binaries')
core = CoreInterface()

# ... load scenarios and run models

core.save_ecosim_results('path/to/save/dir', ["Variables", "to", "save"])
```

The possible variables are:

- `"Biomass"`
- `"ConsumptionBiomass"`
- `"PredationMortality"`
- `"Mortality"`
- `"FeedingTime"`
- `"Prey"`
- `"Catch"`
- `"Value"`
- `"AvgWeightOrProdCons"`
- `"TL"`
- `"TLC"`
- `"KemptonsQ"`
- `"ShannonDiversity"`
- `"FIB"`
- `"TotalCatch"`
- `"CatchFleetGroup"`
- `"MortFleetGroup"`
