#!/bin/bash
# Builds a2c_uvm_loopback_tb.sv on Xcelium or VCS and runs every loopback
# test in it. Exits 0 only when every test reaches the UVM report summary with
# no UVM_ERROR or UVM_FATAL and logs LB_PASS.
#
#   run_loopback.sh xcelium|vcs [seed]
#
# The build and the logs go to ./loopback_<sim> under the current directory,
# which the script empties first. The simulator setup must already be sourced.

set -u

usage() {
    echo "usage: $0 xcelium|vcs [seed]" >&2
    exit 2
}

[ $# -ge 1 ] && [ $# -le 2 ] || usage
SIM=$1
SEED=${2:-1}

HERE=$(cd "$(dirname "$0")" && pwd)
BASE=$(cd "$HERE/../../../.." && pwd)
OUT=$PWD/loopback_$SIM
TESTS="rdy_vld_random_test rdy_vld_burst_test axi4_stream_test raw_test status_test
       no_backpressure_test monitor_checks_test"
# a2c_uvm.f lists every agent package, so every interface they name is compiled.
SRCS="$BASE/interfaces/rdy_vld/rdy_vld_if.sv $BASE/interfaces/apb/apb_if.sv
      $BASE/interfaces/axi4_stream/axi4_stream_if.sv $BASE/interfaces/raw/raw_if.sv
      $BASE/interfaces/status/status_if.sv -F $HERE/../a2c_uvm.f $HERE/a2c_uvm_loopback_tb.sv"

rm -rf "$OUT"
mkdir -p "$OUT"
cd "$OUT" || exit 1

case $SIM in
    xcelium)
        # -uvmhome CDNS-1.2: without it xrun picks UVM 1.1d.
        xrun -64bit -sv -uvm -uvmhome CDNS-1.2 -timescale 1ns/1ps -elaborate $SRCS \
            -top a2c_uvm_loopback_tb -l build.log > /dev/null
        BUILD=$?
        run() { xrun -64bit -R +UVM_TESTNAME=$1 -svseed $SEED -l $1.log > /dev/null; }
        ;;
    vcs)
        vcs -full64 -sverilog -ntb_opts uvm-1.2 -timescale=1ns/1ps $SRCS \
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
