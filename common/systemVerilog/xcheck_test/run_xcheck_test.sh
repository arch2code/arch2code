#!/bin/bash
# Builds xcheck_tb.sv with the <type>_xcheck module of each type in TYPES on
# Xcelium or VCS and runs it. xz_count.c replaces the a2c_xz_fail of
# common/systemc and counts each checker's reports, and every case compares
# its count and first signal with what it expects. Exits 0 only when every
# case logs XC_PASS.
#
#   run_xcheck_test.sh xcelium|vcs [<tb.sv> <source>...]
#
# Given a testbench file, the script builds it instead, with the same
# harness. The sources that follow it compile first. The top module is the
# testbench file's stem. A builder layer tests its own checkers this way.
#
# The build and the log go to ./xcheck_<sim> under the current directory,
# which the script empties first. The simulator setup must already be sourced.
# Verilator is two-state, so it cannot run these cases.

set -u

usage() {
    echo "usage: $0 xcelium|vcs [<tb.sv> <source>...]" >&2
    exit 2
}

[ $# -ge 1 ] || usage
SIM=$1
shift

HERE=$(cd "$(dirname "$0")" && pwd)
BASE=$(cd "$HERE/../../.." && pwd)
OUT=$PWD/xcheck_$SIM
SRCS=""
if [ $# -eq 0 ]; then
    TYPES="rdy_vld apb axi4_stream raw status push_ack notify_ack req_ack pop_ack memory external_reg axi_read axi_write"
    for t in $TYPES; do
        SRCS="$SRCS $BASE/interfaces/$t/${t}_if.sv $BASE/interfaces/$t/${t}_xcheck.sv"
    done
    TB=$HERE/xcheck_tb.sv
else
    TB=$(cd "$(dirname "$1")" && pwd)/$(basename "$1")
    shift
    for f in "$@"; do
        SRCS="$SRCS $(cd "$(dirname "$f")" && pwd)/$(basename "$f")"
    done
fi
TOP=$(basename "$TB" .sv)
SRCS="$SRCS $TB $HERE/xz_count.c"
INCDIRS="+incdir+$BASE/common/systemVerilog +incdir+$HERE"

rm -rf "$OUT"
mkdir -p "$OUT"
cd "$OUT" || exit 1

case $SIM in
    xcelium)
        xrun -64bit -sv -timescale 1ns/1ps $INCDIRS $SRCS -top $TOP -l run.log > /dev/null
        STATUS=$?
        ;;
    vcs)
        # +vcs+lic+wait queues for a runtime licence instead of exiting.
        vcs +vcs+lic+wait -full64 -sverilog -timescale=1ns/1ps $INCDIRS $SRCS -top $TOP -o simv \
            -l build.log > /dev/null && ./simv +vcs+lic+wait -l run.log > /dev/null
        STATUS=$?
        ;;
    *)
        usage
        ;;
esac

if [ $STATUS -ne 0 ] || [ ! -f run.log ]; then
    echo "FAIL: $SIM build or run exited with $STATUS, see $OUT"
    exit 1
fi

CASES=$(grep -h -o 'XC_CASES [0-9]*' run.log | awk '{print $2}')
PASSED=$(grep -c '^XC_PASS' run.log)
FAILED=$(grep -c '^XC_FAIL' run.log)
grep -h '^XC_FAIL' run.log
if [ -z "$CASES" ] || [ "$FAILED" -ne 0 ] || [ "$PASSED" -ne "$CASES" ]; then
    echo "FAIL: $SIM $PASSED of ${CASES:-?} cases passed, $FAILED failed, see $OUT/run.log"
    exit 1
fi
echo "PASS: $SIM all $CASES cases"
exit 0
