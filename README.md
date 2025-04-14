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

### Docstrings

The docstrings follow the [Google Python style guide](https://google.github.io/styleguide/pyguide.html).

[Black](https://github.com/psf/black) is used for code formatting.

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
core.save_all_ecosim_results("ecosim/save/dir")

core.save_ecotracer_results()

core.close_model()
```

### Debugging

```python
from decom_py import CoreInterfacea, EwEState

initialise("path to EwE binary directory")

core = CoreInterface()

# ... code running models

core.print_summary()

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
