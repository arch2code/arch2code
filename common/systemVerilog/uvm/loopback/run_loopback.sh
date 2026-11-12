#!/bin/bash
# Builds a2c_uvm_loopback_tb.sv on Xcelium or VCS and runs every test the
# *_lb_tests.svh files beside it register with the factory: each
# `uvm_component_utils line naming a class whose name ends in _test, file by
# file in name order. Exits 0 only when every file registers at least one
# test and every test reaches the UVM report summary with no UVM_ERROR or
# UVM_FATAL and logs LB_PASS. A line "// LB_TESTS <test>..." in a test file
# adds tests that a macro defines, and a line
# "// LB_PLUSARGS <test> <plusarg>..." gives a test its plusargs. Then
# seedRepro.py runs each check below, and each must end with its verdict.
#
#   run_loopback.sh xcelium|vcs [seed [<layer.f>...]]
#
# Each <layer.f> lists a builder layer's agent packages and compiles after
# a2c_uvm.f. The loopback/ directory beside it holds the layer's
# *_lb_tests.svh files, whose tests also run. It also holds the *.sv files
# that include them, which compile after this testbench.
#
# The build and the logs go to ./loopback_<sim> under the current directory,
# which the script empties first. The simulator setup must already be sourced.

set -u

usage() {
    echo "usage: $0 xcelium|vcs [seed [<layer.f>...]]" >&2
    exit 2
}

[ $# -ge 1 ] || usage
SIM=$1
SEED=${2:-1}
shift $(( $# < 2 ? $# : 2 ))

HERE=$(cd "$(dirname "$0")" && pwd)
OUT=$PWD/loopback_$SIM
LAYER_F=""
LB_DIRS=$HERE
for f in "$@"; do
    dir=$(cd "$(dirname "$f")" && pwd)
    LAYER_F="$LAYER_F $dir/$(basename "$f")"
    LB_DIRS="$LB_DIRS $dir/loopback"
done
TESTS=""
declare -A PLUSARGS
for d in $LB_DIRS; do
    for f in "$d"/*_lb_tests.svh; do
        FILE_TESTS=$(sed -n 's/^[[:space:]]*`uvm_component_utils(\([A-Za-z0-9_]*_test\)).*/\1/p' "$f")
        # A test a macro defines has no `uvm_component_utils line of its own.
        FILE_TESTS="$FILE_TESTS $(sed -n 's#^[[:space:]]*// LB_TESTS \(.*\)#\1#p' "$f")"
        if [ -z "${FILE_TESTS// /}" ]; then
            echo "FAIL: no \`uvm_component_utils(*_test) line and no // LB_TESTS line in $f"
            exit 1
        fi
        TESTS="$TESTS $FILE_TESTS"
        while read -r t args; do
            PLUSARGS[$t]=$args
        done < <(sed -n 's#^[[:space:]]*// LB_PLUSARGS \([A-Za-z0-9_]*\) \(.*\)#\1 \2#p' "$f")
    done
done
# Each agent package a .f lists has its interface, <type>_if.sv, beside it.
# The paths in a .f are relative to its own directory.
SRCS=""
INCDIRS=$HERE
for list in "$HERE/../a2c_uvm.f" $LAYER_F; do
    dir=$(dirname "$list")
    for f in $(sed -n '/^a2c_uvm_pkg\.sv$/!s#_uvm_pkg\.sv$#_if.sv#p' "$list"); do
        SRCS="$SRCS $dir/$f"
    done
done
SRCS="$SRCS -F $HERE/../a2c_uvm.f"
for list in $LAYER_F; do
    SRCS="$SRCS -F $list"
done
SRCS="$SRCS $HERE/a2c_uvm_loopback_tb.sv"
for d in $LB_DIRS; do
    [ "$d" = "$HERE" ] && continue
    INCDIRS="$INCDIRS $d"
    SRCS="$SRCS $(ls "$d"/*.sv)"
done

rm -rf "$OUT"
mkdir -p "$OUT"
cd "$OUT" || exit 1

case $SIM in
    xcelium)
        # -uvmhome CDNS-1.2: without it xrun picks UVM 1.1d.
        xrun -64bit -sv -uvm -uvmhome CDNS-1.2 -timescale 1ns/1ps -incdir ${INCDIRS// / -incdir } -elaborate $SRCS \
            -top a2c_uvm_loopback_tb -l build.log > /dev/null
        BUILD=$?
        run() { xrun -64bit -R +UVM_TESTNAME=$1 -svseed $SEED "${@:2}" -l $1.log > /dev/null; }
        SEED_ARG=-svseed
        seed_cmd() { echo "xrun -64bit -R +UVM_TESTNAME=$1 -svseed $2 ${*:3}"; }
        ;;
    vcs)
        vcs -full64 -sverilog -ntb_opts uvm-1.2 -timescale=1ns/1ps +incdir+${INCDIRS// / +incdir+} $SRCS \
            -top a2c_uvm_loopback_tb -o simv -l build.log > /dev/null
        BUILD=$?
        run() { ./simv +UVM_TESTNAME=$1 +ntb_random_seed=$SEED "${@:2}" -l $1.log > /dev/null; }
        SEED_ARG=+ntb_random_seed
        seed_cmd() { echo "./simv +UVM_TESTNAME=$1 +ntb_random_seed=$2 ${*:3}"; }
        ;;
    *)
        usage
        ;;
esac

if [ $BUILD -ne 0 ]; then
    echo "FAIL: $SIM build, see $OUT/build.log"
    exit 1
fi

FAILED=0
for t in $TESTS; do
    run $t ${PLUSARGS[$t]:-}
    if grep -q "LB_PASS" $t.log && grep -Eq '^UVM_ERROR :\s+0$' $t.log && grep -Eq '^UVM_FATAL :\s+0$' $t.log; then
        echo "PASS: $t ($(grep -h -o 'LB_STATS.*' $t.log | head -1 | sed 's/^LB_STATS\] //'))"
    else
        echo "FAIL: $t, see $OUT/$t.log"
        FAILED=1
    fi
done

# check <name> <verdict> <test> [seedRepro.py option...] [-- plusarg...]: runs
# the test twice under seedRepro.py at SEED. The check passes when the
# runner's last line starts with A2C_SEED_REPRO <verdict>; a check that must
# fail names its reason, so a failure for another reason fails the check.
REPRO=$(cd "$HERE" && pwd -P)/../../../../seedRepro.py
check() {
    local name=$1 verdict=$2 test=$3 opts=() plusargs=()
    shift 3
    while [ $# -gt 0 ] && [ "$1" != -- ]; do opts+=("$1"); shift; done
    [ $# -gt 0 ] && shift
    plusargs=("$@")
    "$REPRO" --seed-arg=$SEED_ARG "${opts[@]}" -- $(seed_cmd $test $SEED "${plusargs[@]}") > $name.log 2>&1
    if tail -1 $name.log | grep -q "^A2C_SEED_REPRO $verdict"; then
        echo "PASS: $name ($(tail -1 $name.log | sed 's/^A2C_SEED_REPRO //'))"
    else
        echo "FAIL: $name, see $OUT/$name.log"
        FAILED=1
    fi
}
OTHER_SEED=$((SEED + 1))
check seed_repro_same "PASS: the digests match" txn_digest_rv_test -- +lb_digest_vary=data
check seed_repro_differ_data "PASS: the digests differ" txn_digest_rv_test --differ $OTHER_SEED -- +lb_digest_vary=data
check seed_repro_differ_timing "PASS: the digests differ" txn_digest_rv_test --differ $OTHER_SEED -- +lb_digest_vary=timing
check seed_repro_differ_none "FAIL: seed $OTHER_SEED gave the same digests" txn_digest_rv_test --differ $OTHER_SEED -- +lb_digest_vary=none
check seed_repro_unstable "FAIL: the same seed gave different digests" txn_digest_rv_test -- +lb_digest_vary=run
check seed_repro_lane_count "FAIL: run 1: port c DUT lane saw 50 items, model lane 51" txn_digest_rv_test -- +lb_digest_vary=lane
# d's comparator compares only some items, so its lanes may count apart.
check seed_repro_status_lanes "PASS: the digests match" txn_digest_rv_test -- +lb_digest_vary=status
# A cut leaves the DUT lane of d with 5 items more than its model lane.
check seed_repro_cut_lanes "PASS: the digests match" txn_digest_cut_test
# Only the rdata levels on the monitor's rdata_ap change with the seed.
check seed_repro_differ_ext_rdata "PASS: the digests differ" txn_digest_er_test --differ $OTHER_SEED
# Only the AXI read data changes with the seed.
check seed_repro_differ_axi_data "PASS: the digests differ" txn_digest_axi_test --differ $OTHER_SEED
# rdy_vld_random_test has no digest.
check seed_repro_no_digest "FAIL: run 1 printed no A2C_DIGEST line" rdy_vld_random_test
exit $FAILED
