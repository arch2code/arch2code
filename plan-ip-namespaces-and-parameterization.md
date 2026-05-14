# IP Support in arch2code: Namespaces, Parameterization, and C++ Modules

## 1. Problem Statement

arch2code needs to support reusable IP blocks that can be:
- **Shared across projects** — multiple IPs coexisting in a design without name collisions
- **Configured per instance** — the same IP instantiated multiple times with different parameters, where the **generated IP source code is text-stable** (unchanged) but compiles differently per configuration

Two interrelated problems must be solved, with a third enabler under consideration:

| Problem | Core Issue |
|---------|-----------|
| **Namespaces** | All C++ types/constants/structures live in the global namespace. Two IPs defining `pixel_t`, or the same IP instantiated twice, cause ODR violations or link-time collisions. SystemVerilog has natural package scoping but lacks a formalized IP-level namespace concept in the YAML schema. |
| **IP Parameters** | Constants resolve at generation time to literal values (`const uint32_t BITS_PER_PIXEL_COLOR = 8` / `localparam int unsigned BITS_PER_PIXEL_COLOR = 32'h0000_0008`). Changing a parameter requires regenerating the IP, and you can't have two instances with different values in the same design. |
| **C++ Modules** | C++20 modules offer compilation-unit isolation and explicit export semantics similar to SystemVerilog packages. Adopting them could simplify the namespace/parameterization story and unify the C++ and SV mental models. |

### Scenarios to Support

**Scenario A — Different IPs, shared types:** A design uses `debayer` IP and `encoder` IP. Both include `isp_types.yaml` which defines `pixel_t`, `video_frame_t`, etc. Both IPs need these types to be identical and interoperable at interfaces.

**Scenario B — Same IP, multiple instances with different parameters:** Two instances of the `debayer` IP in one design: one configured with `BITS_PER_PIXEL_COLOR=8, PIXELS_PER_CLOCK=4` and another with `BITS_PER_PIXEL_COLOR=12, PIXELS_PER_CLOCK=8`. The generated debayer source code must be identical for both; only the parameter values differ.

**Scenario C — Name collision of unrelated definitions:** Two unrelated IPs independently define a type with the same name (e.g., both define `status_t` or `config_reg_t`). These are semantically different types that happen to share a name. Namespaces must prevent collision without requiring either IP to rename.

---

## 2. Current State

### 2.1 What Exists Today

| Mechanism | Scope | How it works |
|-----------|-------|-------------|
| **Block variants** (`parameters:` YAML section) | Block instances | Predefined constant sets per variant; selects between fixed values at generation time. SV: module parameter overrides. C++: `instanceFactory::getParam()`. |
| **`_context` field** | Validation | Every DB record carries its source YAML context. Used for scoped validation lookups. Not used for code-gen scoping. |
| **`include:` mechanism** | File composition | Additive inclusion — all definitions from included files become globally visible. No selective import/export. |
| **`--namespace` CLI arg** | FW headers only | Wraps firmware include files in `namespace fw_ns {}`. Not used for model/simulation code. |
| **SV packages** | RTL | Natural namespace scoping via `isp_types_package`, `debayer_package`. Already working but with flat `import ... ::*` patterns. |

### 2.2 Current Generated Code Patterns

**C++ (model/simulation):**
- Constants: `const uint32_t BITS_PER_PIXEL_COLOR = 8;` — global scope, **resolved value** (not text-stable)
- Types: `typedef uint8_t pixel_t;` — global scope, **resolved to platform C type based on numeric width** (not text-stable)
- Enums: `enum bayer_pattern_t { RGGB=0, BGGR=1, ... };` — global scope, unscoped enumerators pollute global namespace
- Array dimensions: `pixel_t pixels[PIXELS_PER_CLOCK];` — **already symbolic** (references constant name)
- Struct `_bitWidth`: **already fully symbolic** — uses constant names, `clog2()` calls, and sub-struct `::_bitWidth` references (see below)
- `_packedSt` type: `typedef uint32_t _packedSt;` — **resolved based on numeric bitwidth** (not text-stable)
- Pack/unpack methods: use **resolved numeric** shifts and masks (not text-stable)

**C++ `_bitWidth` is already fully symbolic.** The code generators (`structBitWidthExpression_cpp` in `structures.py`, `typeWidthExpression_cpp` in `includes.py`) produce `static constexpr` expressions that preserve symbolic references — literal widths, constant references, `clog2()` calls, sub-struct `::_bitWidth` references, and signed variants. These compose with array multipliers and multi-field addition. The C++ `clog2()` is a `constexpr` function in `bitTwiddling.h` that mirrors SV's `$clog2()` exactly.

**SystemVerilog (RTL):**
- Constants: `localparam int unsigned BITS_PER_PIXEL_COLOR = 32'h0000_0008;` — **resolved value** inside package (not text-stable)
- Types: `typedef logic[BITS_PER_PIXEL_COLOR-1:0] pixel_t;` — **already symbolic** (references constant name)
- Types with log2: `typedef logic[$clog2(BSIZE+1)-1:0] bSizeCountT;` — **already symbolic** (uses `$clog2()`)
- Structs: `typedef struct packed { pixel_t [PIXELS_PER_CLOCK-1:0] pixels; }` — **already symbolic** (member types carry symbolic widths)
- Packages scope all definitions; modules use `import debayer_package::*;`

Both C++ and SV are already substantially text-stable for structure definitions, type widths, and array dimensions. The remaining gaps are:

| Element | C++ | SV |
|---------|-----|-----|
| Constant values | **Gap** — resolved to literals | **Gap** — resolved to literals |
| `typedef` / type alias | **Gap** — resolved to platform C type (`uint8_t`) | Already symbolic (`logic[CONST-1:0]`) |
| `_bitWidth` / struct sizing | Already symbolic | N/A (implicit in packed struct) |
| Array dimensions | Already symbolic | Already symbolic |
| `_packedSt` type | **Gap** — resolved based on bitwidth | N/A |
| Pack/unpack masks/shifts | **Gap** — resolved numeric expressions | N/A (native struct assignment) |

### 2.3 What Does NOT Exist

- No YAML-level namespace concept for IPs or type collections
- No IP packaging/boundary mechanism
- No type parameterization (C++ constants resolve to literals)
- No selective import/export controls
- No way to compile the same IP code against different parameter sets
- No multi-project or sub-project support
- No C++ module support

---

## 3. Issue 1: Namespaces

Namespaces must handle two distinct sub-problems:

1. **Shared definitions** — types that multiple IPs agree on and must be identical (e.g., `isp::pixel_t` used by both debayer and encoder)
2. **Collision avoidance** — types that happen to share a name but are semantically different (e.g., `debayer::config_reg_t` vs. `encoder::config_reg_t`)

A single namespace mechanism should address both: shared definitions live in a shared namespace that both IPs import; IP-specific definitions live in IP-scoped namespaces that don't interfere.

### 3.1 Design Options

#### Option N1 — Explicit YAML namespace per context file

Each YAML file declares a namespace:
```yaml
# isp_types.yaml
namespace: isp
constants:
  BITS_PER_PIXEL_COLOR: {value: 8, desc: "..."}
types:
  pixel_t: {width: BITS_PER_PIXEL_COLOR, desc: "..."}
```

**Generated C++:**
```cpp
namespace isp {
    const uint32_t BITS_PER_PIXEL_COLOR = 8;
    typedef uint8_t pixel_t;
    struct video_frame_t { ... };
}
```

**Generated SV** (already scoped, but namespace could formalize naming):
```systemverilog
package isp_package;
    localparam int unsigned BITS_PER_PIXEL_COLOR = ...;
    typedef logic[BITS_PER_PIXEL_COLOR-1:0] pixel_t;
endpackage
```

**Consumer YAML** uses `include:` and the included namespace is available:
```yaml
# debayer.yaml
namespace: debayer
include:
  - isp_types.yaml     # brings isp:: namespace into scope
```

| Pro | Con |
|-----|-----|
| Explicit, clear scoping | Hand-written code needs `using namespace` or qualification |
| Handles both shared-definition and collision scenarios | Requires migration of existing projects |
| Maps to existing `--namespace` infrastructure | Namespace hierarchy design needs careful thought |
| Natural parallel to SV packages | |

#### Option N2 — Auto-derived namespace from file/project name

Namespace derived from YAML file name: `isp_types.yaml` → `namespace isp_types`.

| Pro | Con |
|-----|-----|
| Zero additional annotation | Less control, file renames change namespace |
| Predictable | Can't share namespace across multiple files easily |

#### Option N3 — IP-level namespace with shared imports

Each IP project declares its namespace in `project.yaml`. Shared type files declare their own namespace. IPs import shared namespaces:

```yaml
# debayer project.yaml
ip:
  namespace: debayer
  imports:
    - {namespace: isp, from: ../shared/isp_types.yaml}
```

Types in `isp_types.yaml` live in `isp::`, types in `debayer.yaml` live in `debayer::`. The debayer IP code can reference `isp::pixel_t` or use a `using namespace isp;` equivalent.

| Pro | Con |
|-----|-----|
| Models the real IP dependency graph | More schema complexity |
| Shared types guaranteed compatible | Requires explicit import declarations |
| Clear IP boundary | |

### 3.2 Cross-Language Namespace Mapping

A key design goal is that the namespace concept maps naturally to both C++ and SystemVerilog:

| YAML | C++ (current) | C++ (with namespaces) | C++ (with modules) | SystemVerilog |
|------|--------------|----------------------|--------------------|--------------| 
| `namespace: isp` | global scope | `namespace isp { ... }` | `export module isp;` with `export namespace isp { ... }` | `package isp_package; ... endpackage` |
| `include: [isp_types.yaml]` | `#include "isp_typesIncludes.h"` | `using namespace isp;` or qualified | `import isp; using namespace isp;` | `import isp_package::*;` |
| No namespace | global scope | global scope (backward compat) | N/A | current package behavior |

**Note:** C++20 module names and C++ namespaces are orthogonal — `import isp;` does not automatically create an `isp::` scope. To get SV-like package scoping, the module interface unit must explicitly wrap exports in `namespace isp { ... }`. With this convention, the SV `import pkg::*` and C++ `import module; using namespace ns;` patterns become structurally similar. This is explored further in Section 6.

### 3.3 Enum Scoping

C++ enums are particularly collision-prone. Currently enumerator names like `RGGB`, `BGGR` leak into whatever scope contains the enum. Two IPs with an enum value named `IDLE` would collide.

**With C++ namespaces:** The namespace wrapping solves this — `isp::RGGB` vs. `other_ip::RGGB` are distinct.

**With C++ modules:** Module-exported enums scoped via the namespace convention (see Section 6.4) work the same way.

**With C++11 `enum class`:** Provides the strongest isolation (`bayer_pattern_t::RGGB`) but requires all existing code to change access patterns. Not strictly required if namespaces/modules are adopted.

**Recommendation:** Namespaces (or modules) provide sufficient enum scoping. Consider `enum class` as an optional future refinement.

### 3.4 Recommendation

Start with **Option N1 (explicit namespace)** as the base mechanism. This is the simplest change, maps to both C++ namespaces and SV packages, and handles both shared-definition and collision scenarios. Option N3 concepts (IP-level namespace with imports) should be the target for the IP packaging phase.

This is a **breaking change** — existing projects will need to be updated. A migration path should be provided (e.g., a tool or make target that adds `namespace:` declarations to existing YAML files and `using namespace` directives to existing C++ code).

---

## 4. Issue 2: IP Parameters

### 4.1 The Goal: Text-Stable Generated Code

The generated IP source code (both C++ and SV) must be invariant to parameter values. The same source files work for `BITS_PER_PIXEL_COLOR=8` and `BITS_PER_PIXEL_COLOR=12`. Different configurations change behavior only at compile time.

As detailed in Section 2.2, SV type widths and array dimensions are already symbolic, while C++ has remaining gaps in constant values, `typedef` type selection, `_packedSt`, and pack/unpack methods. The `_bitWidth` symbolic expression infrastructure is already complete. The remaining work to achieve text-stability is concentrated in:

- C++ constant declarations — must not contain resolved values
- C++ `typedef` — must not resolve to a specific C++ integer type based on width
- C++ `_packedSt` type selection — must use worst-case sizing instead of resolved bitwidth
- C++ pack/unpack bit manipulation — must use symbolic expressions for masks and shifts
- SV `localparam` declarations — must not contain resolved values

### 4.2 Design Options

#### Option P1 — ipParameters + Symbolic Expressions (Existing Plan)

As described in `plan-parameterizableTypesAndStructs.prompt.md`:
- New `ipParameters` YAML section declares parameterizable constants/types with `maxBitwidth`/`maxValue`
- `isParameterizable` flag propagates transitively through types → structures → array sizes
- C++ generation uses symbolic constant names instead of resolved values
- Force `uint64_t` for parameterizable types regardless of actual width
- Address space uses `maxBitwidth`/`maxValue` for worst-case allocation
- `maxBitwidth` violation is a **runtime error** (assertion in the IP code)

**Existing foundation:** A significant portion of the symbolic expression work described in P1 is already implemented. The `_bitWidth` expressions, array dimensions, and SV type widths already use symbolic constant references and `clog2()`/`$clog2()` calls. The remaining P1 work is concentrated in:
1. Constant declaration values (C++ and SV) — currently resolved to literals
2. C++ `typedef` type selection — currently resolved to platform types like `uint8_t`
3. C++ `_packedSt` type — currently resolved based on computed bitwidth
4. C++ pack/unpack mask and shift expressions — currently resolved numeric values
5. The `ipParameters` schema section and transitive propagation pass — new

| Pro | Con |
|-----|-----|
| Detailed plan already exists | Complex transitive propagation logic |
| Much of the symbolic infrastructure is already built | Forcing `uint64_t` is a blunt instrument |
| Text-stable output (primary goal) | Doesn't directly address how different instances get different values |
| Address space correctness via max values | |

This plan makes generated code text-stable but doesn't specify how different instances receive different parameter values — see the Config template approach in Section 4.6.

#### Option P2 — Config Policy Template

Each parameterizable type/struct/block becomes a C++ template parameterized on a single `typename Config` policy struct. The Config struct contains all IP parameters as `static constexpr` members. The consuming project generates one Config struct per IP instance.

This approach:
1. IP code is generated with **Config template parameterization** (text-stable)
2. Each IP instance is represented by a **Config struct** with concrete parameter values
3. `maxBitwidth`/`maxValue` are used for worst-case address-space sizing
4. `maxBitwidth` violations produce a **runtime error** (or `static_assert` where possible)

| Pro | Con |
|-----|-----|
| No injection mechanism — parameterization flows through the type system | Every parameterizable struct/class becomes a template |
| Parallels SV module parameters naturally | Hand-written code uses `Config::` prefixes |
| Standard C++ pattern (well understood by compilers, tools, IDEs) | Template method implementations must be in headers |
| Single compilation — templates instantiated at point of use | SystemC macro compatibility needs validation |
| Adding a new IP parameter only changes Config struct | Code generation templates become more complex |

### 4.3 SV Parameterization Considerations

SystemVerilog has richer native parameterization than C++:

**Current SV state:** Constants are `localparam` inside packages. Type widths already reference constant names symbolically (`logic[BITS_PER_PIXEL_COLOR-1:0]`). The main gap is that `localparam` values are resolved at generation time.

**Options for SV parameterization:**

| Approach | Mechanism | Trade-off |
|----------|-----------|-----------|
| **Parameterized packages** (SV-2012) | `package isp_package #(parameter BITS_PER_PIXEL_COLOR=8)` | Closest to ideal; limited EDA tool support |
| **Module-level parameters** | Move IP constants from package `localparam` to module `parameter` declarations, passed through hierarchy | Well-supported; but types in packages can't depend on module parameters |
| **Separate packages per instance** | Generate `debayer_8bpc_package` and `debayer_12bpc_package` with different `localparam` values | Simple; IP module source must be parameterized on which package to import |
| **Generate blocks** | Use SV `generate` with parameter-dependent type selection | Complex; limited applicability |

**The separate-packages approach** is the SV equivalent of the C++ Config template pattern: each IP instance gets its own package with its own constant values. The IP's module source uses symbolic references and is elaborated against the correct package. The SV module uses `parameter` declarations that the consuming hierarchy overrides, paralleling how the C++ consuming project provides Config structs.

**Open question:** The best SV approach depends on EDA tool support and the complexity of the type dependency chain. This should remain open for prototyping.

### 4.4 YAML-Level Override Mechanism

The consuming project specifies IP parameters in YAML:
```yaml
ipInstances:
  u_debayer_hd:
    ipProject: ./ips/debayer
    parameters:
      BITS_PER_PIXEL_COLOR: 8
      PIXELS_PER_CLOCK: 4
  u_debayer_uhd:
    ipProject: ./ips/debayer
    parameters:
      BITS_PER_PIXEL_COLOR: 12
      PIXELS_PER_CLOCK: 8
```

arch2code:
- Validates all declared `ipParameters` are provided
- Validates values don't exceed `maxBitwidth`/`maxValue` (generation-time check)
- Generates per-instance Config structs (C++) and packages (SV)
- The IP itself asserts `maxBitwidth`/`maxValue` at **runtime** as a secondary safety net

### 4.5 Recommendation

**Option P2 (Config policy template)** combined with the symbolic expression foundation from P1. The `ipParameters` schema section and `maxBitwidth`/`maxValue` constraints from P1 provide the YAML-level infrastructure. The Config template pattern from P2 provides the C++ mechanism for multi-instance parameterization. Symbolic `_bitWidth` expressions (already implemented) and symbolic pack/unpack (to be implemented) make the generated template code text-stable. See Section 4.6 for the full C++ design.

### 4.6 C++ Parameterization: Config Policy Template Approach

#### The Problem

Consider `rgb_pixel_t` which contains three `pixel_t` fields where `pixel_t`'s width depends on `BITS_PER_PIXEL_COLOR`. If the design has two debayer instances with different `BITS_PER_PIXEL_COLOR` values, we need two structurally different versions of `rgb_pixel_t` to coexist in the same program. C++ requires that a type have exactly one definition per scope (ODR), so these must be different types.

Today's IP block code uses unqualified names:

```cpp
// interpolate.h (IP code)
#include "debayerIncludes.h"    // brings in rgb_pixel_t, pixel_t, etc.
SC_MODULE(interpolate) { ... };

// interpolate.cpp (IP code)
#include "interpolate.h"
void interpolate::processPixel() {
    rgb_pixel_t pixel;           // which rgb_pixel_t?
}
```

For multiple parameterizations to coexist, the types themselves must carry their parameter identity. C++ templates are the natural mechanism for this — the parameterization is embedded in the type system, no external injection or per-instance compilation orchestration is needed.

**Why not namespaces/modules?** The alternative of placing each IP instance in a separate namespace/module was considered and rejected. It requires an injection mechanism — each block source file must somehow be told which namespace it belongs to (via build-system macro, generated wrapper, or generated preamble line). Every source file must be compiled once per instance, with separate object files managed by the build system. The injection is inherently fragile and doesn't parallel how SystemVerilog's *native* parameterization works (SV uses module parameters, not per-instance packages). Note: Section 4.3 does list separate per-instance packages as a viable SV *implementation strategy*, but this is distinct from using namespaces as the C++ parameterization mechanism — the SV packages would carry constant values analogous to Config structs, not act as the parameterization mechanism itself.

#### The Config Policy Pattern

Instead of individual template parameters on each struct (which would cause transitive parameter-list explosion), all IP parameters are collected into a single **Config policy struct**:

```cpp
// Generated per-instance by consuming project:
struct debayer_8bpc_config {
    static constexpr uint32_t BITS_PER_PIXEL_COLOR = 8;
    static constexpr uint32_t PIXELS_PER_CLOCK = 4;
    static constexpr uint32_t MAX_PIXEL_VALUE = 255;
    // ... all IP parameters as static constexpr members
};
struct debayer_12bpc_config {
    static constexpr uint32_t BITS_PER_PIXEL_COLOR = 12;
    static constexpr uint32_t PIXELS_PER_CLOCK = 8;
    static constexpr uint32_t MAX_PIXEL_VALUE = 4095;
};
```

Every parameterized type, struct, and block class in the IP takes a single `typename Config` template parameter:

```cpp
// IP types (text-stable, parameterized on Config):
template<typename Config>
using pixel_t = uint64_t;  // Config unused here — templated for type-graph consistency
                            // so that pixel_t<Config> propagates uniformly through structs

template<typename Config>
struct rgb_pixel_t {
    pixel_t<Config> r, g, b;
    static constexpr uint16_t _bitWidth =
        Config::BITS_PER_PIXEL_COLOR + Config::BITS_PER_PIXEL_COLOR
        + Config::BITS_PER_PIXEL_COLOR;
    static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;
    using _packedSt = uint64_t;  // fixed max-size; see "Underlying C++ Type Strategy"
    // pack/unpack use Config::BITS_PER_PIXEL_COLOR symbolically
    void pack(_packedSt &_ret) const;
    void unpack(const _packedSt &_src);
    // ...
};

template<typename Config>
struct rgb_pixels_per_clock_t {
    rgb_pixel_t<Config> pixels[Config::PIXELS_PER_CLOCK];
    static constexpr uint16_t _bitWidth =
        rgb_pixel_t<Config>::_bitWidth * Config::PIXELS_PER_CLOCK;
    // ...
};

template<typename Config>
struct video_rgb_t {
    video_frame_t frame;  // non-parameterized — no template
    rgb_pixels_per_clock_t<Config> data;
    static constexpr uint16_t _bitWidth =
        video_frame_t::_bitWidth + rgb_pixels_per_clock_t<Config>::_bitWidth;
    // ...
};
```

Key points:
- Adding a new IP parameter only changes the Config struct, not every template signature
- Non-parameterized types (`video_frame_t`) remain plain structs — no template overhead
- `_bitWidth` expressions reference `Config::CONSTANT_NAME` instead of bare constant names
- `_packedSt` uses constexpr type selection based on the symbolic `_bitWidth`

#### Block Class Parameterization

The block class and its generated base class are also templated:

```cpp
// interpolateBase.h (generated, text-stable):
template<typename Config>
class interpolateBase : public virtual blockPortBase {
public:
    rdy_vld_out< video_rgb_t<Config> > video_rgb_stream;
    rdy_vld_in< bayer_preprocess_stream_t<Config> > bayer_preprocess_stream;
    // ...
};

// interpolate.h (IP code, text-stable):
template<typename Config>
SC_MODULE(interpolate), public blockBase, public interpolateBase<Config> {
    void processPixel();
    // ...
};

// interpolate.cpp (IP code, text-stable):
template<typename Config>
void interpolate<Config>::processPixel() {
    rgb_pixel_t<Config> pixel;    // type resolved from Config
    pixel.r = some_value;
}
```

The consuming project instantiates with concrete configs:

```cpp
interpolate<debayer_8bpc_config> u_interp_hd;    // 8-bit pixels
interpolate<debayer_12bpc_config> u_interp_uhd;   // 12-bit pixels
```

#### Making Pack/Unpack Text-Stable

Pack/unpack methods use `Config::` references for field widths and cumulative positions:

```cpp
// Text-stable pack (template member function):
template<typename Config>
void rgb_pixel_t<Config>::pack(_packedSt &_ret) const {
    _ret = r;
    _ret |= (_packedSt)g << (Config::BITS_PER_PIXEL_COLOR & _baseMask);
    _ret |= (_packedSt)b << ((2 * Config::BITS_PER_PIXEL_COLOR) & _baseMask);
}

// Text-stable unpack:
template<typename Config>
void rgb_pixel_t<Config>::unpack(const _packedSt &_src) {
    uint16_t _pos{0};
    r = (pixel_t<Config>)((_src >> (_pos & _baseMask))
        & ((1ULL << Config::BITS_PER_PIXEL_COLOR) - 1));
    _pos += Config::BITS_PER_PIXEL_COLOR;
    g = (pixel_t<Config>)((_src >> (_pos & _baseMask))
        & ((1ULL << Config::BITS_PER_PIXEL_COLOR) - 1));
    _pos += Config::BITS_PER_PIXEL_COLOR;
    b = (pixel_t<Config>)((_src >> (_pos & _baseMask))
        & ((1ULL << Config::BITS_PER_PIXEL_COLOR) - 1));
}
```

For structs with mixed parameterized and non-parameterized fields, cumulative positions use `_bitWidth` references:

```cpp
// video_bayer_t: frame (3-bit, non-param) + data (param)
_ret |= data_packed << (video_frame_t::_bitWidth & _baseMask);
```

For arrays, the existing `pack_bits()` / `_pos` runtime tracking pattern works with `Config::` references — the loop bound (`Config::PIXELS_PER_CLOCK`) and element width (`Config::BITS_PER_PIXEL_COLOR`) are constexpr.

#### Template Method Implementations: Header-Only Requirement

A practical consequence of templates: pack/unpack method implementations (currently in `*Includes.cpp` files) must move to header files. C++ requires template definitions to be visible at the point of instantiation. The generated `*Includes.h` file would contain both the struct declaration and method definitions (either inline or in a separate `*Includes_impl.h`).

This is a change from the current pattern where struct declarations are in `.h` and method implementations in `.cpp`. For template structs, everything must be in headers. This is standard C++ practice for template libraries and doesn't cause correctness issues, but it changes the generated file structure.

#### Underlying C++ Type Strategy: Fixed Max-Size vs. `conditional_t`

The system is already designed for C++ storage types to be wider than HW types (e.g., `eol_t` is 1 HW bit stored in `uint8_t`). `_bitWidth`/`_byteWidth` represent HW dimensions; `sizeof(T)` represents C++ dimensions; pack/unpack bridges between the two. Widening `pixel_t` from `uint8_t` to `uint64_t` follows the same principle — pack/unpack uses `_bitWidth`-derived positions and masks regardless of C++ storage width.

With a wider `pixel_t`, existing `(pixel_t)` casts in model code no longer truncate. If truncation to HW width is needed, models should explicitly mask (e.g., `& MAX_PIXEL_VALUE`). Missing masks will surface in tandem testing since RTL naturally truncates at the correct bit width.

**Decision: Use fixed `uint64_t` for all parameterizable types.** This applies to both named member types (`pixel_t`, etc.) and `_packedSt`:

| Element | Strategy | Rationale |
|---------|----------|-----------|
| Named member types (`pixel_t`, etc.) | Fixed `uint64_t` for parameterizable types | C++ storage width is independent of HW width by design; `_bitWidth`/`_byteWidth` handle HW dimensions; eliminates `conditional_t` complexity |
| `_packedSt` | Fixed `uint64_t` (or `uint64_t[N]` for >64 bits) | Simplifies pack/unpack generation; `_byteWidth` defines the valid HW footprint within the wider type |
| `_bitWidth` / `_byteWidth` | Already symbolic constexpr | No change needed — these represent HW dimensions, not C++ storage |
| Non-parameterizable types | Keep current width-matched types (`uint8_t`, etc.) | No reason to change types that don't vary |

The pack function clears `_byteWidth` bytes and populates exactly the HW-significant bits; bytes beyond `_byteWidth` in the wider `uint64_t` are left as garbage by design. The shift mask (`& 63` for `uint64_t`) is the only generator change needed. Memory overhead is acceptable for simulation (e.g., `pixel_t pixels[4]` grows from 4 to 32 bytes for 8bpc).

#### SystemC Compatibility

`SC_MODULE` expands to `struct name : public sc_module`. A templated module:

```cpp
template<typename Config>
SC_MODULE(interpolate) { ... };
```

expands to:

```cpp
template<typename Config>
struct interpolate : public sc_module { ... };
```

This is valid C++. However, `SC_THREAD` and `SC_METHOD` macros register member function pointers for the SystemC kernel's scheduler. With templates, the member function type depends on the template parameter. This typically works because SystemC uses `SC_CURRENT_USER_MODULE` to capture the correct type, but **this needs prototype validation** — particularly for:
- `SC_THREAD`/`SC_METHOD` registration with template classes
- `sc_trace` with template struct types
- SystemC signal/channel binding with template-parameterized port types
- `instanceFactory` registration (currently uses string-based block names)

#### Parallel to SystemVerilog

The template approach directly parallels SV module parameters:

| Concept | SystemVerilog | C++ with Config Template |
|---------|--------------|--------------------------|
| Parameter declaration | `parameter int unsigned BITS_PER_PIXEL_COLOR = 8` | `Config::BITS_PER_PIXEL_COLOR` (from config struct) |
| Parameterized type | `typedef logic[BITS_PER_PIXEL_COLOR-1:0] pixel_t` | `using pixel_t = uint64_t` (fixed max-size for parameterizable types) |
| Instance with params | `interpolate #(.BITS_PER_PIXEL_COLOR(8)) u_interp()` | `interpolate<debayer_8bpc_config> u_interp` |
| Non-param types | Regular `typedef` / `struct` in package | Regular `typedef` / `struct` (no template) |

This unified model means the YAML parameterization concept maps to the same structural pattern in both languages.

---

## 5. Address Decoding Impact

Address decoding is one of the most concrete areas affected by parameterization. Both the APB bus router (inter-block routing) and per-block register decoders (intra-block offset dispatch) currently emit resolved numeric literals for offsets, sizes, and masks. For parameterizable IPs, the address map must be **parameter-invariant** — fixed regardless of instance configuration — so that firmware, bus infrastructure, and address documentation remain stable.

### 5.1 How Address Calculation Works Today

Address allocation is computed in Python at generation time by `calcAddresses()` in `processYaml.py`. It processes each block's registers and memories sequentially:

| Element | Size Calculation | Offset Assignment |
|---------|-----------------|-------------------|
| **Registers** | `ceil(width_bits / 8)`, rounded to alignment | Sequential, packed to alignment boundary |
| **Memories** | `roundup_pow2min4(byte_width) × wordLines`, optionally rounded to power-of-2 | Self-aligned (offset = next multiple of size) or value-aligned |

All values are pure Python integers at this stage. They are stored in the SQLite database and then consumed by template generators that format them as hex literals.

**Two-level decode architecture:**

1. **APB bus router** (`apbDecodeModule.py` → SV; `apbBusDecode.h` → SC) — routes transactions from the bus to individual blocks based on address ranges. Uses a descending-priority if/else-if chain (SV) or linear search (SC) with per-block offsets and a decode mask.

2. **Per-block register decoder** (`moduleRegs.py` → SV; `blockRegs.py` + `constructor.py` → SC) — dispatches transactions within a block to individual registers and memories. Uses `case ... inside` with per-register offsets (SV) or `addressMap::find()` with linear search (SC).

### 5.2 Current Numeric Literal Formats

Every stage emits resolved values — no symbolic constant references appear in address decode logic. Offsets, sizes, masks, and decode masks are all hex or decimal literals in both SC (`0x10`, runtime `uint64_t` args) and SV (`32'h0000_0010`, hex literals in `case`/`inside` statements). The Python codegen resolves everything via `hex(offset)`, `inst['bytes']`, and `(1<<bits)-1`.

Notable: the SC side has a split — offsets and sizes are runtime values passed to `addRegister()`/`addMemory()`, but register byte size also appears as a compile-time template parameter `N` in `hwRegister<REG_DATA, N>` (sizing the internal `sc_bv<N*8>`).

### 5.3 Why Parameterization Requires Worst-Case Address Allocation

When a structure's bitwidth or a memory's depth depends on IP parameters, the corresponding register/memory size varies per instance. But the address map cannot vary — firmware, bus decoders, and documentation must agree on a single set of offsets.

Address allocation must use **worst-case sizes** derived from `maxBitwidth` and `maxValue` constraints. A register containing a parameterizable structure uses `maxBitwidth` to determine its byte footprint. A memory with parameterizable depth uses `maxValue` to determine total size. All offsets are then computed from these worst-case sizes.

**Example:** If a register holds a structure whose `_bitWidth` varies from 24 to 48 bits depending on `BITS_PER_PIXEL_COLOR`, the address map allocates `ceil(48/8)` = 6 → rounded to 8 bytes for that register. An instance with `BITS_PER_PIXEL_COLOR=8` uses only 3 bytes of that 8-byte slot, but the offset of the next register is the same for all instances.

**`maxBitwidth` violations** — If an IP is instantiated with parameters that would cause a structure to exceed its declared `maxBitwidth`, this must be a **runtime error** (assertion failure). The generation-time check validates that the `ipInstances` parameters don't exceed bounds, but the IP itself should also self-check as a safety net.

### 5.4 Impact on SystemC Address Decoding

**What already works for parameterization:**
- `addressMap.addRegister(offset, size, ...)` and `addMemory(offset, structByteWidth, wordLines, ...)` take runtime `uint64_t` arguments. If offsets are made symbolic constants (computed from `maxBitwidth`-derived worst-case values), these calls could be text-stable.
- `hwMemory` takes `rows_` as a runtime constructor parameter — already flexible.
- `nextPowerOf2min4()` is a `constexpr` function — it can operate on symbolic inputs.

**What needs to change:**
- **`hwRegister<REG_DATA, N>` template parameter `N`** — currently generated as a resolved integer (e.g., `hwRegister<configReg_t, 4>`). For parameterizable registers, `N` must use the worst-case byte size so the bit-vector is large enough for any valid parameterization. This could be a `constexpr` expression derived from `maxBitwidth`.
- **Offset literals in `addRegister()` / `addMemory()` calls** — currently hex literals like `0x10`. Must become symbolic expressions computed from worst-case sizes so that the generated code is text-stable.
- **Address mask in `registerHandler()` call** — currently `(1<<(N))-1` where `N` is a resolved integer. Must use worst-case address space size.
- **`blockRegs.py` generated code** — same issues as `constructor.py`: hex offset literals and decimal size literals must become symbolic.

### 5.5 Impact on SystemVerilog Address Decoding

**What needs to change:**
- **`apbDecodeModule.py` (APB bus router)** — per-instance offset comparisons (`32'h{offset:_x}`) and decode masks (`32'h{mask:_x}`) are hex literals. Must use worst-case address allocation. Since these are in the top-level decode (outside the IP), they are generated by the consuming project and can use resolved values from `maxBitwidth`-based allocation — the IP itself doesn't generate this module.
- **`moduleRegs.py` (per-block decoder)** — register offsets in `case` statements and memory address ranges in `inside` expressions are hex literals. These are inside the IP's generated code and must become symbolic expressions for text-stability. This is the harder problem.
- **Memory row address widths** — `rowwidth` is computed from `clog2(wordLines)` at generation time. For parameterizable memory depth, must use `clog2(maxWordLines)`.

### 5.6 The Address Decode Text-Stability Challenge

Address decoding presents a harder text-stability problem than type/structure definitions because offsets are **cumulative** — each register's offset depends on the sizes of all preceding registers. Making offsets symbolic requires one of:

1. **Reference existing named constants** — The FW header infrastructure already generates named constants for every register and memory offset (e.g., `REG_DEBAYER_BAYER_PATTERN`, `BASE_ADDR_U_PREPROCESS`). These are generated by `includeAddresses()` and `includeRegAddresses()` in `includes.py` and placed in `*RegAddresses.h` files. Currently only FW code uses them — the SC model and SV RTL decoders inline the same hex values instead of referencing the names. The decode logic should reference these named constants, making it text-stable.

2. **Compute offsets from symbolic size expressions** — each offset is a sum of preceding sizes, expressed symbolically. This is complex and fragile for large register maps.

3. **Accept that address decode constants are generated per-instance** — since `calcAddresses()` uses worst-case sizes, the offsets are parameter-invariant and identical across all instances of the same IP. The generated values are "stable" in the sense that they don't change with parameters, even though they appear as numeric literals.

**Approach 1 is the right answer.** The named constants already exist for FW use — extending the SC model (`blockRegs.py`, `constructor.py`) and SV RTL (`moduleRegs.py`) to reference them instead of inlining hex literals makes the decode logic text-stable with minimal new infrastructure. The named constants themselves are generated from `calcAddresses()` using worst-case sizes (once that change is made), so their values are parameter-invariant. The naming convention (`REG_{BLOCK}_{REGISTER}` for registers, `BASE_ADDR_{INSTANCE}` for instance bases) is already established.

Today's state:

| Layer | Uses Named Constants? | Current Pattern |
|-------|----------------------|-----------------|
| FW code | **Yes** | `BASE_ADDR_U_DEBAYER + REG_DEBAYER_BAYER_PATTERN` |
| SC model (blockRegs/constructor) | No | `regs.addRegister(0x0, 1, "bayer_pattern", ...)` |
| SV RTL (moduleRegs) | No | `32'h0 : begin` in `case` statements |

Target state: all three layers reference the same named constants. For SV, these would be `localparam` constants in a register-address package. For C++, `constexpr` constants in the includes header (or the existing `#define` macros already generated for FW).

### 5.7 Summary of Required Changes

| Component | Current Behavior | Required Change |
|-----------|-----------------|----------------|
| `calcAddresses()` | Uses resolved constant values for sizes | Use `maxBitwidth`/`maxValue` for parameterizable elements |
| `hwRegister<N>` template param | Resolved integer (e.g., `4`) | Worst-case byte size from `maxBitwidth` |
| `blockRegs.py` / `constructor.py` offsets | Inline hex literals (e.g., `0x10`) | Reference existing FW named constants (`REG_BLOCK_REGNAME`) |
| `moduleRegs.py` offsets | Inline hex literals in `case` statements | Reference named `localparam` constants (SV equivalent of FW named constants) |
| `apbDecodeModule.py` offsets | Inline hex literals | Reference named constants (consuming project generates these) |
| `hwMemory` row count | Runtime constructor arg | Runtime arg, but worst-case allocation in address map |
| `addressMap` mask | `(1<<N)-1` from resolved address bits | `(1<<N)-1` from worst-case address bits |

The named-constant infrastructure for address offsets already exists for firmware use (`REG_{BLOCK}_{REGISTER}`, `BASE_ADDR_{INSTANCE}`). Extending the SC model and SV RTL decoders to reference these same named constants — rather than inlining the identical hex values — makes the decode logic text-stable while leveraging existing infrastructure.

---

## 6. C++ Modules as an Enabler

### 6.1 Why Consider C++ Modules

C++20 modules provide compilation-unit isolation and explicit import/export semantics that closely mirror SystemVerilog packages. This parallel could simplify the arch2code story significantly:

| Feature | SV Packages | C++ Modules | C++ Namespaces + Headers |
|---------|------------|-------------|-------------------------|
| Scope isolation | Yes (package scope) | Yes (module scope) | Partial (namespace wraps, but `#include` is textual) |
| Explicit export | Yes (everything in package is visible) | Yes (`export` keyword) | No (everything in header is visible) |
| Import mechanism | `import pkg::*;` or `import pkg::name;` | `import module;` | `#include` + `using namespace` |
| Selective import | `import pkg::pixel_t;` | `import module; using module::pixel_t;` | `using ns::pixel_t;` |
| Compilation isolation | Package compiled once | Module compiled once, imported as binary | Header re-parsed per translation unit |
| Parameter scoping | `localparam` inside package | `constexpr` inside module | `const`/`constexpr` inside namespace |

### 6.2 How C++ Modules Map to arch2code

Currently, each YAML context generates an `*Includes.h` header file. With C++ modules, each context would generate a **module interface unit**:

**Current (header-based):**
```cpp
// isp_typesIncludes.h
#ifndef ISP_TYPESINCLUDES_H_
#define ISP_TYPESINCLUDES_H_
const uint32_t BITS_PER_PIXEL_COLOR = 8;
typedef uint8_t pixel_t;
struct video_frame_t { ... };
#endif
```
```cpp
// debayerIncludes.h
#include "isp_typesIncludes.h"
const uint32_t BPPC_P1 = 9;
// ...
```

**With C++ modules:**

C++20 module names and namespaces are orthogonal — `import isp;` does not create an `isp::` scope automatically. To mirror SV package scoping, the module must explicitly wrap exports in a namespace matching the module name:

```cpp
// isp_types.cppm (module interface unit)
export module isp;
export namespace isp {
    constexpr uint32_t BITS_PER_PIXEL_COLOR = 8;
    using pixel_t = uint8_t;
    struct video_frame_t { ... };
}
```
```cpp
// debayer.cppm (module interface unit)
export module debayer;
import isp;
using namespace isp;  // make isp:: names available unqualified within this module
export namespace debayer {
    constexpr uint32_t BPPC_P1 = BITS_PER_PIXEL_COLOR + 1;
    // ...
}
```

**Consumer code:**
```cpp
// model/interpolate.cpp
import debayer;
using namespace debayer;  // opt-in to unqualified access
// pixel_t, BITS_PER_PIXEL_COLOR etc. available
```

### 6.3 C++ Modules and the Config Template Approach

With the Config template approach for parameterization (Section 4.6), C++ modules serve a different role than originally envisioned. Rather than having per-instance modules with different constant values, modules provide **namespace scoping** (Issue 1) while templates handle **parameterization** (Issue 2):

```cpp
// isp_types.cppm — shared types module (non-parameterized)
export module isp;
export namespace isp {
    struct video_frame_t { ... };  // not parameterized
    enum bayer_pattern_t { RGGB=0, BGGR=1, ... };
}

// debayer_types.cppm — IP types module (parameterized templates)
export module debayer;
import isp;
export namespace debayer {
    template<typename Config>
    using pixel_t = /* constexpr-selected type */;

    template<typename Config>
    struct rgb_pixel_t { ... };

    template<typename Config>
    struct video_rgb_t { ... };
}
```

The Config structs are generated by the consuming project and live outside the IP module:

```cpp
// config/debayer_configs.h (generated by consuming project)
struct debayer_8bpc_config {
    static constexpr uint32_t BITS_PER_PIXEL_COLOR = 8;
    static constexpr uint32_t PIXELS_PER_CLOCK = 4;
};
struct debayer_12bpc_config { ... };
```

Consumer code imports the module and instantiates templates with specific configs:

```cpp
import debayer;
#include "debayer_configs.h"
debayer::video_rgb_t<debayer_8bpc_config> pixel_data;  // 24-bit
debayer::video_rgb_t<debayer_12bpc_config> pixel_data;  // 36-bit
```

This cleanly separates concerns: modules handle scoping/namespace, templates handle parameterization.

### 6.4 C++ Modules and Enum Scoping

With C++ modules, enum scoping becomes natural when the module wraps exports in a namespace (as described in Section 6.2):

```cpp
// isp.cppm
export module isp;
export namespace isp {
    enum bayer_pattern_t { RGGB=0, BGGR=1, GRBG=2, GBRG=3 };
}
```

The enumerators `RGGB`, `BGGR`, etc. are scoped to `isp::`. A consumer that does `import isp;` can access them as `isp::RGGB`, or opt in to unqualified access via `using namespace isp;`. If two modules export the same enumerator name, they are disambiguated by namespace (`isp::RGGB` vs `other::RGGB`). This mirrors how SV package-scoped enums work.

Contrast with the header approach: `#include "isp_typesIncludes.h"` dumps `RGGB` into whatever scope contains the include. With the module + namespace convention, names are always namespace-scoped, and `using namespace` is an explicit opt-in.

### 6.5 Unified Mental Model: SV Packages ≈ C++ Modules

Adopting C++ modules creates a unified conceptual model across both languages:

| Concept | SystemVerilog | C++ with Modules + Templates |
|---------|--------------|-----------------|
| Type/constant container | `package isp_package;` | `export module isp;` with `export namespace isp { ... }` |
| Import all names | `import isp_package::*;` | `import isp; using namespace isp;` |
| Selective import | `import isp_package::pixel_t;` | `import isp; using isp::pixel_t;` |
| Parameterized types | `parameter` on module, types use param refs | `template<typename Config>`, types use `Config::` refs |
| IP instance with params | `interpolate #(.BPC(8)) u_interp()` | `interpolate<debayer_8bpc_config> u_interp` |
| Shared types | `import shared_package::*;` | `import shared; using namespace shared;` |

The convention that each module wraps its exports in a namespace matching the module name is what makes this parallel work. With this convention, the same YAML namespace concept maps identically to both languages.

### 6.6 Practical Considerations for C++ Module Adoption

| Consideration | Assessment |
|--------------|------------|
| **Compiler support** | GCC 14+, Clang 17+, MSVC 19.38+ have mature module support. SystemC projects typically use GCC/Clang on Linux. |
| **SystemC compatibility** | SystemC headers are not modularized. IP modules would `import` their own types but still `#include "systemc.h"` in the global module fragment. This is supported via `module; #include "systemc.h"; export module isp;` pattern. |
| **Build system** | Module dependency scanning is needed. CMake 3.28+ supports C++ modules natively. Make-based builds would need dependency generation (e.g., `g++ -fmodules-ts -fdep-file`). |
| **Verilator** | Verilator compiles SV to C++. Its generated code uses headers, not modules. Co-simulation wrappers may need to bridge module and header worlds. |
| **Migration effort** | Significant — all `*Includes.h` files become `.cppm` module interface units. All `#include "...Includes.h"` become `import ...;`. All hand-written code needs updating. |
| **Incremental adoption** | Possible — modules can coexist with headers. New IPs use modules; legacy code uses header wrappers that re-export module contents. |

### 6.7 Assessment

C++ modules are a strong candidate for the namespace/scoping mechanism because they:
- Parallel SV packages when combined with the convention of wrapping exports in a matching namespace
- Solve enum scoping naturally via namespace wrapping
- Provide true compilation isolation (not textual inclusion)
- Complement the Config template approach — modules handle scoping, templates handle parameterization

Note that C++20 module names do not create namespaces automatically — the generated module interface units must use `export namespace <name> { ... }` to get SV-like scoping. This is a code-generation convention, not a language guarantee.

However, the migration cost is significant and SystemC/Verilator interop needs validation. **Recommendation:** Prototype C++ module generation for a single YAML context (e.g., `isp_types`) to validate feasibility with the SystemC/Verilator toolchain. If viable, target modules as the primary mechanism; if not, fall back to namespaces + headers with a path to modules later.

---

## 7. How Namespaces and Parameters Interact

The two issues serve distinct but complementary roles:

1. **Namespaces** (Issue 1) prevent name collisions — different IPs with types that happen to share names coexist via `isp::pixel_t` vs `encoder::status_t`. Namespaces also scope shared types that multiple IPs import (e.g., `isp::video_frame_t`).
2. **Config templates** (Issue 2) enable multi-instance parameterization — `video_rgb_t<debayer_8bpc_config>` and `video_rgb_t<debayer_12bpc_config>` are distinct types with different bitwidths, coexisting in the same program through the C++ type system.

For Scenario B (same IP, multiple instances), templates are sufficient on their own — they make each parameterized type distinct without needing separate namespaces. Namespaces are still needed for Scenario A (shared types across IPs) and Scenario C (unrelated name collisions).

### Interface Constraint

**Cross-config interface connections between differently-parameterized instances are prohibited.** If two blocks use different Config types, they cannot directly communicate via interfaces typed with parameterized types because the types are structurally different (e.g., `video_rgb_t<debayer_8bpc_config>` has different bitwidth than `video_rgb_t<debayer_12bpc_config>`).

Blocks that communicate must either:
- Share the same Config type (same parameter configuration)
- Communicate through interfaces typed with non-parameterized types (types without `<Config>`)
- Use an explicit adapter block that bridges between configurations

This constraint should be enforced at the YAML level during connection validation.

---

## 8. Impact Analysis

### 8.1 Schema Changes

| Change | File | Description |
|--------|------|-------------|
| Add `namespace:` field | `schema.yaml` | Optional field on top-level YAML, declares the namespace for all definitions in that file |
| Add `ipParameters` section | `schema.yaml` | New top-level section with `constants` and `types` sub-sections, plus `maxBitwidth`/`maxValue` |
| Add `isParameterizable` | `schema.yaml` | Optional boolean on `types` and `constants` nodes |
| Add `maxBitwidth`/`maxValue` | `schema.yaml` | Optional fields on `types` and `constants` |
| Add `ipInstances` section | `schema.yaml` | For consuming projects: IP reference, Config parameters per instance |

### 8.2 Processing Changes (`processYaml.py`)

| Change | Description |
|--------|-------------|
| Namespace propagation | Track namespace per context, include in all DB records |
| `ipParameters` processing | Parse as embedded YAML, stamp `isParameterizable`, validate `maxBitwidth` |
| Transitive propagation | Walk constants → types → structures marking parameterizable entries |
| Connection validation | Enforce that cross-config connections use compatible (non-parameterized) types |
| Per-instance generation | Generate Config structs (C++) and packages (SV) per `ipInstances` entry |

### 8.3 Template Changes

| Template | C++ Changes | SV Changes |
|----------|------------|------------|
| **includes** | Wrap in `namespace`/`module` (scoping); parameterizable constants become `Config::` refs; parameterizable types become `template<typename Config>` aliases | Symbolic `localparam` values or parameters |
| **structures** | Parameterizable structs become `template<typename Config>`; symbolic `_bitWidth` via `Config::`; symbolic pack/unpack; constexpr `_packedSt` selection; header-only implementations | Symbolic type widths (already mostly done) |
| **baseClassDecl** | Parameterizable base classes become `template<typename Config>`; port types use `<Config>` | N/A (ports reference package types) |
| **classDecl** | Block classes become `template<typename Config>` inheriting from `baseClass<Config>` | N/A |
| **package** | N/A | Per-instance package generation; symbolic constants |
| **fileGen** | Generate Config struct headers per instance; generate `.cppm` module files (if C++ modules adopted) or namespaced headers | Generate per-instance packages |

### 8.4 Build System Changes

| Change | Description |
|--------|-------------|
| Template instantiation | Templates are instantiated at point of use in the consuming project; no per-instance compilation of IP source files |
| Header-only parameterized code | Parameterizable struct implementations move from `.cpp` to headers (required for templates) |
| Module dependency scanning | If C++ modules: build system must handle module deps |
| Config struct generation | Generate per-instance Config struct headers from `ipInstances` YAML |

### 8.5 Hand-Written Code Impact

This is a **breaking change**. All existing hand-written code will need:
- `<Config>` template parameter on parameterizable type references (e.g., `rgb_pixel_t<Config>`)
- `Config::` prefix on parameterizable constant references (e.g., `Config::BITS_PER_PIXEL_COLOR`)
- Block classes become `template<typename Config>` with updated method signatures
- `using namespace <ns>;` or qualified names for namespace scoping (Issue 1)
- Or `import <module>;` statements (if C++ modules adopted)
- SV: Minimal impact (already package-scoped, import patterns stay similar)

A migration tool should be provided to automate the bulk of these changes.

---

## 9. IP Packaging (Light)

For IPs to be distributable and reusable, they need a boundary definition:

```yaml
# IP manifest (in IP's project.yaml)
ip:
  name: debayer
  namespace: debayer
  version: 1.0.0
  ipParameters:
    BITS_PER_PIXEL_COLOR: {maxBitwidth: 16, default: 8, desc: "..."}
    PIXELS_PER_CLOCK: {maxValue: 8, default: 4, desc: "..."}
  exports:
    interfaces: [video_raw_stream, video_rgb_stream]
    types: [video_bayer_t, video_rgb_t]
  requires:
    - {namespace: isp, from: isp_types.yaml}
```

This defines:
- What parameters are configurable (with bounds and defaults)
- What interfaces and types are exposed to consumers
- What shared dependencies are required
- The namespace boundary

Distribution could be a directory (git submodule, tarball, package registry) containing the IP's YAML, generated code, and optionally pre-compiled modules.

---

## 10. Recommended Phased Approach

| Phase | Scope | Enables | Breaking? |
|-------|-------|---------|-----------|
| **Phase 0: Prototype Validation** | Prototype Config template generation for one block (`interpolate`) with two parameter configs. Validate SystemC compatibility (`SC_MODULE`/`SC_THREAD` with templates). Optionally prototype C++ module generation for `isp_types` to validate module feasibility. | Decision on C++ module adoption; SystemC template compatibility confirmed | No |
| **Phase 1: Namespaces** | Add `namespace:` to YAML schema. Generate C++ namespace wrappers (or module interface units) in Includes files. Generate SV packages with namespace-aware naming. Provide migration tooling. | Scenario A (different IPs coexisting), Scenario C (collision avoidance) | **Yes** |
| **Phase 2: Config Templates + Symbolic Constants** | Implement `ipParameters`, `isParameterizable` propagation. Generate `template<typename Config>` parameterizable types/structs/blocks. Symbolic `Config::` expressions for `_bitWidth`, pack/unpack, type selection. Move parameterizable implementations to headers. Runtime assertions for `maxBitwidth`/`maxValue`. | Text-stable parameterizable IP code | **Yes** |
| **Phase 3: Instance Parameterization** | YAML `ipInstances` override mechanism. Per-instance Config struct generation (C++) and package generation (SV). `instanceFactory` support for template-parameterized blocks. | Scenario B (same IP, multiple instances, different params) | No (additive) |
| **Phase 4: IP Packaging** | IP manifest, export/import controls, version tracking, sub-project support, distribution mechanism. | Distributable, reusable IPs | No (additive) |

---

## 11. Open Questions

1. **Shared type namespaces and parameterization:** When `isp_types.yaml` is shared between two IPs, its types live in the `isp` namespace. If a type in `isp_types` depends on a parameterizable constant, does it become `template<typename Config>`? If so, both IPs must use the same Config type for shared types — or shared types must be non-parameterizable only. **This needs further refinement** — the boundary between shared (non-parameterized) and IP-specific (parameterized) types must be precisely defined.

2. **SV parameterization strategy:** Parameterized packages (SV-2012) vs. separate packages per instance vs. module-level parameters. **Left open** for prototyping and EDA tool validation.

3. **`maxBitwidth` compound cases:** When both `arraySize` and element `bitwidth` are parameterizable, the compound expression (`Config::ELEMENT_WIDTH * Config::ARRAY_SIZE`) must be fully symbolic. Is this in scope for Phase 2 or deferred?

4. **SystemC template compatibility:** `SC_MODULE`, `SC_THREAD`, and `SC_METHOD` macros with `template<typename Config>` classes need prototype validation. Key concerns: function pointer registration, `sc_trace` with template types, `instanceFactory` registration with templated blocks.

5. **C++ module + SystemC interop:** SystemC headers use macros that may interact poorly with module boundaries. The feasibility prototype in Phase 0 must validate this.

6. **`instanceFactory` with templates:** The current factory uses string-based block name lookup to create instances. Templated blocks need a mechanism for the factory to instantiate with the correct Config type. This likely requires the consuming project to register template instantiations explicitly.

7. **Migration tooling scope:** What level of automation is feasible for migrating existing projects? The migration from non-template to template structs/blocks is more invasive than adding namespace qualifiers — every use of a parameterizable type must gain `<Config>`.

---

## Appendix A: Reference Files

| File | Relevance |
|------|-----------|
| `builder/base/config/schema.yaml` | Current YAML schema — all changes start here |
| `builder/base/pysrc/processYaml.py` | Core YAML processing engine — `calcAddresses()`, namespace propagation, ipParameters processing |
| `builder/base/pysrc/arch2codeHelper.py` | `roundup_pow2min4()`, `clog2()`, address size utility functions |
| `builder/base/templates/systemc/includes.py` | C++ constant/type/enum generation — namespace wrapping |
| `builder/base/templates/systemc/structures.py` | C++ struct generation — symbolic expressions, pack/unpack |
| `builder/base/templates/systemc/blockRegs.py` | SC register handler generation — offset/size literals, `hwRegister<N>` template param |
| `builder/base/templates/systemc/constructor.py` | SC constructor — `addRegister()`/`addMemory()` calls with offset/size args |
| `builder/base/templates/systemVerilog/package.py` | SV package generation — per-instance packages |
| `builder/base/templates/systemVerilog/constantsTypesEnumsStructures.py` | SV type generation — symbolic widths |
| `builder/base/templates/systemVerilog/apbDecodeModule.py` | SV APB bus router — inter-block address decode with hex offset literals |
| `builder/base/templates/systemVerilog/moduleRegs.py` | SV per-block register decoder — intra-block offset/mask hex literals |
| `builder/base/templates/fileGen/fileGen.py` | File scaffolding — module/header generation |
| `builder/base/common/systemc/addressMap.h` | SC address map — `addRegister()`/`addMemory()`, `registerHandler` dispatch |
| `builder/base/common/systemc/hwRegister.h` | SC register implementation — template param `N` sizes `sc_bv<N*8>` |
| `builder/base/common/systemc/hwMemory.h` | SC memory implementation — runtime `rows_`, `constexpr` row sizing |
| `builder/base/common/systemc/apbBusDecode.h` | SC APB bus decode template — runtime address matching |
| `builder/base/common/systemc/bitTwiddling.h` | `clog2()` and `nextPowerOf2min4()` constexpr functions |
| `builder/base/pysrc/systemcGen.py` | Existing `--namespace` arg — starting point for namespace infrastructure |
| `builder/base/plan-parameterizableTypesAndStructs.prompt.md` | Existing detailed plan for symbolic expression generation |
| `arch/yaml/config/addressControl.yaml` | Address group config — alignment, ordering, `sizeRoundUpPowerOf2` |
| `model/isp_typesIncludes.h` | Example generated C++ output — shows current patterns |
| `rtl/isp_types_package.sv` | Example generated SV output — shows current patterns |
