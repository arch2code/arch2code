---
name: systemc-core
description: Guide for writing core SystemC modules including module structure, threading, and logging
---
# Skill: SystemC Core

## Purpose
Guide the user in writing core SystemC modules, focusing on module structure, threading, and logging.

## References
*   **API Reference:** `SYSTEMC_API_USER_REFERENCE.md` (See "Module Logging")
*   **Code Generation Markers:** `ARCH2CODE_AI_RULES.md` (Section 9 — "Code Generation Markers — Comprehensive Reference") for all `GENERATED_CODE_PARAM` and `GENERATED_CODE_BEGIN` options, templates, and sections.

## Instructions

1.  **Module Structure & Generated Code:**
    *   **Single Module File:** A block implementation is one C++20 module file, `model/<block>.cppm`. It opens with a global-module-fragment (`module;` plus `#include`s), declares the module, then declares the templated class and its constructor — all in the same file. There is no separate `.h`/`.cpp` pair.
    *   **Generated Regions:** Three generated regions carry the block's scaffolding, in order:
        *   `moduleScaffold --section=blockModuleHeader` — the global module fragment: `module;` and the generated `#include`s.
        *   `moduleExport` — `export module <block>.block;` and `import <block>.base;` (module names may be `<project>_<block>`-qualified on cross-project collision).
        *   `classDecl` — `export template<typename Config> SC_MODULE(<block>), public blockBase, public <block>Base<Config>`, the factory registration, the `using <block>Base<Config>::...;` re-exports of inherited names/types, and the constructor declaration.
    *   **Constructor:** The constructor definition lives in the same `.cppm`, split across `constructor --section=init` (the initialization list) and `constructor --section=body`.
    *   **Safe Zones:** **NEVER** modify code between `// GENERATED_CODE_BEGIN` and `// GENERATED_CODE_END` markers.

2.  **Implementation Location:**
    *   **User `#includes`:** Add manual `#include`s after the `blockModuleHeader` region's `// GENERATED_CODE_END`, in the global-module-fragment zone (before `export module`).
    *   **Body-only context types:** Types or constants used only by the block body — not on the interface, so not imported by the generated `moduleExport` region — need a hand-written `import <ctx>; using namespace <ctx>_ns;` in the preamble gap between the `moduleExport` region and the `classDecl` region.
    *   **Members:** Add manual member variables and function declarations **after** the `classDecl` region's `// GENERATED_CODE_END`, inside the class body.
    *   **Initialization List:** Add manual member initializers (starting with a comma `,`) **between** the `constructor --section=init` `// GENERATED_CODE_END` and the next `// GENERATED_CODE_BEGIN`.
    *   **Constructor Body:** Add manual logic (like `SC_THREAD` registration) **after** the `constructor --section=body` `// GENERATED_CODE_END`.
    *   **Inherited names:** Use the generated `using <block>Base<Config>::name;` declarations to refer to inherited constants, parameterized types, and ports unqualified (no `Config::` / `this->`).

    ```cpp
    // myBlock.cppm
    // GENERATED_CODE_BEGIN --template=moduleScaffold --section=blockModuleHeader
    module;
    #include "systemc.h"
    // ... generated #includes ...
    // GENERATED_CODE_END
    // <--- Add manual #includes here --->

    // GENERATED_CODE_BEGIN --template=moduleExport
    export module myBlock.block;
    import myBlock.base;
    // GENERATED_CODE_END
    // <--- body-only context types: import <ctx>; using namespace <ctx>_ns; --->

    // GENERATED_CODE_BEGIN --template=classDecl
    export template<typename Config>
    SC_MODULE(myBlock), public blockBase, public myBlockBase<Config>
    {
        SC_HAS_PROCESS(myBlock);
        using myBlockBase<Config>::somePort;   // inherited names usable unqualified
        myBlock(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
        // GENERATED_CODE_END

        // <--- Add manual members here --->
        sc_event myEvent;
        void myThread();
    };

    // GENERATED_CODE_BEGIN --template=constructor --section=init
    template<typename Config>
    myBlock<Config>::myBlock(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
         : sc_module(blockName)
          ,blockBase("myBlock", name(), bbMode)
          ,myBlockBase<Config>(name(), variant)
    // GENERATED_CODE_END

         // <--- Add manual initializers here --->
         ,myEvent("myEvent")

    // GENERATED_CODE_BEGIN --template=constructor --section=body
    {
         // ... auto-generated body ...
         // GENERATED_CODE_END

         // <--- Add manual constructor logic here --->
         SC_THREAD(myThread);
    }
    ```

3.  **Logging:**
    *   Use `log_.logPrint` for all logging.
    *   Use `std::format` for formatting strings.
    *   Use lazy evaluation (lambda) for complex formatting to avoid overhead when logging is disabled.

    ```cpp
    log_.logPrint(std::format("SystemC Thread:{} started", __func__));
    log_.logPrint([&]() { return std::format("complex info: {}", some_complex_calculation()); }, LOG_DEBUG);
    ```

4.  **Hardware Registers & Memories:**
    *   **Definition:** Registers and memories must be defined in the **YAML architecture files**, not manually in C++.
    *   **Auto-Generation:** The `hwRegister` and `hwMemory` member declarations and their registration (`regs.addRegister`, `regs.addMemory`) are **auto-generated** inside the `GENERATED_CODE` blocks.
    *   **Access:** Access these resources in your manual code using the generated member names (e.g., `myReg.m_val.field`).
    *   **Trackers:** For detailed instructions on using `tracker<T>` for lifecycle monitoring and debugging, refer to the **Debug** skill.

5.  **Status Reporting:**
    *   **See 'Debug' Skill:** For detailed instructions on implementing `statusPrint(void)` to debug simulation hangs, refer to the **Debug** skill.
