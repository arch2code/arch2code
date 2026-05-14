---
name: manage-build
description: Guide for building, simulating, creating implementation file scaffolds, and managing the arch2code project using make targets
---
# Skill: Manage Build

## Purpose
Guide the user on how to build, simulate, and manage the project using the `make` system, adhering to the standard workflow.

## Instructions

1.  **Standard Targets:**
    *   `make gen`: Generates all code (RTL headers, SystemC wrappers, etc.) from the architecture YAML. **Run this first after any YAML change.**
    *   `make db`: Loads the project configuration and architecture into the database. Useful for validation without full generation.
    *   `make clean`: Cleans generated files and build artifacts.
    *   `make help`: Lists available targets.
    *   `make`: Runs full build with just the model
    *   `make VL_DUT=1`: Runs full build with model and RTL

2.  **Module and Implementation File Creation:**
    *   Use `make newmodule` before creating any implementation file (`.sv`, `.cpp`, `.h`) that arch2code should scaffold.
    *   This applies to new blocks and to existing blocks that are gaining a previously skipped artifact, such as changing `hasRtl: false` to `hasRtl: true`.
    *   `make newmodule` creates the directory structure, initial YAML when needed, and implementation skeletons in `model/`, `rtl/`, and related generated locations.
    *   Do not use a direct file write for these scaffolds. Edit only the user-owned body regions after `make newmodule` and `make gen` have produced the file.

3.  **Simulation:**
    *   `make run`: Runs the compiled SystemC simulation.
    *   **Note:** The build artifact is typically located at `rundir/build/run` or `build/<project_name>`.

4.  **Verification (Project Specific):**
    *   Check the project's specific `Makefile` for verification targets (e.g., `test`, `regr`, `verif`).
    *   Commonly, `make all` builds everything including verification components.

## Workflow
1.  **Edit YAML** (`arch/yaml/...`)
2.  **`make db`** (Validate Schema)
3.  **`make gen`** (Generate Code)
4.  **Implement** (`model/...` or `rtl/...`)
5.  **`make run`** (Build & Simulate)

## Constraints
*   **Do not** invoke Python scripts directly (e.g., `arch2code.py`). Always use the `make` targets which set up the correct environment and paths.
*   **Do not** edit generated files. They are overwritten by `make gen`.
*   Most commands should be run from the `rundir` or project root where the main `Makefile` resides. Exception is `make lint` in the rtl dir
