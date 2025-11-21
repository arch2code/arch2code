# Unit Tests

This directory contains unit tests for the arch2code schema and YAML processing.

## Overview

All tests are **self-contained** within the `unittest/` directory. Tests do not depend on external project databases or user-defined data. Tests use either:
- The `mixed_test_arch/` test project data (self-contained copy)
- Mock objects for isolated unit testing
- System-level interface definitions from `builder/interfaces/` (framework resources)

## Test Files

### Core Schema Tests

- **test_nested_loading.py** - Tests 4-level nested table loading (interface_defs → modports → modportGroups → groups)
  - Verifies multi-entry table grouping works correctly
  - Tests composite key construction
  - Validates ancestor key fields are present at all levels
  - Checks for data collisions between interfaces/modports
  - **Self-contained:** Builds temporary database from `mixed_test_arch/`

- **test_apb_validation.py** - Comprehensive APB interface validation (YAML → Schema → Database → Reconstruction)
  - Validates YAML structure of system APB interface
  - Tests database schema and content
  - Confirms modportGroups load correctly (not None)
  - Verifies reconstruction of nested structures
  - **Self-contained:** Builds temporary database from `mixed_test_arch/`

- **test_interface_loading.py** - Tests interface loading with proper key composition
  - Validates interfaces and modports are distinct
  - Checks for data collisions between different interface types
  - Tests signal details and hierarchy
  - **Self-contained:** Builds temporary database from `mixed_test_arch/`

- **test_data_by_parent_logic.py** - Unit tests for data_by_parent indexing logic
  - Tests parent-key indexing without full database
  - Validates Node methods (get_parent_storage_key_field_name, build_storage_key)
  - Tests parent indexing concept
  - **Self-contained:** Uses mock Node objects, no database required

### Project Tests

- **test_mixed_project.py** - Tests mixed project build and schema validation
  - Validates project builds successfully from YAML
  - Checks schema sections and nodes
  - Verifies key building methods exist
  - **Self-contained:** Builds temporary database from `mixed_test_arch/`

### Error Handling Tests

- **test_error_missing_fields.py** - Tests error handling for missing required fields
  - Validates clear error messages (no Python stack traces)
  - Tests 8 common error scenarios (types, constants, interfaces, etc.)
  - **Result:** 8/8 tests pass ✅ (1 bug found and fixed: memory missing wordLines)
  - **Self-contained:** Creates temporary YAML files for each test case

- **test_error_auto_functions.py** - Tests error handling for auto functions and special logic
  - Validates error handling in auto functions (_auto_entryType, _auto_width, etc.)
  - Tests eval expression error handling
  - Tests constant/variable reference resolution
  - **Result:** 5/5 tests pass ✅ (2 bugs found and fixed: enum value validation, eval error handling)
  - **Self-contained:** Creates temporary YAML files for each test case

### Test Data

- **mixed_test_arch/** - Self-contained copy of mixed project YAML files
  - `mixedProject.yaml` - Project definition file
  - `mixed.yaml` - Main architecture file
  - `mixedBlockC.yaml` - Block C definition
  - `mixedInclude.yaml` - Include file
  - `mixedNestedInclude.yaml` - Nested include file
  - `exampleAddress.yaml` - Address configuration
  - `Makefile` - Build configuration

## Running Tests

Run all tests:
```bash
./run_all_tests.sh
```

Run individual tests:
```bash
python3 test_nested_loading.py
python3 test_apb_validation.py
python3 test_interface_loading.py
python3 test_data_by_parent_logic.py
python3 test_mixed_project.py
python3 test_error_missing_fields.py      # Error handling: missing fields
python3 test_error_auto_functions.py      # Error handling: auto functions
```

## Test Coverage

These tests verify:
- ✅ Nested table loading with composite keys (4 levels deep)
- ✅ Multi-entry vs single-entry table handling
- ✅ Parent key chain construction and propagation  
- ✅ Storage key and lookup key building
- ✅ Node pickling and unpickling
- ✅ sqlite3.Row compatibility
- ✅ Error handling for missing keys
- ✅ Interface collision detection
- ✅ Schema section validation
- ✅ Project build from YAML
- ✅ Database creation and cleanup
- ✅ **User-friendly error messages** (13/13 cases validated)
  - **Missing required fields (8 tests)**:
    - Types missing width
    - Constants missing value/eval
    - Interfaces missing interfaceType
    - Structure fields with invalid types
    - Instances missing instanceType
    - Connections missing src
    - Registers missing structure
    - Memories missing wordLines (bug found and fixed)
  - **Auto functions & special logic (5 tests)**:
    - Undefined variable in structure (_auto_entryType)
    - Undefined constant in width (constParse)
    - Enum missing value/eval (eval field type - bug found and fixed)
    - Type missing width with no enum (_auto_width)
    - Eval expression runtime errors (eval try-catch - bug found and fixed)

## Important Notes

- **No External Dependencies:** Tests do not rely on the debayer project database (`/work/ws/debayer/debayer.db`)
- **Temporary Databases:** Tests that require databases create temporary files and clean them up automatically
- **System Interfaces:** Tests may reference system-level interface definitions in `builder/interfaces/` which are framework resources, not user project data
- **Test Isolation:** Each test can run independently without affecting others
