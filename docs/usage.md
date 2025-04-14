# Usage

A tool using [Ecopath with Ecosim](https://ecopath.org/), to explore a wide range of
decomissioning scenarios.

## Example

```python
from decom_py import CoreInterface, EwEState, initialise

initialise(r'path/to/EwE/binaries/directory')
core = CoreInterface()

core.set_default_save_dir('default/save/dir')

model_file = r'path/to/model/file'
core.load_model(model_file)

core.load_ecosim_scenario(1)
core.load_ecotracer_scenario(1)

core.run_ecosim_w_ecotracer()

core.save_ecopath_results()

# Save specific ecosim result variables
be_quiet = True
save_monthly = False
core.save_ecosim_results(
    '<path/to/save/dir>', ["Variables", "to", "save"], save_monthly, be_quiet
)

# or save result variables to a given directory
core.save_all_ecosim_results('ecosim/save/dir')

core.save_ecotracer_results()

core.close_model()
```

### Debugging

```python
from decom_py import CoreInterfacea, EwEState

initialise('path to ewe binary directory')

core = CoreInterface()

# ... code running models

state = core._state
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
