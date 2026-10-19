#!/bin/bash
# Builds a2c_uvm_loopback_tb.sv on Xcelium or VCS and runs every test the
# *_lb_tests.svh files beside it register with the factory: each
# `uvm_component_utils line naming a class whose name ends in _test, file by
# file in name order. Exits 0 only when every file registers at least one
# test and every test reaches the UVM report summary with no UVM_ERROR or
# UVM_FATAL and logs LB_PASS.
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
for d in $LB_DIRS; do
    for f in "$d"/*_lb_tests.svh; do
        FILE_TESTS=$(sed -n 's/^[[:space:]]*`uvm_component_utils(\([A-Za-z0-9_]*_test\)).*/\1/p' "$f")
        if [ -z "$FILE_TESTS" ]; then
            echo "FAIL: no \`uvm_component_utils(*_test) line in $f"
            exit 1
        fi
        TESTS="$TESTS $FILE_TESTS"
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
        run() { xrun -64bit -R +UVM_TESTNAME=$1 -svseed $SEED -l $1.log > /dev/null; }
        ;;
    vcs)
        vcs -full64 -sverilog -ntb_opts uvm-1.2 -timescale=1ns/1ps +incdir+${INCDIRS// / +incdir+} $SRCS \
            -top a2c_uvm_loopback_tb -o simv -l build.log > /dev/null
        BUILD=$?
        run() { ./simv +UVM_TESTNAME=$1 +ntb_random_seed=$SEED -l $1.log > /dev/null; }
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
    run $t
    if grep -q "LB_PASS" $t.log && grep -Eq '^UVM_ERROR :\s+0$' $t.log && grep -Eq '^UVM_FATAL :\s+0$' $t.log; then
        echo "PASS: $t ($(grep -h -o 'LB_STATS.*' $t.log | head -1 | sed 's/^LB_STATS\] //'))"
    else
        echo "FAIL: $t, see $OUT/$t.log"
        FAILED=1
    fi
done
exit $FAILED
