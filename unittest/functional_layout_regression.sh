#!/usr/bin/env bash
#
# functional_layout_regression.sh — byte-identical regression gate for the
# project layout-mode work (plan-decomp-functional-layout.md, T0.1).
#
# Generation is in-place and idempotent, so the safety net for the L1
# config-normalization refactor (T1.2) is simple: capture the generated output
# of every examples/ project today (layout: functional, the only mode that
# exists pre-L1), then after L1 regenerate with layout: functional and prove
# the output is byte-for-byte identical. Any drift in the generated file set or
# its contents is a functional-mode regression.
#
# The baseline is the generation output of the working tree AS-IS, not a
# pristine committed reference: examples/ip_test is mid-migration and has no
# full saved buildable copy, but it generates deterministically, so the gate
# proves generation-equivalence, not build success.
#
# Usage:
#   functional_layout_regression.sh baseline [snapshot-root]   # capture pre-L1 output
#   functional_layout_regression.sh compare  [snapshot-root]   # regen + diff vs baseline
#   functional_layout_regression.sh check     [snapshot-root]  # regen all, report gen failures only
#
# snapshot-root defaults to $A2C_LAYOUT_SNAP or a scratchpad path.

set -u

MODE="${1:-}"
SNAP_ROOT="${2:-${A2C_LAYOUT_SNAP:-/tmp/claude-19778/-work-ws-debayer/a0380a6d-a65f-40ea-8d09-b16980a2c1bb/scratchpad/layout-snap}}"

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"   # builder/base
EXAMPLES_DIR="$BASE_DIR/examples"

# Build-output / non-source artifacts excluded from the snapshot. The gate is
# about generated *source* (arch/base/model/rtl/fw/tb/verif/registrar), not the
# build tree.
EXCLUDES=(
  --exclude='.gen'
  --exclude='build'
  --exclude='obj_dir'
  --exclude='__pycache__'
  --exclude='*.db'
  --exclude='*.log'
  --exclude='compile_commands.json'
  --exclude='.cache'
)

if [[ "$MODE" != "baseline" && "$MODE" != "compare" && "$MODE" != "check" ]]; then
  echo "usage: $0 <baseline|compare|check> [snapshot-root]" >&2
  exit 2
fi

# Examples that cannot generate today for reasons unrelated to the layout work,
# excluded from the gate with a recorded reason. pySocket has not been migrated
# to yamlFormat: 2 (projectCreate hard-stops it), so it produces no functional
# output to compare against.
declare -A SKIP=(
  [pySocket]="not migrated to yamlFormat: 2 (pre-existing; unrelated to layout)"
  [nested]="converted to hierarchical layout (T4.6 sign-off); covered by test_layout_nested.py, not the functional gate"
  [hierVlDemo]="hierarchical-layout verilator-wrapper regression guard; not functional, so excluded from the functional byte-identical gate"
)

# Discover example projects: a dir under examples/ with its own Makefile.
mapfile -t EXAMPLES < <(for d in "$EXAMPLES_DIR"/*/; do
  [[ -f "$d/Makefile" ]] && basename "$d"
done | sort)

if [[ ${#EXAMPLES[@]} -eq 0 ]]; then
  echo "no examples with a Makefile found under $EXAMPLES_DIR" >&2
  exit 2
fi

regen() {
  # Force a full regeneration so the snapshot reflects the current generator,
  # not stale timestamp-gated output. Logs go under the snapshot root, never
  # into the user's example tree.
  local dir="$1" name="$2"
  mkdir -p "$SNAP_ROOT/logs"
  ( cd "$dir" && make clean && make db && make gen ) >"$SNAP_ROOT/logs/regen_$name.log" 2>&1
}

snapshot() {
  # Copy a regenerated example tree (minus build artifacts) into dest.
  local src="$1" dest="$2"
  rm -rf "$dest"
  mkdir -p "$dest"
  tar -C "$src" "${EXCLUDES[@]}" -cf - . | tar -C "$dest" -xf -
}

DEST_SUB="baseline"
[[ "$MODE" == "compare" ]] && DEST_SUB="candidate"

fail_gen=()       # unexpected generation failures
regress_gen=()    # had a baseline but now fails to generate (compare mode)
for ex in "${EXAMPLES[@]}"; do
  exdir="$EXAMPLES_DIR/$ex"
  if [[ -n "${SKIP[$ex]:-}" ]]; then
    printf '  [skip]  %-14s ... %s\n' "$ex" "${SKIP[$ex]}"
    continue
  fi
  printf '  [regen] %-14s ... ' "$ex"
  if regen "$exdir" "$ex"; then
    echo "ok"
  else
    if [[ "$MODE" == "compare" && -d "$SNAP_ROOT/baseline/$ex" ]]; then
      echo "GEN FAILED — REGRESSION (had baseline; see $SNAP_ROOT/logs/regen_$ex.log)"
      regress_gen+=("$ex")
    else
      echo "GEN FAILED (see $SNAP_ROOT/logs/regen_$ex.log)"
      fail_gen+=("$ex")
    fi
    continue
  fi
  if [[ "$MODE" != "check" ]]; then
    snapshot "$exdir" "$SNAP_ROOT/$DEST_SUB/$ex"
  fi
done

if [[ ${#fail_gen[@]} -gt 0 ]]; then
  echo
  echo "GENERATION FAILURES: ${fail_gen[*]}"
fi

if [[ "$MODE" == "baseline" ]]; then
  echo
  echo "baseline captured under: $SNAP_ROOT/baseline"
  exit $(( ${#fail_gen[@]} > 0 ? 1 : 0 ))
fi

if [[ "$MODE" == "check" ]]; then
  exit $(( ${#fail_gen[@]} > 0 ? 1 : 0 ))
fi

# compare mode: diff candidate vs baseline per example
echo
echo "=== diff candidate vs baseline ==="
diff_fail=()
for ex in "${EXAMPLES[@]}"; do
  b="$SNAP_ROOT/baseline/$ex"
  c="$SNAP_ROOT/candidate/$ex"
  if [[ ! -d "$b" ]]; then
    echo "  [diff]  $ex ... NO BASELINE (skipped)"
    continue
  fi
  if diff -rq "$b" "$c" >"$SNAP_ROOT/diff_$ex.txt" 2>&1; then
    printf '  [diff]  %-14s ... IDENTICAL\n' "$ex"
  else
    printf '  [diff]  %-14s ... DIFF (see %s)\n' "$ex" "$SNAP_ROOT/diff_$ex.txt"
    diff_fail+=("$ex")
  fi
done

echo
if [[ ${#diff_fail[@]} -eq 0 && ${#regress_gen[@]} -eq 0 ]]; then
  echo "PASS: functional output byte-identical across all baselined examples."
  exit 0
fi
echo "FAIL: gen-regression=[${regress_gen[*]}] diff=[${diff_fail[*]}]"
exit 1
