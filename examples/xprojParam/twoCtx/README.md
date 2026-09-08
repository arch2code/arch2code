# `twoCtx`, the two-context block

**Status: regression fixture.** The chain builds, links, and runs. It is the
`xproj-twoctx` target and runs as part of `pipeline-test`. The guard is the
checkers' run-time assertions, not the fact that generation succeeded. A wrong
`configContext` choice, or a Config missing a field, fails the run.

## What it is

One block, `xpTwoCtxDut`, whose `params:` names one parameterizable constant
declared in an INCLUDED file (`DP_WIDTH`, from `dpLeaf/yaml/xpDpLeaf.yaml`) and
one declared in its OWN file (`TC_GAIN`), with both bound to non-default values
in one declared variant (12 and 5, against declared defaults of 8 and 2).

A second block, `xpTwoCtxBare`, is the same two-context shape with no
parameterizable structure on its own surface. It names both knobs but carries
only a literal-width port. The two blocks reach their `configContext` by
different rules (a surface scan for `xpTwoCtxDut`, the first entry of `params:`
for `xpTwoCtxBare`), and the fixture checks that both land on the same bound
values regardless. Their Config names do not depend on that order: both
variants are declared by this project, so both spell
`xpTwoCtx_<block>TwoctxConfig`, differing only in the block.

The full chain: `xpTwoCtxLitSrc` drives literal samples into `xpTwoCtxBare`
directly. `xpTwoCtxSrc` drives `dpSt` samples (sized by `DP_WIDTH`) into
`xpTwoCtxDut`, which checks them and forwards a `tcSt` sample offset by
`TC_GAIN_X2` into `xpTwoCtxSnk`. `xpTwoCtxSnk` reaches `TC_GAIN` through its own file's
context rather than the included one, so it and `xpTwoCtxDut` agreeing on the
value is itself part of what the run proves.

## What is emitted

`xpTwoCtxDut`'s Config carries exactly the two parameters it names, nothing
from the included file it did not name (`registrar/xpTwoCtx_xpTwoCtxDutVariantConfig.cppm`):

```cpp
export struct xpTwoCtx_xpTwoCtxDutTwoctxConfig {
    static constexpr uint32_t DP_WIDTH = 12;
    static constexpr uint32_t TC_GAIN = 5;
};
```

`xpTwoCtxBare`'s Config, reached through the other resolution rule, carries the
same two fields (`registrar/xpTwoCtx_xpTwoCtxBareVariantConfig.cppm`):

```cpp
export struct xpTwoCtx_xpTwoCtxBareTwoctxConfig {
    static constexpr uint32_t TC_GAIN = 5;
    static constexpr uint32_t DP_WIDTH = 12;
};
```

`xpTwoCtxSrc` and `xpTwoCtxSnk` each name only one of the two parameters, and
each gets a Config carrying only that one:

```cpp
// registrar/xpTwoCtx_xpTwoCtxSrcVariantConfig.cppm
export struct xpTwoCtx_xpTwoCtxSrcTwoctxConfig {
    static constexpr uint32_t DP_WIDTH = 12;
};

// registrar/xpTwoCtx_xpTwoCtxSnkVariantConfig.cppm
export struct xpTwoCtx_xpTwoCtxSnkTwoctxConfig {
    static constexpr uint32_t TC_GAIN = 5;
};
```

Every Config here - both blocks' defaults and every declared variant - lives in
its declaring project's own registrar-domain module (`xpTwoCtx.<block>.config`,
one per block); the context header (`model/xpTwoCtxVariantConfig.h`) carries
none of them.

Both `xpTwoCtxDut` and `xpTwoCtxBare` derive `TC_GAIN_X2 = Config::TC_GAIN * 2`
in their Base class, so each Config only needs to carry `TC_GAIN` itself. Both
also derive `DP_WIDTH_X2 = Config::DP_WIDTH * 2` over the include-reached
parameter, and the emitted RTL for both blocks spells it as
`localparam DP_WIDTH_X2 = DP_WIDTH * 2`, the module parameter rather than the
included file's default literal of 8. The `xproj-twoctx` Makefile target greps
both `.sv` files for that exact line, so a regression that makes the emitter
fall back to the constant's default would fail the build, not just the run.

## What the run asserts

- `xpTwoCtxDut` asserts at run time that `DP_WIDTH == 12` and `TC_GAIN == 5`,
  then checks each `dpSt` sample's `tag`, `data`, and `mark` fields against
  what `xpTwoCtxSrc` drove. The payload crosses the thunker by `bit_cast`, so
  the field checks prove routing, not width; the two literal asserts are what
  pin the bound values.
- `xpTwoCtxDut` static-asserts that its own Config has no `DP_ALGO` member (the
  included file declares it, but this block does not name it).
- `xpTwoCtxSnk` checks each `tcSt` sample's `tag` and `val` against its OWN
  Config's `TC_GAIN_X2`, so it and `xpTwoCtxDut` reaching the same value proves
  the two context paths agree.
- `xpTwoCtxBare` static-asserts the same absent-`DP_ALGO` fact as `xpTwoCtxDut`,
  and asserts at run time that `DP_WIDTH == 12`, `TC_GAIN == 5`,
  `TC_GAIN_X2 == 10`, and `DP_WIDTH_X2 == 24`, so the params-only resolution
  rule reached both bound values and both derived constants. It also checks
  each `litSt` sample's `v` field against what `xpTwoCtxLitSrc` drove.

## Build and check

```
make xproj-twoctx           # runs xproj-depth first, then twoCtx generates and runs
```

or, from this directory:

```
make clean && make gen -j && make -C rundir -j run
```
