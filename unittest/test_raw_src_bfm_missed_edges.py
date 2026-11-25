#!/usr/bin/env python3
"""The raw src BFM warns when SystemC does not take a word per clock.

raw has no handshake, so the HDL presents a new word on every clock edge and
the BFM writes each one into a blocking channel. An edge that passes while
that write still blocks is a word the BFM never samples. The probe drives the
BFM's data pin with an edge counter from a SystemC thread standing in for the
RTL, runs one reader per scenario, and expects:

- a reader that reads without pause takes the word of every edge after its
  first read and logs nothing;
- a reader that starts at 65 ns, idle until then, logs nothing, because edges
  before the first read do not count;
- a reader that pauses 15 ns after each word loses every third word, from the
  40 ns edge to the 520 ns edge, 17 in all: the BFM warns at the first and
  reports the total at end of simulation.

A miss is a warning, so no scenario sets the exit code.
"""

import os
import re
import shutil
import subprocess
import sys
import tempfile

from test_watchdog_no_terminator import buildProbe

PROBE_SRC = """
#include "systemc.h"
#include "logging.h"
#include "raw_bfm.h"
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <format>
#include <string>
#include <vector>

struct wordSt {
    std::uint64_t w = 0;
    static constexpr std::uint16_t _bitWidth = 64;
    static constexpr std::uint16_t _byteWidth = 8;
    typedef std::uint64_t _packedSt;
    static const char* getValueType() { return ""; }
    std::uint64_t getStructValue() const { return w; }
    void pack( _packedSt& v ) const { v = w; }
    void unpack( const _packedSt& v ) { w = v; }
    sc_bv<64> sc_pack() const { sc_bv<64> p; p = w; return p; }
    void sc_unpack( sc_bv<64> p ) { w = p.to_uint64(); }
    std::string prt( bool = false ) const { return std::format( "0x{:016x}", w ); }
    bool operator==( const wordSt& o ) const { return w == o.w; }
};

constexpr int READS = 8;

SC_MODULE( rawSrc )
{
    sc_in<bool> clk, rst_n;
    raw_channel<wordSt> ch;
    raw_in<wordSt> in;
    raw_hdl_if<sc_bv<64>> hdl;
    raw_src_bfm<wordSt, sc_bv<64>> bfm;
    int startNs, gapNs;
    std::vector<std::uint64_t> received;

    SC_HAS_PROCESS( rawSrc );
    rawSrc( sc_module_name n, int startNs_, int gapNs_ )
      : sc_module( n ), ch( "ch", "tb" ), in( "in" ), bfm( "bfm" ), startNs( startNs_ ), gapNs( gapNs_ )
    {
        in( ch ); bfm.if_p( ch ); bfm.hdl_if_p( hdl ); bfm.clk( clk ); bfm.rst_n( rst_n );
        SC_THREAD( reader ); SC_THREAD( hdlThread );
    }
    void reader()
    {
        wait( startNs, SC_NS );
        while (true) {
            wordSt w;
            in->read( w );
            received.push_back( w.w );
            if (gapNs) { wait( gapNs, SC_NS ); }
        }
    }
    // The pin carries the number of edges seen, like a register that counts
    // clocks, so the value a BFM samples names the edge it was sampled on.
    void hdlThread()
    {
        std::uint64_t edges = 0;
        while (true) {
            wait( clk.posedge_event() );
            wordSt v;
            v.w = ++edges;
            hdl.data = v.sc_pack();
        }
    }
};

SC_MODULE( probe )
{
    sc_clock clk;
    sc_signal<bool> rst_n;
    rawSrc src;

    SC_HAS_PROCESS( probe );
    probe( sc_module_name n, const char *scenario, int startNs, int gapNs )
      : sc_module( n ), clk( "clk", 10, SC_NS ), src( scenario, startNs, gapNs )
    {
        src.clk( clk ); src.rst_n( rst_n );
        SC_THREAD( run );
    }
    void run()
    {
        rst_n = 0;
        wait( 25, SC_NS );
        rst_n = 1;
        wait( 500, SC_NS );
        std::string recv;
        for (int i = 0; i < READS && i < (int)src.received.size(); i++) {
            recv += std::format( "{}{}", i ? "," : "", src.received[i] );
        }
        std::printf( "recv=%s\\n", recv.c_str() );
        sc_stop();
    }
};

int sc_main( int argc, char *argv[] )
{
    logging::GetInstance().setDefaultVerbosity( VERBOSITY_MEDIUM );
    const char *scenario = argv[1];
    int startNs = 25, gapNs = 0;
    if (std::strcmp( scenario, "late" ) == 0) { startNs = 65; }
    if (std::strcmp( scenario, "slow" ) == 0) { gapNs = 15; }
    probe p( "p", scenario, startNs, gapNs );
    sc_start();
    std::printf( "exit=%d\\n", errorCode::getExitCode() );
    return 0;
}
"""

FAILURES = []
MISSED = 'SystemC had not taken the previous raw word at a clock edge, so the word on that edge was lost'


def check(condition, message):
    print(f"  {'PASS' if condition else 'FAIL'}: {message}")
    if not condition:
        FAILURES.append(message)


def bfmLines(output, scenario):
    return [line for line in output.splitlines() if line.startswith(f'p.{scenario}.bfm:')]


def field(output, name):
    match = re.search(rf'^{name}=(.*)$', output, re.M)
    return match.group(1) if match else None


def runScenario(binPath, scenario):
    run = subprocess.run([binPath, scenario], capture_output=True, text=True, timeout=60,
                         env=dict(os.environ, LD_LIBRARY_PATH=os.environ.get('SYSTEMC_LIBDIR', '')))
    output = run.stdout + run.stderr
    check(run.returncode == 0 and field(output, 'exit') is not None,
          f"{scenario} probe runs to completion (status {run.returncode})")
    return output


def test_raw_src_bfm_missed_edges():
    tmpdir = tempfile.mkdtemp(prefix='a2c_raw_src_bfm_')
    try:
        binPath = buildProbe(tmpdir, PROBE_SRC)
        if not os.path.isfile(binPath):
            check(False, f"raw BFM probe must build and link: {binPath}")
            return
        before = len(FAILURES)
        outputs = dict()

        # The first read takes the word sampled at the 0 ns edge, before the
        # counter's first write. The next sample is the 30 ns edge, whose word
        # the 20 ns edge wrote.
        outputs['keep'] = output = runScenario(binPath, 'keep')
        check(field(output, 'recv') == '0,3,4,5,6,7,8,9',
              f"keep takes one word per edge after its first read (recv={field(output, 'recv')})")
        check(bfmLines(output, 'keep') == [], f"keep logs nothing (got {bfmLines(output, 'keep')})")
        check(field(output, 'exit') == '-1', f"keep leaves the exit code unset (exit={field(output, 'exit')})")

        outputs['late'] = output = runScenario(binPath, 'late')
        check(bfmLines(output, 'late') == [],
              f"late logs nothing for the edges before its first read (got {bfmLines(output, 'late')})")
        check(field(output, 'recv') == '0,7,8,9,10,11,12,13',
              f"late takes one word per edge after its first read (recv={field(output, 'recv')})")
        check(field(output, 'exit') == '-1', f"late leaves the exit code unset (exit={field(output, 'exit')})")

        outputs['slow'] = output = runScenario(binPath, 'slow')
        check(field(output, 'recv') == '0,3,5,6,8,9,11,12',
              f"slow loses every third word from the 40 ns edge (recv={field(output, 'recv')})")
        check(bfmLines(output, 'slow') == [f'p.slow.bfm:{MISSED} at 40 ns',
                                           f'p.slow.bfm:{MISSED}, 17 clock edges in total'],
              f"slow warns at the 40 ns edge and reports 17 missed edges (got {bfmLines(output, 'slow')})")
        check(field(output, 'exit') == '-1', f"slow warns without setting the exit code (exit={field(output, 'exit')})")

        if len(FAILURES) > before:
            for scenario, output in outputs.items():
                print(f"--- {scenario}\n{output}")
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == '__main__':
    test_raw_src_bfm_missed_edges()
    if FAILURES:
        print(f"\n  SOME TESTS FAILED ({len(FAILURES)})")
        sys.exit(1)
    print("\n  ALL TESTS PASSED!")
    sys.exit(0)
