# Plan: `.cppm` Module Scaffold Sections

## Goal

Move generated C++20 module interface scaffold for generated `.cppm` context files into generated sections, while keeping section headers clean and driven by file-level mode.

## Current Problem

Generated `.cppm` files currently have module syntax split between fixed file skeleton text and generated sections. This includes critical generated content such as:

- `module;`
- global-module-fragment includes
- `export module ...;`
- dependency `import ...;` and `using namespace ...;`
- `export namespace ... {`
- the namespace close brace

This is fragile because arch2code only regenerates `GENERATED_CODE_BEGIN/END` bodies. Any generated semantic content outside those bodies can drift when module names, namespace names, or dependencies change.

The intended steady state is that copyright remains outside generated sections. The top-of-file module scaffold is regenerated through `moduleScaffold` sections, and each content section emits its own complete exported namespace block in module mode.

## Direction

Use a dedicated module scaffold template and file-level mode.

- Continue hard replacement: generated `*Includes` files are `.cppm` module interface units, not side-by-side `.h` and `.cppm` files.
- Do not add whole-file overwrite behavior for `.cppm` files.
- Do not rely on manual scaffold edits in generated `.cppm` files.
- Keep dependency imports in the existing `headers` template.
- Move the global-module-fragment scaffold, scaffold includes, and module declaration into one generated `moduleScaffold` section.
- Make content templates emit complete `export namespace <module>_ns { ... }` blocks when `mode=module`.
- Use file-level `--mode=module` to select module behavior instead of adding `--fileMapKey=include_cppm` to section headers.

## File-Level Mode Contract

The generated `.cppm` file should declare module mode once:

```cpp
// GENERATED_CODE_PARAM --context=ip.yaml --mode=module
```

Section headers should remain generic where possible:

```cpp
// GENERATED_CODE_BEGIN --template=headers
```

The renderer already merges file-level params into section args. Therefore `headers.py` can use `args.mode` to decide how to render dependencies.

Recommended mode mapping:

- `mode=module`: use the generated `.cppm` include-file map and emit `import <module>;` plus `using namespace <module>_ns;`
- `mode=header`: use the generated header include-file map and emit `#include "..."`
- empty mode: keep legacy header behavior for compatibility

Keep `--fileMapKey` temporarily as an override/backstop for existing special cases, but do not use it in new `.cppm` scaffold sections.

## Target `.cppm` Shape

Approximate output:

```cpp
// GENERATED_CODE_PARAM --context=ip.yaml --mode=module
// copyright ...
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=moduleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "bitTwiddling.h"
#include <algorithm>
export module ip;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=headers
import dependency_module;
using namespace dependency_module_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=includes --section=constants
export namespace ip_ns {
//constants
}
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=includes --section=types
export namespace ip_ns {
// types
}
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=includes --section=enums
export namespace ip_ns {
// enums
}
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=structures
export namespace ip_ns {
// structures
} // namespace ip_ns
// GENERATED_CODE_END
```

## Implementation Plan

1. Add `templates/systemc/moduleScaffold.py`.
2. Register `moduleScaffold` in `config/project.yaml` under `templates:`.
3. Update `templates/fileGen/fileGen.py` `include_cppmTemplate` so copyright is the only non-marker file text outside generated sections; `module;`, all top-of-file scaffold includes, and `export module ...;` must be emitted by `moduleScaffold --section=moduleHeader`.
4. Update `headers.py` so dependency rendering derives from file-level `args.mode` by default.
5. Remove `headers.py` ownership of `moduleFragment` and `moduleClose` scaffold behavior after `moduleScaffold` owns top-of-file module sections.
6. Update `includes.py` so `constants`, `types`, and `enums` wrap their generated content in a complete `export namespace <module>_ns { ... }` block when `mode=module`.
7. Update `structures.py` so the default/header structure section wraps generated structures in a complete `export namespace <module>_ns { ... }` block when `mode=module`.
8. Add `--mode=header` to the normal include-header file-level params if useful for clarity, while keeping empty mode as legacy header behavior.
9. Regenerate `examples/ip_test` generated files from templates rather than manually patching generated `.cppm` outputs.

## Checkpoint Progress

Date: 2026-05-01

Completed for the current `ip_test` checkpoint:

- `templates/fileGen/fileGen.py` `include_cppmTemplate` includes generated structure test sections after the main `structures` section:
  - `structures --section=testStructsHeader`
  - `structures --section=testStructsCPP`
- `templates/systemc/moduleScaffold.py` emits the module global fragment includes, including `q_assert.h`; structure test sections do not add includes inside `export namespace` in module mode.
- `templates/systemc/structures.py` wraps structure declarations and structure test sections in complete `export namespace <module>_ns { ... }` blocks when `mode=module`.
- `examples/ip_test/model/ipIncludes.cppm` has been regenerated with the module scaffold and structure test sections.
- The generated module structure test class is templated: `test_ip_structs<Config>`.
- The generated module structure tests cover both parameterizable structs (`ipDataSt<Config>`, `ipCfgSt<Config>`, etc.) and fixed structs (`ipFixedSt`, `ipFixedNestedSt`, etc.).
- `examples/ip_test/tb/ip_top/ip_topConfig.cpp` now calls `test_ip_structs<ipDefaultConfig>::test()`.

Validation at this checkpoint:

- `python3 -m py_compile templates/systemc/structures.py templates/fileGen/fileGen.py templates/systemc/moduleScaffold.py` passed.
- `make db` in `examples/ip_test` was up to date.
- `make gen` in `examples/ip_test` passed and regenerated `model/ipIncludes.cppm`.
- `make` in `examples/ip_test/rundir` passed.
- `make run` in `examples/ip_test/rundir` printed `Running test_ip_structs`, then failed at the known factory-registration issue (`ip_top_model` unregistered). No structure test failure occurred first.

## `moduleScaffold` Sections

Proposed sections:

- `moduleHeader`: `module;`, required global-module-fragment includes, and `export module <module_name>;`

`moduleScaffold` should not emit namespace open/close sections for the content body. Each content section should own a complete exported namespace block in module mode.

Module and namespace names should be derived from `data["fileNameBase"]`, matching the current logic used by `headers.py`:

- strip `.cppm`
- strip trailing `Includes`
- replace `-` and `.` with `_`
- namespace is `<module>_ns`

## Verification

Minimum checks:

```bash
python3 -m py_compile templates/fileGen/fileGen.py templates/systemc/headers.py templates/systemc/includes.py templates/systemc/structures.py templates/systemc/moduleScaffold.py
```

Regenerate `ip_test`:

```bash
rm -rf /work/ws/debayer/builder/base/examples/ip_test/.gen
make gen
```

Inspect generated `.cppm` files to confirm:

- `module;`, global-module-fragment includes, and `export module` are inside `moduleScaffold --section=moduleHeader`.
- dependency `import` and `using namespace` lines are inside `headers`.
- each content section that emits declarations contains its own complete `export namespace ... { ... }` block in module mode.
- no critical generated module syntax remains outside generated sections.

Copyright may remain outside generated sections. Generated control comments such as `GENERATED_CODE_PARAM`, `GENERATED_CODE_BEGIN`, and `GENERATED_CODE_END` are also necessarily outside generated bodies.

Build verification should be bounded. Run a clean build only if it is cheap and avoid spending significant time on make-system issues because this flow is expected to move to CMake later.

## Open Questions

- Should `mode=header` be added immediately to generated header files, or should empty mode remain the only header signal for now?
- Should `--fileMapKey` be deprecated in docs/comments after module mode is working, or simply left as an internal compatibility escape hatch?
