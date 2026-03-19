# Skill: SystemC Resources

## Purpose
Guide the user on using `hwRegister`, `hwMemory`, and `tracker` for state management and debugging in SystemC.

## Instructions

1.  **Hardware Registers & Memories:**
    *   **Definition:** Registers and memories must be defined in the **YAML architecture files**, not manually in C++.
    *   **Auto-Generation:** The `hwRegister` and `hwMemory` member declarations and their registration (`regs.addRegister`, `regs.addMemory`) are **auto-generated** inside the `GENERATED_CODE` blocks.
    *   **Access:** Access these resources in your manual code using the generated member names (e.g., `myReg.m_val.field`).

2.  **Trackers (`tracker<T>`):**
    *   **See 'Debug' Skill:** For detailed instructions on using trackers for lifecycle monitoring and debugging, refer to the **Debug** skill.

