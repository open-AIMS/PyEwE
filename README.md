# decom_py

A tool using [Ecopath with Ecosim](https://ecopath.org/), to explore a wide range of
decomissioning scenarios.

## Example

```python
from decom_py import EwE

ewe = EwE("path to EwE dll directory.", "path to result save dir")

model_file = "path to model file"
ewe.load_model(model_file)

ewe.run_ecopath()
ewe.load_ecosim_scenario(0)
ewe.load_ecotracer_scenario(0)

if not ewe.run_ecosim():
    print("Failed to run ecosim.")

ewe.save_ecopath_results()
if not ewe.save_ecosim_results("directory to save ecosim results"):
    print("Failed to save ecosim results")

ewe.core().CloseModel()

```

### Debugging

```python
from decom_py import EwE, EwEState
ewe = EwE("path to dlls")

# ... code running models

state = EwEState(ewe.core())
state.print_summary()

# Possible output
# ---- Complate State Summary ----
# 
# ---- EwE State ----
# CanEcopathLoad: True
# CanEcosimLoad: True
# CanEcospaceLoad: True
# CanEcotracerLoad: True
# 
# ---- Ecopath State ----
# HasEcopathInitialized: True
# HasEcopathLoaded: True
# HasEcopathRan: True
# IsEcopathRunning: False
# IsEcopathModified: False
# 
# ---- Ecosim State ----
# HasEcosimInitialized: False
# HasEcosimLoaded: True
# HasEcosimRan: False
# IsEcosimRunning: False
# IsEcosimModified: False
# 
# ---- EcoTracer State ----
# HasEcotracerLoaded: True
# HasEcotracerRanForEcosim: False
# HasEcotracerRanForEcospace: False
# IsEcotracerModified: False

# ... more code running models
```
