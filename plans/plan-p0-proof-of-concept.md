# Plan: P0 Proof-of-Concept — Config Templates + C++ Modules with SystemC

**Status:** historical. This is a completed prototype record; it records
prototype validation only and is not an active implementation plan.

## Objective

Validate that the target code form — **Config-templated structs and SC_MODULE blocks inside C++20 module interface units** — works with the SystemC 2.3.4 toolchain (Clang 20.1, C++23). This is a non-negotiable prerequisite before investing in generator changes.

This is a **throwaway prototype**. No generator code is modified. All files are hand-written under `proto/` and compiled with a standalone Makefile. The prototype succeeds or fails based on whether the target patterns compile, link, and run correctly under SystemC simulation.

## Environment

| Component | Version | Notes |
|-----------|---------|-------|
| **Clang** | **20.1.8** | **Primary target** — default compiler for the project (`CXX=clang++` in `a2c-common.mk:100`) |
| GCC | 13.1.0 | Secondary — available via `USE_GCC=1`, not the focus of this POC |
| C++ standard | C++23 (`-std=c++23`) | Set in `a2c-common.mk:101` |
| SystemC | 2.3.4 | Installed at `/usr/include/systemc.h`, linked via `-lsystemc` |
| Build | GNU Make | Standalone Makefile for POC — **no CMake needed** |

### Why Make is Sufficient (No CMake Required)

CMake 3.28+ provides automatic C++20 module dependency scanning, which is valuable for large projects with many interdependent modules. The POC has at most 3 module files (`isp_types.cppm`, `interpolate.cppm`, and their consumer) with trivial, statically-known dependencies. Clang's module compilation is a straightforward two-step process that maps directly to Make rules:

```makefile
# Step 1: Compile module interface unit -> precompiled module
build/isp.pcm: types/isp_types.cppm
	$(CXX) $(CXX_FLAGS) --precompile $< -o $@

# Step 2: Compile consumer with module reference
build/test_module_types.o: test/test_module_types.cpp build/isp.pcm
	$(CXX) $(CXX_FLAGS) -fmodule-file=isp=build/isp.pcm -c $< -o $@
```

The production build system will need module support added to `a2c-systemc.mk` — but that decision is informed by the POC results, not a prerequisite for it. The POC Makefile will document exactly which flags and compilation steps are needed, serving as the specification for the eventual `a2c-systemc.mk` changes.

## What We're Validating

Seven specific risks from the high-level plan (`plan-ip-namespaces-and-parameterization.md` Sections 4.6, 6.6, Open Questions 4-5):

| ID | Risk | Section | Pass Criteria |
|----|------|---------|---------------|
| **V1** | `template<typename Config> SC_MODULE(block)` with `SC_HAS_PROCESS` / `SC_THREAD` | 4.6 | Template block compiles, constructs, and runs SC_THREAD to completion |
| **V2** | `rdy_vld` channel/port binding with `template<typename Config>` struct payload types | 4.6 | `rdy_vld_channel<video_rgb_t<Config>>` binds to `rdy_vld_in` / `rdy_vld_out`, data transfers correctly |
| **V3** | `sc_trace` with template struct types | 4.6 | `sc_trace(tf, my_struct<Config>, "name")` compiles and produces trace output |
| **V4** | Two Config structs coexisting — different `_bitWidth`, different `_packedSt` behavior | 4.6 | `rgb_pixel_t<config_8bpc>` and `rgb_pixel_t<config_12bpc>` are distinct types, pack/unpack correctly with their respective widths |
| **V5** | C++20 module interface unit with SystemC in global module fragment | 6.6 | `module; #include "systemc.h"; export module isp;` compiles |
| **V6** | Templated structs inside `export namespace` in a module | 6.3 | `template<typename Config> struct rgb_pixel_t` exported from module, imported and instantiated by consumer |
| **V7** | Templated SC_MODULE inside a module, imported by consumer, instantiated and run | 6.3 | Full pipeline: module exports templated block, consumer imports and runs simulation |

## Prototype Structure

```
proto/
├── Makefile                    # Standalone build, no arch2code dependency
├── README.md                   # How to run, expected output
│
├── configs/
│   └── debayer_configs.h       # Two Config structs (8bpc, 12bpc)
│
├── types/
│   ├── isp_types.h             # Hand-written subset of isp_typesIncludes.h/.cpp
│   │                           #   video_frame_t (non-parameterizable, plain struct)
│   │                           #   template<Config> pixel_t, rgb_pixel_t,
│   │                           #   bayer_pixels_per_clock_t, video_bayer_t, video_rgb_t
│   │                           #   with inline pack/unpack (header-only for templates)
│   └── isp_types.cppm          # V5/V6: Module interface unit wrapping the same types
│
├── block/
│   ├── interpolate_base.h      # Hand-written subset of interpolateBase.h
│   │                           #   template<Config> interpolateBase with rdy_vld ports
│   ├── interpolate.h           # template<Config> SC_MODULE(interpolate)
│   ├── interpolate.cpp         # SC_HAS_PROCESS, SC_THREAD, simple passthrough logic
│   └── interpolate.cppm        # V7: Module interface unit for the block
│
├── test/
│   ├── test_structs.cpp        # V4: Instantiate both configs, pack/unpack, verify
│   ├── test_sc_module.cpp      # V1/V2/V3: SystemC testbench — instantiate block,
│   │                           #   bind channels, send data, check output, trace
│   ├── test_module_types.cpp   # V5/V6: Import module, instantiate template types
│   └── test_module_block.cpp   # V7: Import module, instantiate template SC_MODULE
│
└── util/
    ├── bitTwiddling.h           # Copy of builder/base/common/systemc/bitTwiddling.h
    └── rdy_vld_channel.h        # Minimal rdy_vld stub (or symlink to real one)
```

## Detailed File Specifications

### `configs/debayer_configs.h`

Two Config policy structs with different parameter values:

```cpp
#pragma once
#include <cstdint>

struct config_8bpc {
    static constexpr uint32_t BITS_PER_PIXEL_COLOR = 8;
    static constexpr uint32_t MAX_PIXEL_VALUE = 255;
    static constexpr uint32_t PIXELS_PER_CLOCK = 4;
};

struct config_12bpc {
    static constexpr uint32_t BITS_PER_PIXEL_COLOR = 12;
    static constexpr uint32_t MAX_PIXEL_VALUE = 4095;
    static constexpr uint32_t PIXELS_PER_CLOCK = 8;
};
```

### `types/isp_types.h` — Template Struct Definitions

Hand-write the target form of what the generators would eventually produce. This is the core of the validation — these patterns must compile and behave correctly.

Subset of current `isp_typesIncludes.h` + `isp_typesIncludes.cpp`, transformed to:
- Non-parameterizable structs (`video_frame_t`) remain plain structs, unchanged from current generated code
- Parameterizable types use `template<typename Config>`:
  - `pixel_t` → `template<typename Config> using pixel_t = uint64_t;`
  - `rgb_pixel_t` → `template<typename Config> struct rgb_pixel_t { pixel_t<Config> r, g, b; ... };`
  - `bayer_pixels_per_clock_t` → `template<typename Config> struct bayer_pixels_per_clock_t { pixel_t<Config> pixels[Config::PIXELS_PER_CLOCK]; ... };`
  - `rgb_pixels_per_clock_t` → same pattern with `rgb_pixel_t<Config>` array
  - `video_bayer_t` → mixed: `video_frame_t frame;` (plain) + `bayer_pixels_per_clock_t<Config> data;` (templated)
  - `video_rgb_t` → same mixed pattern

Key patterns to replicate from current generated code:
- `static constexpr uint16_t _bitWidth` using `Config::BITS_PER_PIXEL_COLOR` instead of bare `BITS_PER_PIXEL_COLOR`
- `static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;`
- `typedef uint64_t _packedSt;` (fixed for all parameterizable structs)
- `pack()` / `unpack()` with `Config::` symbolic expressions instead of resolved literals
- `sc_bv<StructName<Config>::_bitWidth>` in `sc_pack()` / `sc_unpack()` (constexpr template argument)
- `operator==`, `prt()`, `sc_trace()` as inline friend functions
- All method implementations inline in the header (template requirement)

The `_baseMask` changes to `63` for all parameterizable structs (since `_packedSt` is `uint64_t`).

**Current form** (from `isp_typesIncludes.cpp:73-88`):
```cpp
void rgb_pixel_t::pack(_packedSt &_ret) const {
    memset(&_ret, 0, rgb_pixel_t::_byteWidth);
    _ret = r;
    _ret |= (uint32_t)g << (8 & 31);
    _ret |= (uint32_t)b << (16 & 31);
}
void rgb_pixel_t::unpack(const _packedSt &_src) {
    uint16_t _pos{0};
    r = (pixel_t)((_src >> (_pos & 31)) & ((1ULL << 8) - 1));
    _pos += 8;
    g = (pixel_t)((_src >> (_pos & 31)) & ((1ULL << 8) - 1));
    _pos += 8;
    b = (pixel_t)((_src >> (_pos & 31)) & ((1ULL << 8) - 1));
}
```

**Target form** (for prototype):
```cpp
template<typename Config>
void rgb_pixel_t<Config>::pack(_packedSt &_ret) const {
    memset(&_ret, 0, rgb_pixel_t<Config>::_byteWidth);
    _ret = r;
    _ret |= (uint64_t)g << (Config::BITS_PER_PIXEL_COLOR & 63);
    _ret |= (uint64_t)b << ((2 * Config::BITS_PER_PIXEL_COLOR) & 63);
}
template<typename Config>
void rgb_pixel_t<Config>::unpack(const _packedSt &_src) {
    uint16_t _pos{0};
    r = (pixel_t<Config>)((_src >> (_pos & 63)) & ((1ULL << Config::BITS_PER_PIXEL_COLOR) - 1));
    _pos += Config::BITS_PER_PIXEL_COLOR;
    g = (pixel_t<Config>)((_src >> (_pos & 63)) & ((1ULL << Config::BITS_PER_PIXEL_COLOR) - 1));
    _pos += Config::BITS_PER_PIXEL_COLOR;
    b = (pixel_t<Config>)((_src >> (_pos & 63)) & ((1ULL << Config::BITS_PER_PIXEL_COLOR) - 1));
}
```

### `types/isp_types.cppm` — Module Interface Unit (V5/V6)

```cpp
module;
// Global module fragment — non-module headers go here
#include "systemc.h"
#include "bitTwiddling.h"

export module isp;

export namespace isp {
    // Non-parameterizable struct — plain, no template
    struct video_frame_t { /* same as isp_types.h */ };

    // Parameterizable types — template<typename Config>
    template<typename Config> using pixel_t = uint64_t;
    template<typename Config> struct rgb_pixel_t { /* same as isp_types.h */ };
    // ... etc
}
```

### `block/interpolate.h` — Template SC_MODULE (V1)

The critical pattern to validate. Mirrors current `model/interpolate.h` + `base/interpolateBase.h`:

```cpp
#include "systemc.h"
#include "isp_types.h"         // or: import isp; (for V7)
#include "rdy_vld_channel.h"

// Template base class (mirrors interpolateBase.h)
template<typename Config>
class interpolateBase : public virtual blockPortBase {
public:
    rdy_vld_out< video_rgb_t<Config> > video_rgb_stream;
    rdy_vld_in< video_bayer_t<Config> > video_bayer_stream;

    interpolateBase(std::string name) :
        video_rgb_stream("video_rgb_stream"),
        video_bayer_stream("video_bayer_stream")
    {};
};

// Template block (mirrors interpolate.h)
template<typename Config>
SC_MODULE(interpolate), public interpolateBase<Config> {
    SC_CTOR(interpolate) : interpolateBase<Config>(name()) {
        SC_THREAD(main_thread);
    }
    void main_thread();
};
```

**Key decision: `SC_CTOR` vs `SC_HAS_PROCESS`**

Current code uses `SC_HAS_PROCESS(interpolate)` in the `.cpp` file. The `SC_HAS_PROCESS` macro expands to `typedef interpolate SC_CURRENT_USER_MODULE;` — with templates this becomes `typedef interpolate<Config> SC_CURRENT_USER_MODULE;` which should work since it's inside the template class scope. However, `SC_HAS_PROCESS` takes a bare name, not `interpolate<Config>`. We need to test both patterns:

- **Pattern A**: `SC_CTOR` in the header (simpler, self-contained)
- **Pattern B**: `SC_HAS_PROCESS(interpolate)` in the `.cpp` with explicit template instantiation — tests whether the macro works with template classes

Both patterns must be tested. The prototype should implement Pattern B first (matches the existing code structure) and fall back to Pattern A if it fails.

For Pattern B, the `.cpp` would look like:
```cpp
template<typename Config>
void interpolate<Config>::main_thread() {
    // Simple passthrough: read bayer, write rgb
    while (true) {
        auto bayer = this->video_bayer_stream->read();
        video_rgb_t<Config> rgb;
        rgb.frame = bayer.frame;
        // ... simple conversion
        this->video_rgb_stream->write(rgb);
    }
}
```

Note: since `interpolate<Config>` is a template, the `.cpp` must either be `#include`-ed by consumers or use explicit template instantiation for each Config type. The prototype should test explicit instantiation:
```cpp
// interpolate.cpp
template class interpolate<config_8bpc>;
template class interpolate<config_12bpc>;
```

### `test/test_structs.cpp` — Config Coexistence (V4)

No SystemC simulation needed — pure C++ compile + run:

```cpp
#include "isp_types.h"
#include "debayer_configs.h"
#include <cassert>

int main() {
    // Verify distinct types
    static_assert(!std::is_same_v<rgb_pixel_t<config_8bpc>, rgb_pixel_t<config_12bpc>>);

    // Verify bitwidths
    static_assert(rgb_pixel_t<config_8bpc>::_bitWidth == 24);
    static_assert(rgb_pixel_t<config_12bpc>::_bitWidth == 36);

    // Pack/unpack roundtrip — 8bpc
    rgb_pixel_t<config_8bpc> p8{};
    p8.r = 0xAA; p8.g = 0xBB; p8.b = 0xCC;
    rgb_pixel_t<config_8bpc>::_packedSt packed8;
    p8.pack(packed8);
    rgb_pixel_t<config_8bpc> p8_rt{};
    p8_rt.unpack(packed8);
    assert(p8 == p8_rt);

    // Pack/unpack roundtrip — 12bpc
    rgb_pixel_t<config_12bpc> p12{};
    p12.r = 0xAAA; p12.g = 0xBBB; p12.b = 0xCCC;
    rgb_pixel_t<config_12bpc>::_packedSt packed12;
    p12.pack(packed12);
    rgb_pixel_t<config_12bpc> p12_rt{};
    p12_rt.unpack(packed12);
    assert(p12 == p12_rt);

    // Compound: video_bayer_t with array of parameterizable elements
    video_bayer_t<config_8bpc> vb8{};
    vb8.frame.sof = 1;
    vb8.data.pixels[0] = 42;
    video_bayer_t<config_8bpc>::_packedSt vb8_packed;
    vb8.pack(vb8_packed);
    video_bayer_t<config_8bpc> vb8_rt{};
    vb8_rt.unpack(vb8_packed);
    assert(vb8 == vb8_rt);

    // sc_bv roundtrip
    auto bv8 = p8.sc_pack();
    rgb_pixel_t<config_8bpc> p8_sc{};
    p8_sc.sc_unpack(bv8);
    assert(p8 == p8_sc);

    printf("PASS: All struct tests passed\n");
    return 0;
}
```

### `test/test_sc_module.cpp` — SystemC Block Test (V1/V2/V3)

Full SystemC simulation testbench:

```cpp
#include "systemc.h"
#include "interpolate.h"
#include "debayer_configs.h"

// Minimal testbench: source -> interpolate -> sink
template<typename Config>
SC_MODULE(testbench) {
    // Channels
    rdy_vld_channel< video_bayer_t<Config> > bayer_ch;
    rdy_vld_channel< video_rgb_t<Config> > rgb_ch;

    // DUT
    interpolate<Config> u_interp;

    SC_CTOR(testbench)
        : bayer_ch("bayer_ch")
        , rgb_ch("rgb_ch")
        , u_interp("u_interp")
    {
        // Bind
        u_interp.video_bayer_stream(bayer_ch);
        u_interp.video_rgb_stream(rgb_ch);

        SC_THREAD(stimulus);
        SC_THREAD(checker);
    }

    void stimulus() {
        video_bayer_t<Config> bayer{};
        bayer.frame.sof = 1;
        bayer.data.pixels[0] = 42;
        bayer_ch.write(bayer);
        // ... send a few more
    }

    void checker() {
        auto rgb = rgb_ch.read();
        // verify frame fields survived
        assert(rgb.frame.sof == 1);
        printf("PASS: SC_MODULE test passed\n");
        sc_stop();
    }
};

int sc_main(int argc, char* argv[]) {
    // V3: trace
    sc_trace_file *tf = sc_create_vcd_trace_file("trace");

    testbench<config_8bpc> tb("tb");

    // V3: trace a template struct signal
    // sc_trace(tf, tb.rgb_ch, "rgb_ch");  // test if this compiles

    sc_start();
    sc_close_vcd_trace_file(tf);
    return 0;
}
```

### `test/test_module_types.cpp` — Module Import Test (V5/V6)

```cpp
import isp;
#include "debayer_configs.h"
using namespace isp;

int main() {
    rgb_pixel_t<config_8bpc> p{};
    p.r = 100; p.g = 200; p.b = 50;
    static_assert(rgb_pixel_t<config_8bpc>::_bitWidth == 24);

    rgb_pixel_t<config_8bpc>::_packedSt packed;
    p.pack(packed);
    rgb_pixel_t<config_8bpc> p2{};
    p2.unpack(packed);
    assert(p == p2);

    printf("PASS: Module type import test passed\n");
    return 0;
}
```

### `test/test_module_block.cpp` — Module + SC_MODULE Test (V7)

This is the full target form — templated SC_MODULE exported from a module, imported and instantiated by consumer code running a SystemC simulation. Only attempt this if V1-V6 all pass.

## Makefile

Standalone Makefile using Clang (the project's default compiler). No arch2code or project build system dependencies.

```makefile
CXX = clang++
CXX_FLAGS = -std=c++23 -g -Wall -Wextra -pthread \
            -DSC_CPLUSPLUS=201703L -DSC_INCLUDE_DYNAMIC_PROCESSES
SC_INCLUDE = -I$(SYSTEMC_INCLUDE)
SC_LDFLAGS = -L$(SYSTEMC_LIBDIR) -lsystemc
INCLUDES = -Iconfigs -Itypes -Iblock -Iutil $(SC_INCLUDE)

BUILD = build

#--- Step 1: Pure C++ template validation (no SystemC link) ---

$(BUILD)/test_structs: test/test_structs.cpp types/isp_types.h configs/debayer_configs.h
	$(CXX) $(CXX_FLAGS) $(INCLUDES) $< -o $@ $(SC_LDFLAGS)

#--- Step 2: SystemC template SC_MODULE validation ---

$(BUILD)/test_sc_module: test/test_sc_module.cpp block/interpolate.h \
                         block/interpolate_base.h types/isp_types.h
	$(CXX) $(CXX_FLAGS) $(INCLUDES) $< -o $@ $(SC_LDFLAGS)

#--- Step 3: C++ module compilation (two-step) ---

# 3a: Compile module interface unit -> precompiled module
$(BUILD)/isp.pcm: types/isp_types.cppm
	@mkdir -p $(BUILD)
	$(CXX) $(CXX_FLAGS) $(SC_INCLUDE) -Iutil --precompile $< -o $@

# 3b: Compile module object (needed for linking)
$(BUILD)/isp_types.o: $(BUILD)/isp.pcm
	$(CXX) $(CXX_FLAGS) -c $< -o $@

# 3c: Consumer that imports the module
$(BUILD)/test_module_types: test/test_module_types.cpp $(BUILD)/isp.pcm $(BUILD)/isp_types.o
	$(CXX) $(CXX_FLAGS) -Iconfigs -fmodule-file=isp=$(BUILD)/isp.pcm \
	    $< $(BUILD)/isp_types.o -o $@ $(SC_LDFLAGS)

#--- Step 4: Full module + SC_MODULE validation ---

$(BUILD)/interpolate.pcm: block/interpolate.cppm $(BUILD)/isp.pcm
	$(CXX) $(CXX_FLAGS) $(SC_INCLUDE) -Iutil -Iconfigs \
	    -fmodule-file=isp=$(BUILD)/isp.pcm --precompile $< -o $@

$(BUILD)/interpolate.o: $(BUILD)/interpolate.pcm
	$(CXX) $(CXX_FLAGS) -c $< -o $@

$(BUILD)/test_module_block: test/test_module_block.cpp \
                            $(BUILD)/isp.pcm $(BUILD)/isp_types.o \
                            $(BUILD)/interpolate.pcm $(BUILD)/interpolate.o
	$(CXX) $(CXX_FLAGS) -Iconfigs \
	    -fmodule-file=isp=$(BUILD)/isp.pcm \
	    -fmodule-file=interpolate=$(BUILD)/interpolate.pcm \
	    $< $(BUILD)/isp_types.o $(BUILD)/interpolate.o -o $@ $(SC_LDFLAGS)

#--- Phony targets ---

.PHONY: step1 step2 step3 step4 all clean

step1: $(BUILD)/test_structs
	$(BUILD)/test_structs

step2: $(BUILD)/test_sc_module
	$(BUILD)/test_sc_module

step3: $(BUILD)/test_module_types
	$(BUILD)/test_module_types

step4: $(BUILD)/test_module_block
	$(BUILD)/test_module_block

all: step1 step2 step3 step4

clean:
	rm -rf $(BUILD)
```

Key Clang module flags:
- `--precompile`: Compile `.cppm` to `.pcm` (precompiled module interface)
- `-fmodule-file=<name>=<path>`: Tell the consumer where to find a named module
- The `.pcm` must also be compiled to `.o` for linking (contains non-inline definitions)

This Makefile serves as the specification for what `a2c-systemc.mk` will eventually need. The production build changes are deferred until after P0 validates the patterns.

## Implementation Order

| Step | Tests | Validates | Depends On | Effort |
|------|-------|-----------|------------|--------|
| **1** | `test_structs` | V4 — template structs with two Configs, pack/unpack, sc_bv | None | Small — pure C++ |
| **2** | `test_sc_module` | V1 — SC_MODULE with template, SC_HAS_PROCESS/SC_THREAD | Step 1 | Medium — SystemC linking, channel stubs |
| **2b** | (extend `test_sc_module`) | V2 — rdy_vld binding with template payload | Step 2 | Small — extends step 2 |
| **2c** | (extend `test_sc_module`) | V3 — sc_trace with template structs | Step 2 | Small — extends step 2 |
| **3** | `test_module_types` | V5/V6 — C++ module with SystemC header in global fragment, template export | Step 1 | Medium — module compilation |
| **4** | `test_module_block` | V7 — full pipeline: module + template + SC_MODULE | Steps 2, 3 | Large — everything combined |

**Stop early** if any step fails — record what failed and why. This is a validation prototype, not a feature delivery.

## Expected Outcomes and Fallback Decisions

| Outcome | Decision |
|---------|----------|
| V1-V4 pass, V5-V7 pass | Proceed with Option 4 (Foundation + Address, then combined Modules + Config Templates) |
| V1-V4 pass, V5-V7 fail (Clang) | Investigate the specific failure. Try GCC 13.1 as a secondary check. If both fail, proceed with Option 2 (Config Templates on headers). Revisit modules when toolchain matures. No wasted work — template content transfers to modules later. |
| V1-V3 pass, V4 fail (pack/unpack issues) | Fix the symbolic expression patterns before proceeding. Likely an expression error, not a fundamental blocker. |
| V1 fail (SC_MODULE + template) | Investigate the specific macro failure. Try `SC_CTOR` vs `SC_HAS_PROCESS`. If both fail, the Config template approach for block classes needs redesign (possibly wrapper classes instead of direct templating). |
| V2 fail (rdy_vld binding) | Investigate whether `rdy_vld_channel` requires concrete (non-template) types. If so, explicit instantiation or type erasure wrappers may be needed at interface boundaries. |

## Specific Risks and Mitigations

### `SC_HAS_PROCESS` with templates

`SC_HAS_PROCESS(interpolate)` expands to `typedef interpolate SC_CURRENT_USER_MODULE;`. Inside `template<typename Config> struct interpolate`, the bare name `interpolate` refers to `interpolate<Config>` (C++ injected class name), so this should work. But `SC_THREAD` uses `SC_CURRENT_USER_MODULE` for member function pointer casting — verify this resolves correctly.

**Mitigation**: If `SC_HAS_PROCESS` fails, use `SC_CTOR` (which embeds the process type internally) or use direct `sc_process_handle` registration.

### `sc_bv` with constexpr template argument

`sc_bv<rgb_pixel_t<Config>::_bitWidth>` requires that `_bitWidth` is usable as a template argument. Since `_bitWidth` is `static constexpr uint16_t` composed of `Config::` constexpr values, this should be a valid constant expression. Verify that the compiler evaluates it at compile time and doesn't emit a "not a constant expression" error.

### Module + SystemC macro interaction

SystemC 2.3.4's `systemc.h` uses macros extensively (`SC_MODULE`, `sc_signal`, etc.). In a module interface unit, macros from the global module fragment are visible to the module purview. The critical test: after `module; #include "systemc.h"; export module isp;`, can code in the module purview use `sc_trace()` and SystemC types normally?

### `sc_trace` with template friend functions

Current generated code uses `inline friend void sc_trace(sc_trace_file*, const T&, const std::string&)` inside structs. With templates, this becomes a friend of a template class. The SystemC trace infrastructure discovers `sc_trace` via ADL (argument-dependent lookup). Verify ADL finds the friend function for template struct instances.

## Success Deliverables

1. A working `proto/` directory with passing tests (or a clear record of what failed)
2. A summary of which patterns work, which don't, and any workarounds needed
3. A recommendation for which development ordering option to follow (Option 4 vs Option 2 fallback)
4. The POC Makefile — serves as the specification for what module compilation flags and rules `a2c-systemc.mk` will eventually need
5. Notes on any Clang-specific behavior or flags required beyond the standard

---

## Results

**Status: COMPLETE — All seven validations pass.**

Executed 2025-04-21 with Clang 20.1.8, SystemC 2.3.4, C++23. Full clean build + test run (`make clean && make all`) succeeds with zero errors.

### Validation Results

| ID | Risk | Result | Details |
|----|------|--------|---------|
| **V1** | `template<Config> SC_MODULE` with `SC_HAS_PROCESS` / `SC_THREAD` | **PASS** | Pattern B (SC_HAS_PROCESS in header, constructor + thread implementation in `.cpp`, explicit template instantiation) works correctly. `SC_HAS_PROCESS(interpolate)` resolves to `typedef interpolate<Config> SC_CURRENT_USER_MODULE` via injected class name as predicted. `SC_THREAD(main_thread)` correctly casts the member function pointer through `SC_CURRENT_USER_MODULE`. |
| **V2** | `rdy_vld` channel/port binding with template payload types | **PASS** | `rdy_vld_channel<video_bayer_t<Config>>` and `rdy_vld_channel<video_rgb_t<Config>>` bind correctly to `rdy_vld_in`/`rdy_vld_out` ports. Data transfers with full struct fidelity — all fields (frame metadata + pixel arrays) survive the write→channel→read roundtrip. |
| **V3** | `sc_trace` with template struct types | **PASS** | `inline friend void sc_trace(sc_trace_file*, const rgb_pixel_t<Config>&, const std::string&)` compiles inside template structs. ADL correctly discovers the friend function for template struct instances. Trace file infrastructure (create/close VCD) works alongside template blocks. |
| **V4** | Two Config structs coexisting — different `_bitWidth`, different `_packedSt` behavior | **PASS** | `rgb_pixel_t<config_8bpc>` (24-bit) and `rgb_pixel_t<config_12bpc>` (36-bit) are confirmed distinct types via `static_assert(!std::is_same_v<...>)`. Pack/unpack roundtrips verified for both configs. `sc_bv<_bitWidth>` roundtrips verified for both configs plus compound `video_bayer_t<config_8bpc>`. Constexpr `_bitWidth` composed from `Config::` values works as template arguments to `sc_bv`. |
| **V5** | C++20 module interface unit with SystemC in global module fragment | **PASS** | `module; #include "systemc.h"; export module isp;` compiles cleanly. All SystemC macros (`sc_trace`, `sc_bv`, `SC_MODULE`, etc.) from the global module fragment are visible in the module purview. No special flags beyond `--precompile` and `-fmodule-file=` required. |
| **V6** | Templated structs inside `export namespace` in a module | **PASS** | `template<typename Config> struct rgb_pixel_t` (and all other template types) exported from `export namespace isp { }` inside module `isp`. Consumer imports module, instantiates templates with concrete Config types, and uses pack/unpack/prt/operator== — all work. |
| **V7** | Templated SC_MODULE inside a module, imported by consumer, instantiated and run | **PASS** | Full pipeline validated: module `interpolate_mod` exports a `template<Config> SC_MODULE(interpolate)` with rdy_vld ports typed on `isp::video_bayer_t<Config>` and `isp::video_rgb_t<Config>` (imported from module `isp`). Consumer imports both modules, instantiates `testbench<config_8bpc>` containing `interpolate<config_8bpc>`, binds channels, runs SystemC simulation, and verifies data correctness through assertions. |

### Test Output

```
=== Step 1: Template struct validation (V4) ===
  8bpc rgb_pixel pack/unpack: OK
  12bpc rgb_pixel pack/unpack: OK
  8bpc video_bayer pack/unpack: OK
  8bpc rgb_pixel sc_bv roundtrip: OK
  12bpc rgb_pixel sc_bv roundtrip: OK
  8bpc video_bayer sc_bv roundtrip: OK
PASS: All struct tests passed

=== Step 2: Template SC_MODULE validation (V1/V2/V3) ===
  Stimulus: sending bayer frame: frame:<eol:0x0 sof:0x1 eof:0x0> data:<pixels:[0x2a,0x64,0xc8,0xff]>
  Checker: received rgb frame: frame:<eol:0x0 sof:0x1 eof:0x0> data:<rgb_pixels:[{r:0x2a g:0x2a b:0x2a}, ...]>
PASS: SC_MODULE test passed (V1/V2)

=== Step 3: C++20 module type import (V5/V6) ===
PASS: Module type import test passed (V5/V6)

=== Step 4: Full module + SC_MODULE (V7) ===
PASS: Module block test passed (V7)
```

### Findings and Notes

#### What worked exactly as predicted

1. **SC_HAS_PROCESS injected class name** — The prediction in "Specific Risks and Mitigations" was correct: `SC_HAS_PROCESS(interpolate)` inside `template<typename Config> struct interpolate` expands to `typedef interpolate SC_CURRENT_USER_MODULE;`, which resolves to `typedef interpolate<Config> SC_CURRENT_USER_MODULE;` via C++ injected class name rules. `SC_THREAD` then correctly uses this typedef for member function pointer registration. No fallback to `SC_CTOR` or `sc_process_handle` was needed.

2. **`sc_bv<_bitWidth>` with constexpr template argument** — `sc_bv<rgb_pixel_t<Config>::_bitWidth>` works as a return type, parameter type, and in range() operations. The compiler evaluates the constexpr chain (`Config::BITS_PER_PIXEL_COLOR` → `_bitWidth` → template argument) at compile time with no issues.

3. **Module + SystemC macro interaction** — Macros defined by `systemc.h` in the global module fragment (`SC_MODULE`, `SC_HAS_PROCESS`, `SC_THREAD`, `SC_CTOR`, `SC_ZERO_TIME`, etc.) are all visible in the module purview. `sc_trace()`, `sc_bv`, `sc_prim_channel`, and all other SystemC types work normally inside `export namespace`.

4. **ADL for template friend functions** — `inline friend void sc_trace(...)` inside template structs works correctly. ADL discovers the friend function for concrete instantiations like `rgb_pixel_t<config_8bpc>`.

#### Issues encountered and resolved during implementation

1. **Explicit instantiation: `struct` vs `class`** — `SC_MODULE(interpolate)` expands to `struct interpolate : public sc_module`, so explicit instantiation must use `template struct interpolate<config_8bpc>;` (not `template class`). Using `class` triggers `-Wmismatched-tags`. This is a minor generator concern — the explicit instantiation keyword must match the `SC_MODULE` expansion.

2. **`rdy_vld_channel` namespace ambiguity** — When the channel class is defined inside `namespace sc_core` (matching the real code) and a global `using` alias is also provided, the combination with `using namespace sc_core` from `systemc.h` creates an ambiguous name lookup. Resolution: the global `using` alias is unnecessary because `using namespace sc_core` already makes the class accessible. The production code avoids this because it doesn't have both. For generated code, either define the channel outside `sc_core` or rely on the `using namespace` import — don't create a redundant alias.

3. **Dependent module `.pcm` → `.o` compilation** — When compiling `interpolate_mod.pcm` to `interpolate_mod.o`, the compiler needs `-fmodule-file=isp=build/isp.pcm` even though the `.pcm` already contains the resolved module dependency. Without this flag, Clang emits `error: failed to find module file for module 'isp'`. This is a Clang implementation requirement — module file paths are not embedded in `.pcm` files. The production build system must propagate `-fmodule-file=` flags to all compilation steps, not just the `--precompile` step.

4. **`_packedSt` sizing for large types** — `typedef uint64_t _packedSt` works for types where `_bitWidth ≤ 64` (rgb_pixel_t, bayer_pixels_per_clock_t at 8bpc/4ppc, video_bayer_t at 8bpc/4ppc). For larger types like `rgb_pixels_per_clock_t` (96 bits at 8bpc/4ppc) and `video_rgb_t` (99 bits at 8bpc/4ppc), a single `uint64_t` is insufficient. The prototype uses `uint64_t _packedSt` for all types, with pack/unpack only correct for `_bitWidth ≤ 64`. Production generators will need to compute the `_packedSt` size: either `uint64_t` for small types or `uint64_t[(_bitWidth + 63) / 64]` for larger ones, using `pack_bits()` for multi-word operations. This is a generator output concern, not a template/module compatibility issue — the POC confirms the constexpr-dependent array sizing `uint64_t[(_bitWidth + 63) / 64]` compiles correctly.

#### Clang-specific flags required

| Flag | Purpose | When needed |
|------|---------|-------------|
| `--precompile` | Compile `.cppm` → `.pcm` (precompiled module interface) | Module interface compilation only |
| `-fmodule-file=<name>=<path>` | Tell compiler where to find a named module | Any compilation that depends on a module (both `--precompile` of dependent modules AND `.pcm` → `.o` compilation AND consumer `.cpp` compilation) |
| `-DSC_CPLUSPLUS=201703L` | Override SystemC's C++ standard detection | All SystemC compilations (existing requirement) |
| `-DSC_INCLUDE_DYNAMIC_PROCESSES` | Enable `SC_THREAD` in non-constructor contexts | All SystemC compilations (existing requirement) |

No additional flags were needed beyond the standard project flags (`-std=c++23`, `-g`, `-Wall`, `-Wextra`, `-pthread`).

#### Compilation model for `a2c-systemc.mk`

The POC Makefile documents the three-step module compilation process that must be added to the production build system:

```makefile
# Step 1: .cppm → .pcm (precompile module interface)
build/isp.pcm: types/isp_types.cppm
	$(CXX) $(CXX_FLAGS) $(SC_INCLUDE) -Iutil --precompile $< -o $@

# Step 2: .pcm → .o (compile module object for linking)
# NOTE: Must pass -fmodule-file= for ALL imported modules
build/isp_types.o: build/isp.pcm
	$(CXX) $(CXX_FLAGS) -c $< -o $@

# Step 3: Consumer compilation (pass module references)
build/consumer.o: consumer.cpp build/isp.pcm
	$(CXX) $(CXX_FLAGS) -fmodule-file=isp=build/isp.pcm -c $< -o $@
```

For modules that import other modules, the dependency chain must be fully specified:
```makefile
build/interpolate_mod.pcm: block/interpolate.cppm build/isp.pcm
	$(CXX) $(CXX_FLAGS) -fmodule-file=isp=build/isp.pcm --precompile $< -o $@

build/interpolate_mod.o: build/interpolate_mod.pcm build/isp.pcm
	$(CXX) $(CXX_FLAGS) -fmodule-file=isp=build/isp.pcm -c $< -o $@
```

## Conclusion

**Recommendation: Proceed with Option 4** (Foundation + Address, then combined Modules + Config Templates).

All seven risks have been validated. The target code form — Config-templated structs and SC_MODULE blocks inside C++20 module interface units — compiles, links, and runs correctly with the project's exact toolchain (Clang 20.1.8, SystemC 2.3.4, C++23). No fundamental blockers were found. The issues encountered (explicit instantiation keyword, namespace aliasing, module file flag propagation) are minor and have straightforward solutions for the generators and build system.
