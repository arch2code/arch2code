# Plan: P0 RTL Proof-of-Concept — SV Parameterization Patterns

**Status:** historical. This is a completed prototype record; it records
prototype validation only and is not an active implementation plan.

## Objective

Validate that the target SystemVerilog parameterization pattern — **per-variant package generation with text-stable module source** — works with the project's Verilator-based toolchain. This mirrors the completed SystemC P0 (`plan-p0-proof-of-concept.md`) but is substantially simpler because SV types are already largely text-stable.

This is a **throwaway prototype**. No generator code is modified. All files are hand-written under `proto_rtl/` and compiled with a standalone Makefile. The prototype succeeds or fails based on whether the target patterns compile, elaborate, simulate, and co-simulate correctly under Verilator.

## Environment

| Component | Version | Notes |
|-----------|---------|-------|
| **Verilator** | Project default | Primary target — Verilator-based simulation and tandem co-simulation |
| **Clang** | **20.1.8** | For SystemC co-simulation testbench compilation |
| C++ standard | C++23 (`-std=c++23`) | For SystemC side of co-simulation |
| SystemC | 2.3.4 | For co-simulation testbench |
| Build | GNU Make | Standalone Makefile — no arch2code dependency |

## Key Insight: SV Parameterization Has Two Levels

The SystemC P0 validated Config templates because C++ needs distinct types to coexist in the same binary — `rgb_pixel_t<config_8bpc>` and `rgb_pixel_t<config_12bpc>` are separate types in the same compilation unit.

SV has two distinct parameterization levels, depending on whether the IP is instantiated once or multiple times with different parameters in the same build:

### Level 1: Single-Instance — Per-Variant Package Generation

When each build contains only one instance of the IP (the common case for leaf-level tandem verification), the parameterization is straightforward:

| Aspect | C++ | SV (single-instance) |
|--------|-----|-----|
| Config delivery | Config struct (`static constexpr` members) | Package `localparam` values (regenerated per variant) |
| Type text-stability | `template<typename Config> struct rgb_pixel_t` with `Config::` refs | `typedef struct packed { pixel_t b, g, r; }` — **already text-stable** |
| What changes per variant | Nothing — Config struct is external | Package `localparam` values only |
| Module source text-stable? | Yes (templates) | **Yes (already — types reference symbolic constants)** |

The SV type system is already substantially text-stable. The existing generated code (`isp_types_package.sv`) defines types symbolically:
```systemverilog
typedef logic[BITS_PER_PIXEL_COLOR-1:0] pixel_t;                    // symbolic
typedef struct packed { pixel_t [PIXELS_PER_CLOCK-1:0] pixels; }    // symbolic
```

The **only** non-text-stable elements are the `localparam` value declarations themselves:
```systemverilog
localparam int unsigned BITS_PER_PIXEL_COLOR = 32'h0000_0008;  // ← this literal changes per variant
```

Per-variant package generation solves this: regenerate the package with different `localparam` values, re-verilate with the same module source. No per-instance packages (different package names), no parameterized packages (SV-2012), no name mangling.

### Level 2: Multi-Instance — Module Parameters with Local Types

When a design instantiates the same IP twice with different parameters (e.g., a chip with high-res 12bpc and low-res 8bpc cameras), the package is compiled once and can only define one set of types. The parameterized types must move from the package to the modules:

| Aspect | C++ | SV (multi-instance) |
|--------|-----|-----|
| Multi-instance mechanism | `template<typename Config>` — two configs in same binary | Module parameters (default from package) + local type definitions |
| IP module types | `Config::pixel_t` (from template parameter) | Module-local `pixel_t` (from module parameter) |
| Container types | Templated — `interpolate<config_8bpc>`, `interpolate<config_12bpc>` | Container-local types per instance — `hires_pixel_t`, `lores_pixel_t` |
| Type boundary | C++ templates — same type from same Config | SV structural typing — `struct packed` with identical layout |

The IP module pattern becomes:
```systemverilog
module interpolate_mparam
    import isp_types_package::*;   // for default parameter values
#(
    parameter int unsigned BITS_PER_PIXEL_COLOR = isp_types_package::BITS_PER_PIXEL_COLOR
) (...);
    // Parameterized types defined locally — NOT from package
    typedef logic[BITS_PER_PIXEL_COLOR-1:0] pixel_t;
    // ...
```

This works in **both** contexts:
- **Single-instance build:** Parameters default to package values. Module-local types match what the package would have defined.
- **Multi-instance build:** Container overrides parameters per instance. Each instance gets different-width local types.

### What This Means for the Prototype

The SV P0 has more to prove than initially expected. Beyond text-stability (which is already solved), the remaining risks are:

1. Does the per-variant build flow actually work end-to-end with Verilator?
2. Does the IP module pattern work — module parameters defaulting from a package, with all parameterized types defined locally?
3. Can register decode logic use named constants instead of hex literals?
4. What happens when derived constants and types change width between variants — does everything elaborate cleanly?
5. When two differently-parameterized instances coexist in one build, does structural type compatibility work at every scope boundary (testbench ↔ container ↔ IP module)?

## What SV Already Has (No Validation Needed)

| Element | Current State | Example |
|---------|---------------|---------|
| Symbolic type widths | Working | `typedef logic[BITS_PER_PIXEL_COLOR-1:0] pixel_t;` |
| Symbolic array dimensions | Working | `pixel_t [PIXELS_PER_CLOCK-1:0] pixels;` |
| Symbolic struct composition | Working | `typedef struct packed { pixel_t b, g, r; } rgb_pixel_t;` |
| Parameterized interfaces | Working | `rdy_vld_if #(.data_t(bayer_preprocess_stream_t))` |
| Package imports | Working | `import isp_types_package::*;` |
| Symbolic `$clog2()` | Working | `typedef logic[$clog2(BSIZE+1)-1:0] bSizeCountT;` |
| Derived constants | Working | `localparam int unsigned BPPC_P1 = BITS_PER_PIXEL_COLOR + 1;` (expression is symbolic, value is resolved) |

## What We're Validating

Six specific risks. These are more targeted than the C++ P0 because SV's text-stability is already stronger.

| ID | Risk | Pass Criteria |
|----|------|---------------|
| **R1** | Per-variant package generation — same module source, different package constants | Same `interpolate.sv` module source elaborates and simulates correctly against two different package variants (8bpc and 12bpc). Types, widths, and array dimensions resolve correctly in each variant. Each variant is a separate Verilator build. |
| **R2** | Derived constants and type chain correctness across variants | Constants derived from parameterizable constants (e.g., `BPPC_P1 = BITS_PER_PIXEL_COLOR + 1`, accumulator types, grid types) resolve correctly when base constants change. The full type dependency chain — constants → types → structs → interface data types — elaborates without width mismatches or truncation. |
| **R3** | Module-level parameters with local types — the IP module pattern | A module declares `parameter int unsigned BITS_PER_PIXEL_COLOR = isp_types_package::BITS_PER_PIXEL_COLOR` (defaulting from package), defines **all parameterized types locally** from its parameters, and uses them through `rdy_vld_if`. This is the required IP module pattern when the same IP may be instantiated with different parameters in the same build. Validates that Verilator can elaborate module-local types in interface bindings and that two differently-parameterized instances coexist in one build. |
| **R4** | Named constant references in register decode logic | Register decode `case` statements use `localparam REG_BAYER_PATTERN = ...` named constants instead of hex literals (`32'h0`). Decode logic is functionally equivalent. Constants could come from the package or a dedicated reg-address package. |
| **R5** | Per-variant tandem build flow | The per-variant Verilator build integrates with the existing tandem verification flow. The RTL variant is built against its package, the SystemC model is compiled with the matching Config struct, and tandem co-simulation runs correctly. Both builds use the same text-stable module/model source. |
| **R6** | Dual-instance integration — two IP instances with different parameters in one build | A system container (e.g., a chip with high-res and low-res cameras) instantiates the same IP twice with different parameters (12bpc/8PPC and 8bpc/4PPC). The container defines **local types per instance** to create internal interfaces. Each IP module defines its own types from module parameters. Data flows correctly across the type boundary: container-local types ↔ module-local types. This validates structural type compatibility for `struct packed` across scopes in Verilator. |

### What We Are NOT Validating

| Approach | Why Not |
|----------|---------|
| **Per-instance packages** (different package names like `isp_types_8bpc_pkg`) | Unnecessary complexity. Per-variant builds with the same package name achieve the same result without name mangling or import selection mechanisms. For multi-instance builds, module parameters handle differentiation. |
| **Parameterized packages** (SV-2012 `package #(parameter)`) | Poor EDA tool support. Difficult to use in a text-stable way. Not worth prototyping. |
| **Generate blocks for type selection** | Overly complex for the use case. |

## Per-Variant Build Model

The deployment model for SV parameterization:

```
variant_8bpc/                        variant_12bpc/
├── isp_types_package.sv  ← generated  ├── isp_types_package.sv  ← generated
│   BITS_PER_PIXEL_COLOR = 8           │   BITS_PER_PIXEL_COLOR = 12
│   PIXELS_PER_CLOCK = 4              │   PIXELS_PER_CLOCK = 8
│   MAX_PIXEL_VALUE = 255             │   MAX_PIXEL_VALUE = 4095
│                                      │
├── interpolate.sv ─── symlink ──────> ├── interpolate.sv        ← SAME file
├── preprocess.sv  ─── symlink ──────> ├── preprocess.sv         ← SAME file
├── debayer.sv     ─── symlink ──────> ├── debayer.sv            ← SAME file
│                                      │
└── Verilator build (independent)      └── Verilator build (independent)
```

The prototype validates this model directly: two build directories, same module source, different package files.

## Prototype Structure

```
proto_rtl/
├── Makefile                    # Standalone build, per-variant targets
│
├── packages/
│   ├── shared_types_pkg.sv     # Non-parameterizable types (video_frame_t, etc.)
│   ├── isp_types_pkg_8bpc.sv   # Variant: BITS_PER_PIXEL_COLOR=8, PPC=4
│   └── isp_types_pkg_12bpc.sv  # Variant: BITS_PER_PIXEL_COLOR=12, PPC=8
│   # NOTE: Both files define `package isp_types_package` (same name, different values).
│   # Each variant build uses one or the other.
│
├── interfaces/
│   └── rdy_vld_if.sv           # Minimal rdy_vld interface stub
│
├── rtl/
│   ├── interpolate.sv          # R1/R2: Text-stable module using package types
│   ├── preprocess.sv           # R1/R2: Text-stable passthrough module
│   ├── debayer.sv              # R1/R2: Text-stable hierarchical container
│   ├── interpolate_mparam.sv   # R3/R6: IP module — params default from package, local types
│   ├── preprocess_mparam.sv    # R6: Parameterized passthrough
│   ├── decode_named.sv         # R4: Register decode with named constants
│   └── camera_subsystem.sv     # R6: System container — two IP instances, different params
│
├── test/
│   ├── tb_variant.sv           # R1/R2: Per-variant testbench (same for both variants)
│   ├── tb_mparam.sv            # R3: Module-parameter testbench (two instances, one build)
│   ├── tb_decode.sv            # R4: Named constant decode test
│   └── tb_dual_instance.sv     # R6: Dual-instance integration test
│
└── cosim/                      # R5: Stretch goal — tandem co-simulation per variant
    ├── tb_cosim.cpp            # SystemC testbench for tandem
    └── Makefile.cosim
```

## Detailed File Specifications

### `packages/shared_types_pkg.sv` — Non-Parameterizable Types

Types that do not depend on IP parameters. These remain in a fixed package, shared unchanged across all variants.

```systemverilog
package shared_types_pkg;
    typedef logic[1-1:0] eol_t;
    typedef logic[1-1:0] sof_t;
    typedef logic[1-1:0] eof_t;

    typedef struct packed {
        eol_t eol;
        sof_t sof;
        eof_t eof;
    } video_frame_t;
endpackage
```

### `packages/isp_types_pkg_8bpc.sv` — Variant Package (8bpc)

Generated per variant. The package **name** is always `isp_types_package` — only the `localparam` values change. The type definitions, struct layouts, and symbolic expressions are identical across variants (text-stable).

```systemverilog
// Generated for variant: 8bpc
package isp_types_package;
    import shared_types_pkg::*;

    // ---- IP Parameters (variant-specific values) ----
    localparam int unsigned BITS_PER_PIXEL_COLOR = 8;
    localparam int unsigned MAX_PIXEL_VALUE = 255;
    localparam int unsigned PIXELS_PER_CLOCK = 4;

    // ---- Derived constants (text-stable expressions, variant-specific values) ----
    localparam int unsigned BPPC_P1 = BITS_PER_PIXEL_COLOR + 1;
    localparam int unsigned BPPC_P2 = BITS_PER_PIXEL_COLOR + 2;

    // ---- Types (text-stable — reference constants symbolically) ----
    typedef logic[BITS_PER_PIXEL_COLOR-1:0] pixel_t;
    typedef logic[BPPC_P1-1:0] acc2_t;
    typedef logic[BPPC_P2-1:0] acc4_t;

    // ---- Structures (text-stable) ----
    typedef struct packed {
        pixel_t b;
        pixel_t g;
        pixel_t r;
    } rgb_pixel_t;

    typedef struct packed {
        pixel_t [PIXELS_PER_CLOCK-1:0] pixels;
    } bayer_pixels_per_clock_t;

    typedef struct packed {
        rgb_pixel_t [PIXELS_PER_CLOCK-1:0] pixels;
    } rgb_pixels_per_clock_t;

    typedef struct packed {
        bayer_pixels_per_clock_t data;
        video_frame_t frame;
    } video_bayer_t;

    typedef struct packed {
        rgb_pixels_per_clock_t data;
        video_frame_t frame;
    } video_rgb_t;

endpackage
```

### `packages/isp_types_pkg_12bpc.sv` — Variant Package (12bpc)

Identical structure, different values. The text of this file is identical to the 8bpc version **except** for the three IP parameter `localparam` lines.

```systemverilog
// Generated for variant: 12bpc
package isp_types_package;
    import shared_types_pkg::*;

    // ---- IP Parameters (variant-specific values) ----
    localparam int unsigned BITS_PER_PIXEL_COLOR = 12;
    localparam int unsigned MAX_PIXEL_VALUE = 4095;
    localparam int unsigned PIXELS_PER_CLOCK = 8;

    // ---- Derived constants (text-stable expressions, variant-specific values) ----
    localparam int unsigned BPPC_P1 = BITS_PER_PIXEL_COLOR + 1;
    localparam int unsigned BPPC_P2 = BITS_PER_PIXEL_COLOR + 2;

    // ---- Types (text-stable) ----
    typedef logic[BITS_PER_PIXEL_COLOR-1:0] pixel_t;
    typedef logic[BPPC_P1-1:0] acc2_t;
    typedef logic[BPPC_P2-1:0] acc4_t;

    // ---- Structures (text-stable) ----
    typedef struct packed {
        pixel_t b;
        pixel_t g;
        pixel_t r;
    } rgb_pixel_t;

    typedef struct packed {
        pixel_t [PIXELS_PER_CLOCK-1:0] pixels;
    } bayer_pixels_per_clock_t;

    typedef struct packed {
        rgb_pixel_t [PIXELS_PER_CLOCK-1:0] pixels;
    } rgb_pixels_per_clock_t;

    typedef struct packed {
        bayer_pixels_per_clock_t data;
        video_frame_t frame;
    } video_bayer_t;

    typedef struct packed {
        rgb_pixels_per_clock_t data;
        video_frame_t frame;
    } video_rgb_t;

endpackage
```

**Key observation:** Diff between 8bpc and 12bpc packages: only the 3 `localparam` value lines differ. Everything else is byte-for-byte identical. This demonstrates that the package itself is text-stable except for the IP parameter value declarations. A generator could emit the package once as a template and substitute only the parameter values per variant.

### `interfaces/rdy_vld_if.sv` — Parameterized Interface

Minimal stub matching the project's interface pattern:

```systemverilog
interface rdy_vld_if #(type data_t = logic);
    data_t data;
    logic  vld;
    logic  rdy;

    modport src (output data, output vld, input  rdy);
    modport dst (input  data, input  vld, output rdy);
endinterface
```

### `rtl/interpolate.sv` — Text-Stable Module (R1/R2)

The core validation module. This file is **identical** across all variants — it imports `isp_types_package` and uses symbolic type references. Mirrors a simplified version of `rtl/interpolate.sv` from the real design.

```systemverilog
module interpolate
    import shared_types_pkg::*;
    import isp_types_package::*;
(
    rdy_vld_if.dst bayer_in,
    rdy_vld_if.src rgb_out,
    input clk, rst_n
);

    // Simple passthrough: replicate bayer pixel to all RGB channels
    // Validates that package types elaborate correctly per variant
    assign bayer_in.rdy = rgb_out.rdy;

    video_bayer_t bayer_data;
    assign bayer_data = bayer_in.data;

    video_rgb_t rgb_data;
    always_comb begin
        rgb_data.frame = bayer_data.frame;
        for (int i = 0; i < PIXELS_PER_CLOCK; i++) begin
            rgb_data.data.pixels[i].r = bayer_data.data.pixels[i];
            rgb_data.data.pixels[i].g = bayer_data.data.pixels[i];
            rgb_data.data.pixels[i].b = bayer_data.data.pixels[i];
        end
    end

    assign rgb_out.data = rgb_data;
    assign rgb_out.vld = bayer_in.vld;

    // Use derived types to verify the full constant chain
    function automatic pixel_t round_div2(input acc2_t sum);
        return sum[BPPC_P1-1:1];
    endfunction

endmodule
```

### `rtl/preprocess.sv` — Text-Stable Passthrough (R1/R2)

```systemverilog
module preprocess
    import shared_types_pkg::*;
    import isp_types_package::*;
(
    rdy_vld_if.dst bayer_in,
    rdy_vld_if.src bayer_out,
    input clk, rst_n
);

    assign bayer_in.rdy = bayer_out.rdy;
    assign bayer_out.data = bayer_in.data;
    assign bayer_out.vld = bayer_in.vld;

endmodule
```

### `rtl/debayer.sv` — Text-Stable Hierarchical Container (R1/R2)

```systemverilog
module debayer
    import shared_types_pkg::*;
    import isp_types_package::*;
(
    rdy_vld_if.dst video_raw_stream,
    rdy_vld_if.src video_rgb_stream,
    input clk, rst_n
);

    rdy_vld_if #(.data_t(video_bayer_t)) preprocess_to_interp ();

    preprocess u_preprocess (
        .bayer_in(video_raw_stream),
        .bayer_out(preprocess_to_interp),
        .clk(clk),
        .rst_n(rst_n)
    );

    interpolate u_interpolate (
        .bayer_in(preprocess_to_interp),
        .rgb_out(video_rgb_stream),
        .clk(clk),
        .rst_n(rst_n)
    );

endmodule
```

### `rtl/interpolate_mparam.sv` — IP Module with Parameterized Types (R3/R6)

The IP module pattern for parameterizable designs. Parameters default from the package (so the module works unchanged in per-variant builds) but can be overridden at instantiation (required for multi-instance builds). All parameterized types are defined locally from module parameters — not imported from the package.

```systemverilog
module interpolate_mparam
    import shared_types_pkg::*;
    import isp_types_package::*;
#(
    parameter int unsigned BITS_PER_PIXEL_COLOR = isp_types_package::BITS_PER_PIXEL_COLOR,
    parameter int unsigned MAX_PIXEL_VALUE = isp_types_package::MAX_PIXEL_VALUE,
    parameter int unsigned PIXELS_PER_CLOCK = isp_types_package::PIXELS_PER_CLOCK
) (
    rdy_vld_if.dst bayer_in,
    rdy_vld_if.src rgb_out,
    input clk, rst_n
);
    // Parameterized types — defined locally from module parameters
    typedef logic[BITS_PER_PIXEL_COLOR-1:0] pixel_t;
    localparam int unsigned BPPC_P1 = BITS_PER_PIXEL_COLOR + 1;
    typedef logic[BPPC_P1-1:0] acc2_t;

    typedef struct packed { pixel_t b, g, r; } rgb_pixel_t;
    typedef struct packed { pixel_t [PIXELS_PER_CLOCK-1:0] pixels; } bayer_pixels_per_clock_t;
    typedef struct packed { rgb_pixel_t [PIXELS_PER_CLOCK-1:0] pixels; } rgb_pixels_per_clock_t;
    typedef struct packed { bayer_pixels_per_clock_t data; video_frame_t frame; } video_bayer_t;
    typedef struct packed { rgb_pixels_per_clock_t data; video_frame_t frame; } video_rgb_t;

    // Passthrough logic using module-local types
    assign bayer_in.rdy = rgb_out.rdy;

    video_bayer_t bayer_data;
    assign bayer_data = bayer_in.data;

    video_rgb_t rgb_data;
    always_comb begin
        rgb_data.frame = bayer_data.frame;
        for (int i = 0; i < PIXELS_PER_CLOCK; i++) begin
            rgb_data.data.pixels[i].r = bayer_data.data.pixels[i];
            rgb_data.data.pixels[i].g = bayer_data.data.pixels[i];
            rgb_data.data.pixels[i].b = bayer_data.data.pixels[i];
        end
    end

    assign rgb_out.data = rgb_data;
    assign rgb_out.vld = bayer_in.vld;

endmodule
```

**Key design decisions:**
- `import isp_types_package::*;` — provides default parameter values and non-parameterized types
- Parameters default to `isp_types_package::BITS_PER_PIXEL_COLOR` etc. — in per-variant builds, no override needed
- All parameterized types defined locally from parameters — required so two instances with different parameters define different-width types
- Non-parameterized types (`video_frame_t`) still come from the shared package

### `rtl/decode_named.sv` — Named Constant Decode (R4)

```systemverilog
module decode_named (
    input logic clk, rst_n,
    input logic [11:0] addr,
    input logic [31:0] wdata,
    input logic wr_en,
    output logic [31:0] rdata
);
    // Named constants for register offsets
    // These would come from a generated reg-address package in production
    localparam logic [11:0] REG_BAYER_PATTERN  = 12'h000;
    localparam logic [11:0] REG_DEBAYER_ENABLE = 12'h004;
    localparam logic [11:0] REG_STATUS         = 12'h008;

    logic [31:0] bayer_pattern_reg;
    logic [31:0] debayer_enable_reg;

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            bayer_pattern_reg <= '0;
            debayer_enable_reg <= '0;
        end else if (wr_en) begin
            case (addr)
                REG_BAYER_PATTERN:  bayer_pattern_reg <= wdata;
                REG_DEBAYER_ENABLE: debayer_enable_reg <= wdata;
                default: ;
            endcase
        end
    end

    always_comb begin
        case (addr)
            REG_BAYER_PATTERN:  rdata = bayer_pattern_reg;
            REG_DEBAYER_ENABLE: rdata = debayer_enable_reg;
            REG_STATUS:         rdata = 32'hDEAD_BEEF;
            default:            rdata = '0;
        endcase
    end

endmodule
```

### `test/tb_variant.sv` — Per-Variant Testbench (R1/R2)

This testbench is also text-stable — it imports `isp_types_package` and works with whatever constants that package defines. The **same testbench file** is used for both the 8bpc and 12bpc variants.

```systemverilog
module tb_variant;
    import shared_types_pkg::*;
    import isp_types_package::*;

    logic clk, rst_n;
    initial clk = 0;
    always #5 clk = ~clk;

    rdy_vld_if #(.data_t(video_bayer_t)) raw_in ();
    rdy_vld_if #(.data_t(video_rgb_t))   rgb_out ();

    debayer u_dut (
        .video_raw_stream(raw_in),
        .video_rgb_stream(rgb_out),
        .clk(clk),
        .rst_n(rst_n)
    );

    initial begin
        rst_n = 0;
        raw_in.vld = 0;
        rgb_out.rdy = 1;
        #20 rst_n = 1;

        // Report which variant we're running
        $display("INFO: BITS_PER_PIXEL_COLOR = %0d", BITS_PER_PIXEL_COLOR);
        $display("INFO: PIXELS_PER_CLOCK     = %0d", PIXELS_PER_CLOCK);
        $display("INFO: MAX_PIXEL_VALUE      = %0d", MAX_PIXEL_VALUE);
        $display("INFO: video_bayer_t width  = %0d bits", $bits(video_bayer_t));
        $display("INFO: video_rgb_t width    = %0d bits", $bits(video_rgb_t));
        $display("INFO: pixel_t width        = %0d bits", $bits(pixel_t));

        // ---- Test: Send a bayer frame, verify RGB output ----
        @(posedge clk);

        // Build bayer input using struct assignment
        begin
            video_bayer_t bayer_frame;
            bayer_frame.frame.eof = 0;
            bayer_frame.frame.sof = 1;
            bayer_frame.frame.eol = 0;
            bayer_frame.data = '0;
            bayer_frame.data.pixels[0] = pixel_t'(42);
            bayer_frame.data.pixels[1] = pixel_t'(100);
            raw_in.data = bayer_frame;
        end
        raw_in.vld = 1;
        @(posedge clk);
        raw_in.vld = 0;

        // Check output
        @(posedge clk);
        begin
            video_rgb_t rgb_frame;
            rgb_frame = rgb_out.data;

            $display("Output: sof=%0b, pixel[0].r=%0d, pixel[0].g=%0d, pixel[0].b=%0d",
                rgb_frame.frame.sof,
                rgb_frame.data.pixels[0].r,
                rgb_frame.data.pixels[0].g,
                rgb_frame.data.pixels[0].b);

            // Verify passthrough: each RGB channel should equal the bayer pixel
            assert(rgb_frame.frame.sof == 1'b1)
                else $fatal(1, "FAIL: sof mismatch");
            assert(rgb_frame.data.pixels[0].r == pixel_t'(42))
                else $fatal(1, "FAIL: pixel[0].r mismatch, got %0d expected 42",
                    rgb_frame.data.pixels[0].r);
            assert(rgb_frame.data.pixels[0].g == pixel_t'(42))
                else $fatal(1, "FAIL: pixel[0].g mismatch");
            assert(rgb_frame.data.pixels[0].b == pixel_t'(42))
                else $fatal(1, "FAIL: pixel[0].b mismatch");
            assert(rgb_frame.data.pixels[1].r == pixel_t'(100))
                else $fatal(1, "FAIL: pixel[1].r mismatch");
        end

        // Verify derived constant chain
        $display("INFO: BPPC_P1=%0d, BPPC_P2=%0d", BPPC_P1, BPPC_P2);
        assert(BPPC_P1 == BITS_PER_PIXEL_COLOR + 1)
            else $fatal(1, "FAIL: BPPC_P1 derivation");
        assert($bits(acc2_t) == BPPC_P1)
            else $fatal(1, "FAIL: acc2_t width mismatch");

        $display("PASS: Variant test passed (BITS_PER_PIXEL_COLOR=%0d)",
            BITS_PER_PIXEL_COLOR);
        $finish;
    end

endmodule
```

### `test/tb_mparam.sv` — Module-Parameter Testbench (R3)

Tests module-level parameters with two differently-parameterized instances in the **same** testbench. This validates that the IP module pattern (local types from module parameters) works and that two instances with different widths coexist in one Verilator build.

```systemverilog
module tb_mparam;
    import shared_types_pkg::*;

    logic clk, rst_n;
    initial clk = 0;
    always #5 clk = ~clk;

    // ---- 8bpc types (TB-local, matching module-param instance) ----
    localparam int unsigned BPC_8 = 8;
    localparam int unsigned PPC_8 = 4;
    typedef logic[BPC_8-1:0] pixel_8_t;
    typedef struct packed { pixel_8_t [PPC_8-1:0] pixels; } bayer_ppc_8_t;
    typedef struct packed { bayer_ppc_8_t data; video_frame_t frame; } video_bayer_8_t;
    typedef struct packed { pixel_8_t b, g, r; } rgb_pixel_8_t;
    typedef struct packed { rgb_pixel_8_t [PPC_8-1:0] pixels; } rgb_ppc_8_t;
    typedef struct packed { rgb_ppc_8_t data; video_frame_t frame; } video_rgb_8_t;

    // ---- 12bpc types (TB-local) ----
    localparam int unsigned BPC_12 = 12;
    localparam int unsigned PPC_12 = 8;
    typedef logic[BPC_12-1:0] pixel_12_t;
    typedef struct packed { pixel_12_t [PPC_12-1:0] pixels; } bayer_ppc_12_t;
    typedef struct packed { bayer_ppc_12_t data; video_frame_t frame; } video_bayer_12_t;
    typedef struct packed { pixel_12_t b, g, r; } rgb_pixel_12_t;
    typedef struct packed { rgb_pixel_12_t [PPC_12-1:0] pixels; } rgb_ppc_12_t;
    typedef struct packed { rgb_ppc_12_t data; video_frame_t frame; } video_rgb_12_t;

    // ---- Interfaces ----
    rdy_vld_if #(.data_t(video_bayer_8_t))  bayer_8 ();
    rdy_vld_if #(.data_t(video_rgb_8_t))    rgb_8 ();
    rdy_vld_if #(.data_t(video_bayer_12_t)) bayer_12 ();
    rdy_vld_if #(.data_t(video_rgb_12_t))   rgb_12 ();

    // ---- Two instances with different parameters ----
    interpolate_mparam #(
        .BITS_PER_PIXEL_COLOR(8),
        .MAX_PIXEL_VALUE(255),
        .PIXELS_PER_CLOCK(4)
    ) u_interp_8bpc (
        .bayer_in(bayer_8), .rgb_out(rgb_8),
        .clk(clk), .rst_n(rst_n)
    );

    interpolate_mparam #(
        .BITS_PER_PIXEL_COLOR(12),
        .MAX_PIXEL_VALUE(4095),
        .PIXELS_PER_CLOCK(8)
    ) u_interp_12bpc (
        .bayer_in(bayer_12), .rgb_out(rgb_12),
        .clk(clk), .rst_n(rst_n)
    );

    initial begin
        rst_n = 0;
        bayer_8.vld = 0;  bayer_12.vld = 0;
        rgb_8.rdy = 1;    rgb_12.rdy = 1;
        #20 rst_n = 1;

        // Test 8bpc instance
        @(posedge clk);
        begin
            video_bayer_8_t vb;
            vb = '0;
            vb.frame.sof = 1'b1;
            vb.data.pixels[0] = 8'hAA;
            bayer_8.data = vb;
        end
        bayer_8.vld = 1;
        @(posedge clk);
        bayer_8.vld = 0;
        @(posedge clk);
        begin
            video_rgb_8_t vr;
            vr = rgb_8.data;
            assert(vr.data.pixels[0].r == 8'hAA)
                else $fatal(1, "FAIL: 8bpc pixel mismatch");
            $display("8bpc: pixel[0].r = 0x%h — OK", vr.data.pixels[0].r);
        end

        // Test 12bpc instance
        @(posedge clk);
        begin
            video_bayer_12_t vb;
            vb = '0;
            vb.frame.sof = 1'b1;
            vb.data.pixels[0] = 12'hBBB;
            bayer_12.data = vb;
        end
        bayer_12.vld = 1;
        @(posedge clk);
        bayer_12.vld = 0;
        @(posedge clk);
        begin
            video_rgb_12_t vr;
            vr = rgb_12.data;
            assert(vr.data.pixels[0].r == 12'hBBB)
                else $fatal(1, "FAIL: 12bpc pixel mismatch");
            $display("12bpc: pixel[0].r = 0x%h — OK", vr.data.pixels[0].r);
        end

        $display("PASS: Module-parameter test passed (R3)");
        $finish;
    end

endmodule
```

### `test/tb_decode.sv` — Named Constant Decode Test (R4)

```systemverilog
module tb_decode;

    logic clk, rst_n;
    initial clk = 0;
    always #5 clk = ~clk;

    logic [11:0] addr;
    logic [31:0] wdata, rdata;
    logic wr_en;

    decode_named u_dut (.*);

    initial begin
        rst_n = 0;
        addr = '0; wdata = '0; wr_en = 0;
        #20 rst_n = 1;

        // Write to REG_BAYER_PATTERN (0x000)
        @(posedge clk);
        addr = 12'h000; wdata = 32'h0000_0002; wr_en = 1;
        @(posedge clk);
        wr_en = 0;

        // Read back
        @(posedge clk);
        addr = 12'h000;
        @(posedge clk);
        assert(rdata == 32'h0000_0002)
            else $fatal(1, "FAIL: REG_BAYER_PATTERN readback, got 0x%h", rdata);

        // Write to REG_DEBAYER_ENABLE (0x004)
        @(posedge clk);
        addr = 12'h004; wdata = 32'h0000_0001; wr_en = 1;
        @(posedge clk);
        wr_en = 0;
        @(posedge clk);
        addr = 12'h004;
        @(posedge clk);
        assert(rdata == 32'h0000_0001)
            else $fatal(1, "FAIL: REG_DEBAYER_ENABLE readback");

        // Read REG_STATUS (0x008)
        @(posedge clk);
        addr = 12'h008;
        @(posedge clk);
        assert(rdata == 32'hDEAD_BEEF)
            else $fatal(1, "FAIL: REG_STATUS readback");

        $display("PASS: Named constant decode test passed (R4)");
        $finish;
    end

endmodule
```

### `rtl/preprocess_mparam.sv` — Parameterized Passthrough (R6)

Simple passthrough with module parameters for consistency. In a real design, preprocess would define local types and manipulate pixel data. For the prototype, it validates the interface binding path.

```systemverilog
module preprocess_mparam
    import shared_types_pkg::*;
    import isp_types_package::*;
#(
    parameter int unsigned BITS_PER_PIXEL_COLOR = isp_types_package::BITS_PER_PIXEL_COLOR,
    parameter int unsigned PIXELS_PER_CLOCK = isp_types_package::PIXELS_PER_CLOCK
) (
    rdy_vld_if.dst bayer_in,
    rdy_vld_if.src bayer_out,
    input clk, rst_n
);

    assign bayer_in.rdy = bayer_out.rdy;
    assign bayer_out.data = bayer_in.data;
    assign bayer_out.vld = bayer_in.vld;

endmodule
```

### `rtl/camera_subsystem.sv` — Dual-Instance System Container (R6)

The core R6 test module. A system container with two camera channels — high-res (12bpc, 8 PPC) and low-res (8bpc, 4 PPC). The container defines **local types per instance** to create internal interfaces, then instantiates the same IP modules with different parameters.

This models the real-world scenario: a chip integrates two debayer pipelines for cameras with different capabilities. The package is compiled once per build — it cannot serve both parameter sets. The container must define types locally for each instance.

```systemverilog
module camera_subsystem
    import shared_types_pkg::*;
(
    // High-res camera port (12bpc, 8 PPC)
    rdy_vld_if.dst hires_raw,
    rdy_vld_if.src hires_rgb,
    // Low-res camera port (8bpc, 4 PPC)
    rdy_vld_if.dst lores_raw,
    rdy_vld_if.src lores_rgb,
    input clk, rst_n
);

    // ---- High-res types (12bpc, 8 PPC) ----
    localparam int unsigned HIRES_BPC = 12;
    localparam int unsigned HIRES_PPC = 8;
    localparam int unsigned HIRES_MPV = 4095;
    typedef logic[HIRES_BPC-1:0] hires_pixel_t;
    typedef struct packed { hires_pixel_t b, g, r; } hires_rgb_pixel_t;
    typedef struct packed { hires_pixel_t [HIRES_PPC-1:0] pixels; } hires_bayer_ppc_t;
    typedef struct packed { hires_rgb_pixel_t [HIRES_PPC-1:0] pixels; } hires_rgb_ppc_t;
    typedef struct packed { hires_bayer_ppc_t data; video_frame_t frame; } hires_video_bayer_t;
    typedef struct packed { hires_rgb_ppc_t data; video_frame_t frame; } hires_video_rgb_t;

    // ---- Low-res types (8bpc, 4 PPC) ----
    localparam int unsigned LORES_BPC = 8;
    localparam int unsigned LORES_PPC = 4;
    localparam int unsigned LORES_MPV = 255;
    typedef logic[LORES_BPC-1:0] lores_pixel_t;
    typedef struct packed { lores_pixel_t b, g, r; } lores_rgb_pixel_t;
    typedef struct packed { lores_pixel_t [LORES_PPC-1:0] pixels; } lores_bayer_ppc_t;
    typedef struct packed { lores_rgb_pixel_t [LORES_PPC-1:0] pixels; } lores_rgb_ppc_t;
    typedef struct packed { lores_bayer_ppc_t data; video_frame_t frame; } lores_video_bayer_t;
    typedef struct packed { lores_rgb_ppc_t data; video_frame_t frame; } lores_video_rgb_t;

    // ---- Internal interfaces (container-local types) ----
    rdy_vld_if #(.data_t(hires_video_bayer_t)) hires_pp_to_interp ();
    rdy_vld_if #(.data_t(lores_video_bayer_t)) lores_pp_to_interp ();

    // ---- High-res pipeline ----
    preprocess_mparam #(
        .BITS_PER_PIXEL_COLOR(HIRES_BPC),
        .PIXELS_PER_CLOCK(HIRES_PPC)
    ) u_hires_pp (
        .bayer_in(hires_raw),
        .bayer_out(hires_pp_to_interp),
        .clk(clk), .rst_n(rst_n)
    );

    interpolate_mparam #(
        .BITS_PER_PIXEL_COLOR(HIRES_BPC),
        .MAX_PIXEL_VALUE(HIRES_MPV),
        .PIXELS_PER_CLOCK(HIRES_PPC)
    ) u_hires_interp (
        .bayer_in(hires_pp_to_interp),
        .rgb_out(hires_rgb),
        .clk(clk), .rst_n(rst_n)
    );

    // ---- Low-res pipeline ----
    preprocess_mparam #(
        .BITS_PER_PIXEL_COLOR(LORES_BPC),
        .PIXELS_PER_CLOCK(LORES_PPC)
    ) u_lores_pp (
        .bayer_in(lores_raw),
        .bayer_out(lores_pp_to_interp),
        .clk(clk), .rst_n(rst_n)
    );

    interpolate_mparam #(
        .BITS_PER_PIXEL_COLOR(LORES_BPC),
        .MAX_PIXEL_VALUE(LORES_MPV),
        .PIXELS_PER_CLOCK(LORES_PPC)
    ) u_lores_interp (
        .bayer_in(lores_pp_to_interp),
        .rgb_out(lores_rgb),
        .clk(clk), .rst_n(rst_n)
    );

endmodule
```

**Key questions this validates:**
- Can a system container define local types for two different parameter sets and create interfaces with them?
- Does data flow correctly across the boundary: container-local `hires_video_bayer_t` (in the interface) → module-local `video_bayer_t` (from module params, same width)?
- Do two differently-parameterized `interpolate_mparam` instances coexist in one Verilator build?
- Is `struct packed` structural type compatibility honored across scope boundaries (container-local type ↔ module-local type)?

### `test/tb_dual_instance.sv` — Dual-Instance Integration Test (R6)

Tests both camera channels end-to-end in a single build. The testbench defines local types matching each channel, creates typed interfaces, and verifies data integrity through the full pipeline.

```systemverilog
module tb_dual_instance;
    import shared_types_pkg::*;

    logic clk, rst_n;
    initial clk = 0;
    always #5 clk = ~clk;

    // ---- High-res types (12bpc, 8 PPC) — must match camera_subsystem ----
    localparam int unsigned HIRES_BPC = 12;
    localparam int unsigned HIRES_PPC = 8;
    typedef logic[HIRES_BPC-1:0] hires_pixel_t;
    typedef struct packed { hires_pixel_t b, g, r; } hires_rgb_pixel_t;
    typedef struct packed { hires_pixel_t [HIRES_PPC-1:0] pixels; } hires_bayer_ppc_t;
    typedef struct packed { hires_rgb_pixel_t [HIRES_PPC-1:0] pixels; } hires_rgb_ppc_t;
    typedef struct packed { hires_bayer_ppc_t data; video_frame_t frame; } hires_video_bayer_t;
    typedef struct packed { hires_rgb_ppc_t data; video_frame_t frame; } hires_video_rgb_t;

    // ---- Low-res types (8bpc, 4 PPC) — must match camera_subsystem ----
    localparam int unsigned LORES_BPC = 8;
    localparam int unsigned LORES_PPC = 4;
    typedef logic[LORES_BPC-1:0] lores_pixel_t;
    typedef struct packed { lores_pixel_t b, g, r; } lores_rgb_pixel_t;
    typedef struct packed { lores_pixel_t [LORES_PPC-1:0] pixels; } lores_bayer_ppc_t;
    typedef struct packed { lores_rgb_pixel_t [LORES_PPC-1:0] pixels; } lores_rgb_ppc_t;
    typedef struct packed { lores_bayer_ppc_t data; video_frame_t frame; } lores_video_bayer_t;
    typedef struct packed { lores_rgb_ppc_t data; video_frame_t frame; } lores_video_rgb_t;

    // ---- Interfaces ----
    rdy_vld_if #(.data_t(hires_video_bayer_t)) hires_raw ();
    rdy_vld_if #(.data_t(hires_video_rgb_t))   hires_rgb ();
    rdy_vld_if #(.data_t(lores_video_bayer_t)) lores_raw ();
    rdy_vld_if #(.data_t(lores_video_rgb_t))   lores_rgb ();

    camera_subsystem u_dut (
        .hires_raw(hires_raw), .hires_rgb(hires_rgb),
        .lores_raw(lores_raw), .lores_rgb(lores_rgb),
        .clk(clk), .rst_n(rst_n)
    );

    initial begin
        rst_n = 0;
        hires_raw.vld = 0; lores_raw.vld = 0;
        hires_rgb.rdy = 1; lores_rgb.rdy = 1;
        #20 rst_n = 1;

        $display("INFO: hires_video_bayer_t = %0d bits", $bits(hires_video_bayer_t));
        $display("INFO: lores_video_bayer_t = %0d bits", $bits(lores_video_bayer_t));
        $display("INFO: hires_video_rgb_t   = %0d bits", $bits(hires_video_rgb_t));
        $display("INFO: lores_video_rgb_t   = %0d bits", $bits(lores_video_rgb_t));

        // ---- Test high-res path (12bpc, 8 PPC) ----
        @(posedge clk);
        begin
            hires_video_bayer_t vb;
            vb = '0;
            vb.frame.sof = 1'b1;
            vb.data.pixels[0] = 12'hABC;
            hires_raw.data = vb;
        end
        hires_raw.vld = 1;
        @(posedge clk);
        hires_raw.vld = 0;
        @(posedge clk);
        begin
            hires_video_rgb_t vr;
            vr = hires_rgb.data;
            assert(vr.data.pixels[0].r == 12'hABC)
                else $fatal(1, "FAIL: hires pixel[0].r mismatch, got 0x%h", vr.data.pixels[0].r);
            assert(vr.data.pixels[0].g == 12'hABC)
                else $fatal(1, "FAIL: hires pixel[0].g mismatch");
            assert(vr.frame.sof == 1'b1)
                else $fatal(1, "FAIL: hires sof mismatch");
            $display("hires: pixel[0].r = 0x%h — OK", vr.data.pixels[0].r);
        end

        // ---- Test low-res path (8bpc, 4 PPC) ----
        @(posedge clk);
        begin
            lores_video_bayer_t vb;
            vb = '0;
            vb.frame.sof = 1'b1;
            vb.data.pixels[0] = 8'h42;
            lores_raw.data = vb;
        end
        lores_raw.vld = 1;
        @(posedge clk);
        lores_raw.vld = 0;
        @(posedge clk);
        begin
            lores_video_rgb_t vr;
            vr = lores_rgb.data;
            assert(vr.data.pixels[0].r == 8'h42)
                else $fatal(1, "FAIL: lores pixel[0].r mismatch, got 0x%h", vr.data.pixels[0].r);
            assert(vr.data.pixels[0].g == 8'h42)
                else $fatal(1, "FAIL: lores pixel[0].g mismatch");
            assert(vr.frame.sof == 1'b1)
                else $fatal(1, "FAIL: lores sof mismatch");
            $display("lores: pixel[0].r = 0x%h — OK", vr.data.pixels[0].r);
        end

        $display("PASS: Dual-instance test — 12bpc and 8bpc in one build (R6)");
        $finish;
    end

endmodule
```

**Data flow tested:** For each channel: TB typed interface → `camera_subsystem` (container-local types, internal interfaces) → `preprocess_mparam` (parameterized passthrough) → internal `rdy_vld_if` (container-local type as `data_t`) → `interpolate_mparam` (module-local types from params) → back to TB. Both channels run in the same Verilator build with different type widths.

## Makefile

Per-variant build targets for R1/R2, plus a single multi-instance build for R6.

```makefile
VERILATOR = verilator
VERILATOR_FLAGS = --binary --timing -Wall -Wno-UNUSEDSIGNAL -Wno-UNUSEDPARAM \
                  --trace --x-initial-edge

SV_SHARED = packages/shared_types_pkg.sv interfaces/rdy_vld_if.sv
SV_MODULES = rtl/interpolate.sv rtl/preprocess.sv rtl/debayer.sv

BUILD = build

$(BUILD):
	@mkdir -p $(BUILD)

#--- Step 1: Per-variant build — 8bpc (R1/R2) ---

step1_8bpc: | $(BUILD)
	@echo "=== Step 1a: Per-variant build — 8bpc (R1/R2) ==="
	$(VERILATOR) $(VERILATOR_FLAGS) --top-module tb_variant \
	    $(SV_SHARED) packages/isp_types_pkg_8bpc.sv \
	    $(SV_MODULES) test/tb_variant.sv \
	    --Mdir $(BUILD)/step1_8bpc -o Vtb_variant
	$(BUILD)/step1_8bpc/Vtb_variant

#--- Step 1: Per-variant build — 12bpc (R1/R2) ---

step1_12bpc: | $(BUILD)
	@echo "=== Step 1b: Per-variant build — 12bpc (R1/R2) ==="
	$(VERILATOR) $(VERILATOR_FLAGS) --top-module tb_variant \
	    $(SV_SHARED) packages/isp_types_pkg_12bpc.sv \
	    $(SV_MODULES) test/tb_variant.sv \
	    --Mdir $(BUILD)/step1_12bpc -o Vtb_variant
	$(BUILD)/step1_12bpc/Vtb_variant

#--- Step 2: Module-level parameters (R3) ---
# Package needed for default param values in interpolate_mparam

step2: | $(BUILD)
	@echo "=== Step 2: Module-level parameters — two instances (R3) ==="
	$(VERILATOR) $(VERILATOR_FLAGS) --top-module tb_mparam \
	    $(SV_SHARED) packages/isp_types_pkg_8bpc.sv \
	    rtl/interpolate_mparam.sv test/tb_mparam.sv \
	    --Mdir $(BUILD)/step2 -o Vtb_mparam
	$(BUILD)/step2/Vtb_mparam

#--- Step 3: Named constant decode (R4) ---

step3: | $(BUILD)
	@echo "=== Step 3: Named constant decode (R4) ==="
	$(VERILATOR) $(VERILATOR_FLAGS) --top-module tb_decode \
	    rtl/decode_named.sv test/tb_decode.sv \
	    --Mdir $(BUILD)/step3 -o Vtb_decode
	$(BUILD)/step3/Vtb_decode

#--- Step 4: Dual-instance integration (R6) ---
# Single build with BOTH 12bpc and 8bpc instances — package provides defaults only

SV_MPARAM = rtl/interpolate_mparam.sv rtl/preprocess_mparam.sv rtl/camera_subsystem.sv

step4: | $(BUILD)
	@echo "=== Step 4: Dual-instance — 12bpc + 8bpc in one build (R6) ==="
	$(VERILATOR) $(VERILATOR_FLAGS) --top-module tb_dual_instance \
	    $(SV_SHARED) packages/isp_types_pkg_8bpc.sv \
	    $(SV_MPARAM) test/tb_dual_instance.sv \
	    --Mdir $(BUILD)/step4 -o Vtb_dual_instance
	$(BUILD)/step4/Vtb_dual_instance

#--- Phony targets ---

.PHONY: step1_8bpc step1_12bpc step1 step2 step3 step4 all clean

step1: step1_8bpc step1_12bpc

all: step1 step2 step3 step4

clean:
	rm -rf $(BUILD)
```

**Key points:**
- Steps 1a and 1b compile the **exact same** module source against different package files. This validates per-variant builds.
- Step 2 needs a package file (8bpc, arbitrary) because `interpolate_mparam` imports it for default parameter values. The testbench overrides all parameters at instantiation — the package defaults are unused.
- Step 4 is a **single build** with both 12bpc and 8bpc instances. The package provides default values only — `camera_subsystem` overrides all parameters per instance. This is the key multi-instance test.

## Implementation Order

| Step | Tests | Validates | Depends On | Effort |
|------|-------|-----------|------------|--------|
| **1a** | `tb_variant` with 8bpc package | R1/R2 — text-stable module source with 8bpc package constants | None | Medium — write all source files |
| **1b** | `tb_variant` with 12bpc package | R1/R2 — same source, different constants, correct widths | Step 1a (same files) | Tiny — just write the 12bpc package |
| **2** | `tb_mparam` | R3 — IP module pattern: params default from package, local types, two instances in one build | None (independent) | Small |
| **3** | `tb_decode` | R4 — named constant decode | None (independent) | Small |
| **4** | `tb_dual_instance` | R6 — system container with two differently-parameterized IP instances, container-local types, structural type compatibility at boundaries | Step 2 (reuses `interpolate_mparam.sv`) | Medium — write container, preprocess_mparam, testbench |

Steps 1a/1b and step 2 are independent and can be developed in parallel. Step 4 is the highest-risk test — it exercises structural type compatibility when three scopes (testbench, container, IP module) each define types locally with the same layout. Step 3 is independent.

**Stop early** if step 1a fails — basic per-variant pattern doesn't work. If step 2 fails — module-local types don't work in Verilator — skip step 4.

## Expected Outcomes and Decisions

| Outcome | Decision |
|---------|----------|
| Steps 1a+1b pass | **Confirm per-variant package generation** as the primary SV parameterization mechanism for single-instance builds. Generator changes are minimal: make `localparam` value declarations variant-specific, everything else is already text-stable. |
| Step 1a passes, 1b fails (width issues) | Investigate which derived constant or type breaks at the new widths. Likely a boundary case in Verilator or a type dependency that doesn't propagate correctly. Fix and retry. |
| Step 2 passes | **IP module pattern confirmed.** Modules can define parameterized types locally from module parameters that default to the package. Required for multi-instance builds. Also skip step 4 dependency concern. |
| Step 2 fails | Module-local types in interface binding don't work under Verilator. **Blocker for multi-instance use case.** Per-variant builds (step 1) still work for single-instance IPs. Multi-instance designs would require per-instance packages (the approach we want to avoid). Skip step 4. |
| Step 3 passes | Named constants confirmed working for decode. Proceed with A2 (named-constant decode in SV) from `plan-foundation-address-decode.md`. |
| Step 4 passes | **Dual-instance integration works.** Container-local types and module-local types are structurally compatible at interface boundaries. A system can instantiate the same IP with different parameters in one build. The generator must support: (1) IP modules with parameterized local types, (2) container modules with per-instance local types. |
| Step 4 fails (type compatibility) | Structural type compatibility between container-local and module-local types fails in Verilator. **Implication:** even though both types have identical `struct packed` layouts, Verilator treats them as incompatible across scopes. Workaround: use a single set of types (from one package) or investigate Verilator cast mechanisms. |

## Specific Risks and Mitigations

### Derived constant chain across variants

When `BITS_PER_PIXEL_COLOR` changes from 8 to 12, all derived constants (`BPPC_P1`, `BPPC_P2`, etc.) and all types (`pixel_t`, `acc2_t`, etc.) must change width accordingly. The symbolic expressions in the package handle this automatically, but this needs end-to-end validation — especially for types used in interface `data_t` parameters, where width changes affect interface signal widths.

**Mitigation**: The testbench explicitly checks `$bits()` of key types and verifies constant derivation chains.

### Module-local types in interface binding (R3)

For the IP module pattern: `rdy_vld_if #(.data_t(local_struct))` where `local_struct` is defined from module parameters. Verilator must resolve the type at elaboration time. This exercises a different Verilator code path than package-typed interfaces.

**Mitigation**: If this fails, multi-instance builds (R6) are also blocked. Per-variant builds (R1/R2) with package types still work for single-instance IPs.

### Structural type compatibility across module boundaries (R3/R6)

When parent and child modules both define `video_bayer_t` locally (from different parameter/localparam sources but with the same `struct packed` layout), Verilator must treat these as structurally compatible at the interface boundary. SV uses structural typing for `struct packed`, so this should work, but it's a less-tested Verilator path.

**Mitigation**: If structural compatibility fails, the fallback is per-instance packages (Approach B — different package names per instance), which we want to avoid. This would be a significant finding.

### Dual-instance type scope crossing (R6)

The highest-risk scenario in the prototype. Three scopes each define types with the same layout:

```
Testbench scope:   rdy_vld_if #(.data_t(hires_video_bayer_t))  — TB-local type
                          ↓ (interface binding to container port)
Container scope:   rdy_vld_if #(.data_t(hires_video_bayer_t))  — container-local type
                          ↓ (interface binding to child port)
IP module scope:   bayer_data = bayer_in.data                  — module-local video_bayer_t
```

All three `video_bayer_t` types are structurally identical `struct packed` with the same member widths (12bpc, 8 PPC in this case), but they're defined in different scopes. SV says they're compatible; the question is whether Verilator agrees.

**Mitigation**: If this fails, investigate whether Verilator needs explicit type casts or whether all levels must reference a single type definition. Worst case: per-instance packages (different names) to provide a single type source per instance.

## Mapping: C++ Config Template ↔ SV Parameterization

| Concept | C++ (Config Template) | SV (Per-Variant Package + Module Params) |
|---------|----------------------|--------------------------|
| Parameter container | `struct config_8bpc { static constexpr ... }` | `package isp_types_package; localparam ... endpackage` |
| Type text-stability | `template<typename Config> struct rgb_pixel_t` with `Config::` refs | `typedef struct packed { pixel_t b, g, r; }` — types reference symbolic constants/params |
| What varies per variant | Config struct (external to IP) | Package `localparam` values (regenerated) |
| What's text-stable | All IP source (templates) | All IP module source + package type/struct definitions |
| Single-instance mechanism | Config template | Per-variant package build |
| Multi-instance mechanism | Two Config instantiations in same binary | Module parameters (default from package) + container-local types |
| Tandem pairing | `interpolate<config_8bpc>` model ↔ RTL built with 8bpc package | SC model with `config_8bpc` ↔ RTL verilated with 8bpc package |

## Success Deliverables

1. A working `proto_rtl/` directory with passing tests for per-variant builds (R1/R2), module parameters (R3), named constant decode (R4), and dual-instance integration (R6)
2. Confirmation that per-variant package generation is the right mechanism for single-instance builds
3. Confirmation that the IP module pattern (params defaulting from package, local types) works for multi-instance builds
4. Assessment of structural type compatibility at container boundaries (container-local types ↔ module-local types)
5. The POC Makefile documenting both per-variant and multi-instance build patterns
6. Notes on any Verilator-specific behavior or limitations encountered
7. Comparison table: how SV per-variant packages map to C++ Config templates (above)

## Relationship to Existing Plans

| Plan | How This RTL P0 Relates |
|------|-------------------------|
| `plan-p0-proof-of-concept.md` | **Predecessor** — this is the RTL counterpart of that completed SystemC P0. Simpler because SV types are already text-stable. |
| `plan-ip-namespaces-and-parameterization.md` Section 4.3 | **Answers Open Question 2** — SV parameterization strategy: per-variant package generation for single-instance builds, module parameters with local types for multi-instance builds. Not per-instance packages, not parameterized packages. |
| `plan-parameterizable-config-template.md` Steps 10, 12d | **Validates** SV constant emission patterns and named-constant decode. |
| `plan-development-ordering.md` Items S1, S2 | **Informs** S1 (omit parameterizable constants from IP package) and S2 (per-instance package generation). S2 simplifies: same package name, different values per variant, not separate named packages. |
| `plan-foundation-address-decode.md` A2 | **Validates** SV named-constant decode (R4). |
