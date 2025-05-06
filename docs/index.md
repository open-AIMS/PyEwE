# decom_py

A tool using [Ecopath with Ecosim](https://ecopath.org/) to explore a wide range of
contaminant release scenarios.

Supports [Ecopath with Ecosim v6.7](https://ecopath.org/downloads/#toggle-id-1).

## Setup

Download [Ecopath with Ecosim v6.7](https://ecopath.org/downloads/#toggle-id-1) and record
the installation path.

Install [uv](https://docs.astral.sh/uv/#__tabbed_1_2) to manage python version and
dependecies.

Navigate to the project directory and run:

```bash
uv sync
```

Add a `EWE_BIN_PATH` environment variable with with a path to the directory of the EwE
binaries.

**Powershell**
```Powershell
$env:EWE_BIN_DIR_PATH="Path to EwE binaries"
```

**bash**
```bash
export ENV_BIN_DIR_PATH="Path to EwE binaries"
```

See [Usage](usage.md#usage) to understand how to use the library.
