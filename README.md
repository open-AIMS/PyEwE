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

ewe_int.run_scenarios(scen_df, "path to save dir")
```

## Developer setup

Additional packages for a development environment can be added:

```bash
uv add --dev <name of package>
```

These packages will not be included in the package dependencies and are only installed
locally.

### Documentation

Documentation can be build and read using 

```bash
mkdocs serve
```

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

### Testing

1. Define an environment variable pointing to the EwE binaries.

**Powershell**
```Powershell
$env:EWE_BIN_DIR_PATH="Path to EwE binaries"
```

**bash**
```bash
export ENV_BIN_DIR_PATH="Path to EwE binaries"
```

2. Run tests with `pytest`

```bash
uv run --dev pytest
```

For more information, add `-v`. To suppress "Windows fatal exception: access violation",
set `-p no:faulthandler`
```bash
uv run --dev pytest -p no:faulthandler -v
```

---

If you use an IDE test runner, you can specify the environment variable in a `.env` file,
which pytest will discover:

```
EWE_BIN_DIR_PATH=c:\\Program Files\\Ecopath with Ecosim 40 years 6.7.0.18865_64-bit
```

For VSCode test runner, go through pytest setup in the Testing left panel, or search
 Settings (Workspace) for "pytest". Your _.vscode/settings.json_ file should look like this:

```json
{
    "terminal.integrated.env.windows": {
        "EWE_BIN_DIR_PATH": "c:\\Program Files\\Ecopath with Ecosim 40 years 6.7.0.18865_64-bit"
    },
    "python.testing.pytestArgs": [
        "test",
        "-v",
        "-p no:faulthandler"
    ],
    "python.testing.unittestEnabled": false,
    "python.testing.pytestEnabled": true
}
```
