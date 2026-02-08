# Skill: SystemC Core

## Purpose
Guide the user in writing core SystemC modules, focusing on module structure, threading, and logging.

## References
*   **API Reference:** `SYSTEMC_API_USER_REFERENCE.md` (See "Module Logging")

## Instructions

1.  **Module Structure & Generated Code:**
    *   **Auto-Generation:** The class declaration, inheritance, factory registration, and member declarations (registers/memories/ports) are **auto-generated** in the `.h` file.
    *   **Constructor:** The constructor signature and initialization list are **auto-generated** in the `.cpp` file.
    *   **Safe Zones:** **NEVER** modify code between `// GENERATED_CODE_BEGIN` and `// GENERATED_CODE_END` markers.

2.  **Implementation Location:**
    *   **Header (.h):** Add manual member variables and function declarations **after** the `// GENERATED_CODE_END` marker in the class definition.
    *   **Source (.cpp):**
        *   **Initialization List:** Add manual member initializers (starting with a comma `,`) **between** the first `// GENERATED_CODE_END` and the next `// GENERATED_CODE_BEGIN`.
        *   **Constructor Body:** Add manual logic (like `SC_THREAD` registration) **after** the final `// GENERATED_CODE_END` in the constructor.

    ```cpp
    // MyBlock.h
    SC_MODULE(MyBlock), public blockBase, public MyBlockBase
    {
        // GENERATED_CODE_BEGIN
        // ... auto-generated members ...
        // GENERATED_CODE_END

        // <--- Add manual members here --->
        sc_event myEvent;
        void myThread();
    };
    ```

    ```cpp
    // MyBlock.cpp
    MyBlock::MyBlock(...) : ...
         // GENERATED_CODE_BEGIN --template=constructor --section=init
         ,autoGenMember(...)
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

4.  **Status Reporting:**
    *   **See 'Debug' Skill:** For detailed instructions on implementing `statusPrint(void)` to debug simulation hangs, refer to the **Debug** skill.
