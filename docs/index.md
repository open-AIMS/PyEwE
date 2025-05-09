# decom_py

Welcome to `decom_py`! This tool utilizes [Ecopath with Ecosim](https://ecopath.org/) to explore a wide range of contaminant release and decommissioning scenarios.

This documentation provides guidance on setup, usage, and development.

Supports **Ecopath with Ecosim v6.7**.

## Setup

1.  **Download Ecopath with Ecosim:**
    Obtain [Ecopath with Ecosim v6.7](https://ecopath.org/downloads/#toggle-id-1) and note the installation path (the directory containing `EwECore.dll`).

2.  **Install Python Environment Manager:**
    We recommend [uv](https://docs.astral.sh/uv/#__tabbed_1_2) for managing Python versions and dependencies. Install it if you haven't already. Restart your terminal after installation.

3.  **Install Project Dependencies:**
    Navigate to the `decom_py` project directory in your terminal and run:
    ```bash
    uv sync
    ```
    This command installs all necessary Python packages specified in the project configuration.

4.  **Set Environment Variable:**
    Add an environment variable `EWE_BIN_PATH` that points to the directory containing the EwE binaries (e.g., where `EwECore.dll` is located).

    **Powershell (Windows):**
    ```powershell
    $env:EWE_BIN_PATH="C:\Path\To\Your\EwE\Binaries"
    ```
    To make this permanent, you can add it to your PowerShell profile or set it through the System Properties dialog.

    **bash (Linux/macOS):**
    ```bash
    export EWE_BIN_PATH="/path/to/your/ewe/binaries"
    ```
    To make this permanent, add the `export` command to your shell's configuration file (e.g., `~/.bashrc`, `~/.zshrc`).

    The library will attempt to automatically initialize with this path. If this variable is not set, or you need to use a different path at runtime, you can call the `initialise()` function manually in your Python script.

## Quick Links

*   See [Usage](usage.md) for a guide on how to use the library with examples.
*   Explore the [API Reference](api/reference.md) for detailed information on classes and functions.
*   For developers, the [Development Notes](development.md) provide insights into the library's internals and setup for contribution.
