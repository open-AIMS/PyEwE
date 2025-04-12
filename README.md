# decom_py

A tool using [Ecopath with Ecosim](https://ecopath.org/), to explore a wide range of
decomissioning scenarios.

## Setup

Install [uv](https://docs.astral.sh/uv/#__tabbed_1_2) to manage python versions and
dependencies.

Once installed, restart the terminal for changes to take effect.

Navigate to the project directory and run:

```bash
uv sync
```

This will install needed dependencies.

## Developer setup

Additional packages for a development environment can be added:

```bash
uv add --dev <name of package>
```

These packages will not be included in the package dependencies and are only installed
locally.

### Jupyter notebooks

To setup a ipykernel:

Linux:

```bash
uv run ipython kernel install --user --env VIRTUAL_ENV $(pwd)/.venv --name=decom_py
```

For Powershell:

```bash
uv run ipython kernel install --user --env VIRTUAL_ENV "$((Get-Location).Path)\.venv" --name=decom_py
```

The appropriate kernel can then be selected in Jupyter Notebook.

### Useful IPython magic commands

When developing in a Jupyter notebook or in IPython, it is useful for code to be
hot-reloaded after changing the code. To enable this, use the autoreload extension.

```bash
%load_ext autoreload
%autoreload 2
```

The number `2` in the example above autoreloads all modules.

See [here](https://ipython.readthedocs.io/en/stable/config/extensions/autoreload.html#magic-autoreload)
for more information.

## Example

```python
from decom_py import CoreInterface, EwEState, initialise

initialise("C:/Program Files/Ecopath with Ecosim 40 years 6.7.0.18865_64-bit")
core = CoreInterface()

core.set_default_save_dir("./Outputs/")

model_file = "C:/Users/dtan/data/Decommissioning/Past_Ecopath/GippslandBasin/East Bass Strait.eweaccdb"
core.load_model(model_file)

core.load_ecosim_scenario(1)


if not core.load_ecotracer_scenario(1):
    print("Failed to load ecotracer scenario.")

if not core.run_ecosim_w_ecotracer():
    print("Failed to run ecosim.")

core.save_ecopath_results()
core.save_ecosim_results("Outputs/ecosim_res")

if not core.save_ecotracer_results():
   print("Failed to save ecotracer results.")

core.close_model()
```

### Debugging

```python
from decom_py import CoreInterfacea, EwEState

initialise("path to ewe binary directory")

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
