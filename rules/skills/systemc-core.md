---
name: systemc-core
description: Guide for writing core SystemC modules including module structure, threading, register and memory access, and logging
---
# Skill: SystemC core

## Purpose
Write a block's SystemC model: the module file layout, where hand-written code goes, register and memory access, threads and logging.

## References
*   API reference: `builder/base/SYSTEMC_API_USER_REFERENCE.md`, sections "Module Logging" and "Hardware Objects".
*   Code generation markers: `ARCH2CODE_AI_RULES.md`, heading "9. Code Generation Markers" under "Best Practices & Common Patterns". It lists every `GENERATED_CODE_PARAM` and `GENERATED_CODE_BEGIN` option.
*   Port calls for each interface family: **systemc-interfaces**. Shared events, arbitration and `synchLock`: **systemc-synchronization**. Trackers and `statusPrint`: **debug**.

## 1. Module file layout
A block model is one C++20 module file, `model/<block>.cppm`. Its ports are declared in the generated `base/<block>Base.cppm`, which you never edit. Never edit between `GENERATED_CODE_BEGIN` and `GENERATED_CODE_END`.

The generated regions, in order:
*   `moduleScaffold --section=blockModuleHeader` is the global module fragment, `module;` and the generated `#include`s.
*   `moduleExport` holds `export module <module>.block;` and every import: `import <module>.base;`, the block's own Config module when it declares `params:`, each child's `.base` module and any child Config module the class names, and each context module the block's ports and members use. It holds no `using namespace` line, so the slot after it stays open for imports.
*   `classDecl` holds a `using namespace <context>_ns;` for each imported context, the class head, the generated register and memory members, and the constructor declaration.
*   `constructor --section=init` is the initializer list.
*   `constructor --section=body` opens the constructor body. In a block with children it binds the child instances. In a leaf block with firmware-accessible registers or memories it registers them and starts the register handler thread.

In a project with an `addressBlock:` router, every block that owns registers or firmware-accessible memories gets a generated register handler block, named `<block>` with `fileGeneration.regBlockNaming.blockSuffix` appended, so `blockB` in the mixed example has handler `blockBRegs`. The suffix defaults to `_regs`, and the examples set `Regs`. The handler always has RTL. It has a model only when the owning block also has children. The handler model uses `blockRegs --section=header`, `--section=init` and `--section=body` in place of `classDecl` and `constructor`. A leaf block has no handler model. Its own model holds the `hwRegister` members and the `regHandler` thread, as section 3 describes.

### Plain class or Config template
The model class is a `template<typename Config>` class only when the block declares its own `params:`. Otherwise it is a plain class.

| | Block without its own `params:` | Block with its own `params:` |
| :--- | :--- | :--- |
| Class head | `export SC_MODULE(blk), public blockBase, public blkBase` | `export template<typename Config>` then `SC_MODULE(blk), public blockBase, public blkBase<Config>` |
| `SC_HAS_PROCESS` | constructor init region, at namespace scope | inside the class |
| Factory registration | constructor init region | the generated registrar, not this file |
| Inherited constants, types, ports | named directly | named through the generated `using blkBase<Config>::name;` lines, with no `Config::` or `this->` |
| Out-of-class member definition | `void blk::fn()` | `template<typename Config> void blk<Config>::fn()` |

### Naming
*   A block's C++ module is `<project>_<block>.block`. A name that equals the project name, or already starts with `<project>_`, is used unchanged. Block `ip` in project `ip` gives module `ip.block`.
*   A YAML context's module is `<project>_<includeName>` under the same rule. Its namespace is the module name plus `_ns`. `includeName` is the file stem unless the file sets a top-level `includeName:`.
*   Copy a context's name from the `export module` line of its generated `model/<includeName>Includes.cppm` rather than building it.

## 2. Where hand-written code goes
The scaffold labels each user slot with a comment.

*   `// user #includes here`, after the `blockModuleHeader` region: plain headers, including any whose definitions live in a `.cpp`. They attach to the global module.
*   `// user imports here`, after the `moduleExport` region: the module preamble. Import here a context whose types only the block body uses, since the generated region imports only what ports and generated members need. Write every `import` first, then the `using namespace` lines, then `#include`s of headers that name module or `Config` types. Any declaration closes the preamble, a `using namespace` as much as an `#include`, and an `import` after it is ill-formed.
*   `// block implementation members`, after the `classDecl` region: member variables and function declarations, inside the class body.
*   Between the `constructor --section=init` end marker and the `--section=body` begin marker: member initializers, each starting with a comma.
*   After the `constructor --section=body` end marker: `SC_THREAD` registrations and other constructor logic. A testbench registers its tests here with `ADD_TEST` (see **verify-testbench**).

A header that defines a pimpl class also defined in a plain `.cpp` goes in the `#include` slot, because that class must attach to the global module to match the `.cpp` at link time.

A block without its own `params:`, in project `proj`:

```cpp
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=blockModuleHeader
module;
#include "systemc.h"
// ... generated #includes ...
// GENERATED_CODE_END
// user #includes here ...
#include "q_assert.h"
// GENERATED_CODE_BEGIN --template=moduleExport
export module proj_myBlock.block;
import proj_myBlock.base;
import proj;
// GENERATED_CODE_END
// user imports here ...
import proj_bodyTypes;
using namespace proj_bodyTypes_ns;
// GENERATED_CODE_BEGIN --template=classDecl
using namespace proj_ns;
export SC_MODULE(myBlock), public blockBase, public myBlockBase
{
    // ... generated members ...
    myBlock(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    // GENERATED_CODE_END
    // block implementation members
    sc_event myEvent;
    void myThread(void);
};

// GENERATED_CODE_BEGIN --template=constructor --section=init
SC_HAS_PROCESS(myBlock);
// ... factory registration ...
myBlock::myBlock(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("myBlock", name(), bbMode)
        ,myBlockBase(name(), variant)
// GENERATED_CODE_END
        ,myEvent("myEvent")
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    // ... generated body ...
    // GENERATED_CODE_END
    SC_THREAD(myThread);
}

void myBlock::myThread(void)
{
    // ...
}
```

## 3. Registers and memories
Declare registers and memories in YAML. The generator emits the `hwRegister` and `hwMemory` members, their registration (`_a2cRegs.addRegister`, `_a2cRegs.addMemory`), the memory `bindPort` calls and the register handler (`regHandler`, `registerHandler(_a2cRegs, ...)`, `SC_THREAD(regHandler)`). Never add a thread on the register bus port.

*   **A register the block owns** is an `hwRegister` member. Read it with `reg.read()`. To react to firmware writes, call `reg.registerEvent(&ev)` once and loop on `wait(ev)`. The block's own `reg.write(v)` notifies the same event. An `hwRegister` holds one event, so a second `registerEvent` replaces the first. It has no `->`, no `setExternalEvent` and no `readNonBlocking`.
*   **A memory the block owns** is an `hwMemory` member. Datapath code uses `read(i)`, `write(i, v)` and the RMW calls. `writeNoDelay(i, v)` writes with no access delay, for a thread whose port call already supplies the timing. `operator[]` skips timing and is only for backdoor uses such as logging. Never add a shadow copy. `readRMW(i, magic)` locks row `i` and returns it. Finish with `writeRMW(i, v)` or `releaseRMW(i)`. `magic` is the tandem match key, as for `synchLock::lock`, so give each call site its own value. The RMW calls assert unless the constructor body first calls `mem.configureSynch(getAltName(), nullptr)`.
*   **A memory reached through a `memory` port** (`memory_out`) uses `port->request(isWrite, addr, data)`.
*   **A local `regType: memory` register** is the one case that needs a hand-written register thread. It serves `<reg>_channel` with `reqReceive` and `complete`, against storage the block declares.
*   **`status` and `external_reg` ports** each have their own call rules. See the table in **systemc-interfaces**.

Firmware writes a register wider than 32 bits one word at a time (`+0` holds bits `[31:0]`, `+4` bits `[63:32]`).
*   In a block model, each word write updates the `hwRegister` and notifies the event passed to `registerEvent()`. A thread woken by the low-word write still sees the old high word. A read-only `hwRegister` ignores firmware writes.
*   In a register handler model, a read-write `hwRegisterIf` issues one `reg_write_cmd` per word write, so the child block sees the new low word next to the old high word.

## 4. Threads
*   A thread is a `while (true)` loop registered with `SC_THREAD` in the constructor body.
*   A loop that blocks in a port call (`read()`, `receiveAddr()`, `request()`) needs no explicit `wait()`. A loop of only non-blocking calls spins, so give it a `wait()`.
*   A model has no clock or reset ports, and its threads never wait on a block clock. Block clocks and resets exist only in the RTL. An `output` clock or reset has no model counterpart, and co-simulation compares data ports only. See `builder/base/specs/spec-clock-reset-requirements.md` §4.11.

## 5. Logging and errors
*   Log with `log_.logPrint`, and format with `std::format`. Pass a lambda when the formatting is costly, so it runs only when the level prints.
*   The default run verbosity is medium. `logPrint(msg)` with no level is LOG_NORMAL and prints only at high or above. `make run` passes no extra arguments to the binary. To raise verbosity, go to `rundir/`, rerun the command `make run` prints and append `--verbosity high`, for example `build/run <testbench> --verbosity high`.
*   Each verbosity adds one level: low prints LOG_ALWAYS, medium adds LOG_IMPORTANT, high adds LOG_NORMAL, full adds LOG_DEBUG.
*   `--verbosity` accepts `low`, `med`, `medium`, `high`, `full` or `0`-`3`, in any case. Any other value stops the run with exit status 2 and lists the accepted spellings.
*   There is no `logError`. Report a test failure with `errorCode::fail`.

```cpp
log_.logPrint(std::format("Thread {} started", __func__), LOG_IMPORTANT);
log_.logPrint([&]() { return std::format("state {}", someCostlyDump()); }, LOG_DEBUG);
```

## 6. Assertions and unique names
*   `Q_ASSERT(cond, msg)` passes `name()` as its context, so it compiles only in a member of a class that has `name()`, such as an `sc_module`. Elsewhere, such as in a testbench `Config` class, use `Q_ASSERT_CTX(cond, ctx, msg)` and pass the context string.
*   Call `sc_gen_unique_name` with both arguments, for example `sc_gen_unique_name("x", false)`. Only `sysc/kernel/sc_simcontext.h` declares the `preserve_first = false` default. `sysc/kernel/sc_process.h` declares the function without it, so a translation unit that sees only that header rejects the one-argument call.
