# `twoCtx` — the two-context block

**Status: experiment fixture, recorded rather than fixed. It does NOT compile,
by design, and it is wired into no `make` target.** `make db` and `make gen` are
clean; the C++ build fails, and that failure is the finding.

**Carries a known second defect, left in place.** Its testbench External is still
at the scaffold seed `--block=xpTwoCtxTop`, so it elaborates a SECOND copy of the
DUT's children under `tb.external.*` (see `xpTwoCtxTopExternal.cppm`). The other
`xprojParam` tops were retargeted at their `_tb` container
(`--block=<X>_tb --excludeInst=u_<X>`); this one was not, because the retarget
cannot be verified while the fixture does not build. Retarget it as part of
whatever change makes this fixture compile.

## What it is

One block, `xpTwoCtxDut`, whose `params:` names one parameterizable constant
declared in an INCLUDED file (`DP_WIDTH`, from `dpLeaf/yaml/xpDpLeaf.yaml`) and
one declared in its OWN file (`TC_GAIN`), with both bound to NON-default values
in one declared variant (12 and 5 against declared defaults of 8 and 2). No such
block existed anywhere in either tree.

A second block, `xpTwoCtxBare`, is the same two-context shape with **no
parameterizable structure on its own surface** — it names both knobs and carries
a literal-width port. The two blocks reach their `configContext` by different
code paths and behave differently, which is why both are here.

## What is emitted

`xpTwoCtxDut`'s `configContext` is the INCLUDED file. Its Config carries the
included context's constants plus a synthetic for the other one:

```cpp
export struct xpTwoCtx_xpTwoCtxDutTwoctxConfig {
    static constexpr uint32_t DP_ALGO = 1;    // never named by this block
    static constexpr uint32_t DP_WIDTH = 12;  // bound value, correct
    static constexpr uint32_t TC_GAIN = 5;    // bound value, synthetic arm
};
```

`TC_GAIN_X2`, the second context's DERIVED constant, is absent — and the
generated base class names it:

```
base/xpTwoCtxDutBase.cppm:49:48: fatal error: no member named 'TC_GAIN_X2'
   in 'xpTwoCtx_xpTwoCtxDutTwoctxConfig'
   49 |     static constexpr auto TC_GAIN_X2 = Config::TC_GAIN_X2;
```

The SystemVerilog side carries BOTH contexts correctly — both module parameters
and both contexts' module-local declarations, `TC_GAIN_X2` included — so the two
languages disagree about the block's parameter set.

## Order dependence

For `xpTwoCtxBare`, which has no parameterizable own surface, the whole choice
turns on the order of the `params:` list, silently:

| `params:` | `configContext` | `defaultConfig` |
| :-- | :-- | :-- |
| `[DP_WIDTH, TC_GAIN]` | `dpLeaf/yaml/xpDpLeaf.yaml` | `xpDpLeafDefaultConfig` |
| `[TC_GAIN, DP_WIDTH]` | `twoCtx/yaml/xpTwoCtx.yaml` | `xpTwoCtxDefaultConfig` |

The Config's name, its home header and its field set all move with it. The tree
currently carries the second row.

For `xpTwoCtxDut`, which does have a parameterizable own surface, neither the
`params:` order nor the `ports:` order moves the choice: the context comes from
the surface scan instead.
