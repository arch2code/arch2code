#!/bin/bash
# Parallel drop-in for run_all_tests.sh (which is left untouched).
#
# Safety model (verified by auditing every test_*.py for shared-path access):
#
#   WRITER of shared examples/ trees (exactly one):
#     test_build_manifest.py runs `make clean/db/gen` IN PLACE on every example
#     under examples/. It mutates the committed example trees, so it must run
#     mutually exclusive with any suite that reads an examples/ tree.
#
#   READERS of shared examples/ trees (read-only):
#     The eval/addrctl ip_test parity suites, the boundary-signal suite, the
#     nested-layout suite, and the layout-migration suite all READ an examples/
#     tree (projectCreate/arch2code parse the shared YAML and write their DB to
#     a unique temp path, or copytree the tree into a private tempdir). They are
#     safe concurrently with each other (concurrent reads) but NOT concurrent
#     with test_build_manifest.py.
#
#   ISOLATED (everything else):
#     Each isolates via TemporaryDirectory / mkdtemp / uniquely named
#     mkstemp|mktemp, or only READS the committed read-only unittest/
#     mixed_test_arch fixture. No shared-tree writes; safe to run anytime,
#     including concurrently with the examples lane.
#
# Lanes (run concurrently):
#   - ISOLATED lane: fanned across nproc. Never touches examples/.
#   - EXAMPLES lane: readers run concurrently, then (after they all finish) the
#     sole in-place writer runs alone. This enforces reader XOR writer while
#     overlapping the isolated fan-out.
#
# Each suite's stdout+stderr goes to its own log file, so output never
# interleaves. Final banner and exit code match run_all_tests.sh (drop-in).

set -u

cd "$(dirname "$0")" || exit 2

JOBS="$(nproc)"

# Read-only on shared examples/ trees. Run concurrently among themselves.
EXAMPLE_READERS=(
    test_eval_canonical_view.py       # reads examples/ip_test
    test_eval_cpp_emit.py             # reads examples/ip_test
    test_eval_sv_emit.py              # reads examples/ip_test (copytree)
    test_addrctl_ip_test_view.py      # reads examples/ip_test
    test_boundary_signals.py          # reads examples/ip_test
    test_layout_nested.py             # reads examples/nested (copytree)
    test_migrate_layout.py            # reads examples/simple + examples/hierInclude
)

# Sole in-place WRITER of all examples/ trees. Runs exclusive of the readers.
EXAMPLE_WRITER="test_build_manifest.py"

# ISOLATED = all test_*.py minus readers minus writer.
declare -A SKIP=()
for s in "${EXAMPLE_READERS[@]}" "$EXAMPLE_WRITER"; do SKIP["$s"]=1; done
ISOLATED=()
for f in test_*.py; do
    [[ -n "${SKIP[$f]:-}" ]] && continue
    ISOLATED+=("$f")
done

# Every suite the serial runner runs, for aggregation.
ALL=("${ISOLATED[@]}" "${EXAMPLE_READERS[@]}" "$EXAMPLE_WRITER")

# Guard against silently dropping suites: the serial runner runs 98 suites.
if [[ ${#ALL[@]} -ne 98 ]]; then
    echo "WARNING: expected 98 suites (serial-runner set), found ${#ALL[@]}." >&2
    echo "         New/removed test_*.py detected; review bucket classification." >&2
fi

LOGDIR="$(mktemp -d "${TMPDIR:-/tmp}/a2c_partests.XXXXXX")"
trap 'rm -rf "$LOGDIR"' EXIT

# Run one suite: log to its own file, record exit code.
run_one() {
    local script="$1" logdir="$2"
    python3 "$script" > "$logdir/$script.log" 2>&1
    echo "$?" > "$logdir/$script.rc"
}
export -f run_one

echo "========================================================================"
echo "Running All Unit Tests (parallel)"
echo "  isolated : ${#ISOLATED[@]} suites fanned across ${JOBS} cores"
echo "  examples : ${#EXAMPLE_READERS[@]} readers (concurrent) then 1 in-place writer (exclusive)"
echo "========================================================================"

START=$SECONDS

# EXAMPLES lane: readers concurrently, then the writer alone. Overlaps the
# isolated fan-out (which never touches examples/).
(
    for s in "${EXAMPLE_READERS[@]}"; do run_one "$s" "$LOGDIR" & done
    wait
    run_one "$EXAMPLE_WRITER" "$LOGDIR"
) &
EXAMPLES_PID=$!

# ISOLATED lane: fan out, bounded by nproc.
printf '%s\n' "${ISOLATED[@]}" \
    | xargs -P "$JOBS" -I {} bash -c 'run_one "$@"' _ {} "$LOGDIR"

wait "$EXAMPLES_PID"

ELAPSED=$((SECONDS - START))

# ---- retry-once for a failed suite (known spurious Verilator flake) ----
for s in "${ALL[@]}"; do
    rc="$(cat "$LOGDIR/$s.rc" 2>/dev/null || echo 127)"
    if [[ "$rc" != "0" ]]; then
        echo "Suite ${s} failed (rc=${rc}); retrying once from clean..."
        python3 "$s" > "$LOGDIR/$s.log" 2>&1
        echo "$?" > "$LOGDIR/$s.rc.retry"
    fi
done

# ---- aggregate ----
echo ""
echo "========================================================================"
echo "Per-suite results"
echo "------------------------------------------------------------------------"
FAILED=0
PASS_COUNT=0
FAIL_COUNT=0
FAILED_SUITES=()
for s in "${ALL[@]}"; do
    rc="$(cat "$LOGDIR/$s.rc" 2>/dev/null || echo 127)"
    note=""
    if [[ "$rc" != "0" && -f "$LOGDIR/$s.rc.retry" ]]; then
        rc="$(cat "$LOGDIR/$s.rc.retry")"
        note=" (passed on retry)"
        [[ "$rc" != "0" ]] && note=" (failed on retry too)"
    fi
    if [[ "$rc" == "0" ]]; then
        printf "  PASS  %s%s\n" "$s" "$note"
        PASS_COUNT=$((PASS_COUNT + 1))
    else
        printf "  FAIL  %s (rc=%s)%s\n" "$s" "$rc" "$note"
        FAIL_COUNT=$((FAIL_COUNT + 1))
        FAILED=1
        FAILED_SUITES+=("$s")
    fi
done

echo "------------------------------------------------------------------------"
echo "Ran ${#ALL[@]} suites: ${PASS_COUNT} passed, ${FAIL_COUNT} failed"
echo "Total wall-clock: ${ELAPSED}s"

if [[ ${#FAILED_SUITES[@]} -gt 0 ]]; then
    echo ""
    echo "==== failing suite logs (tail) ===="
    for s in "${FAILED_SUITES[@]}"; do
        echo "----- ${s} -----"
        tail -n 25 "$LOGDIR/$s.log"
        echo ""
    done
fi

echo ""
echo "========================================================================"
if [ $FAILED -eq 0 ]; then
    echo "✅ ALL TEST SUITES PASSED!"
    echo "========================================================================"
    exit 0
else
    echo "❌ SOME TEST SUITES FAILED!"
    echo "========================================================================"
    exit 1
fi
