#!/usr/bin/env python3
"""The memory BFMs return the right read word and count the accesses they skip.

memory_dst_bfm drives a model's memory requests onto the pins of a memory the
HDL holds. The memory registers read_data on the access edge, so the word
arrives after that edge: in later delta cycles from Verilated RTL or a vendor
simulator, 100 ps later from a UVM memory agent. The BFM must read it after
both and before the next access edge, and hand it to the model at the
following rising edge, so the model's next pin writes land after a posedge and
not at the negedge where a UVM monitor samples. The probe's stub memory
answers either way. Four writes and four reads go out back to back; every read
must return the word written to its address, the writes must take consecutive
clock edges and each later read a second edge, and every read must resume the
model in a rising edge's timestep.

memory_src_bfm serves one HDL access per enabled rising edge by calling the
model's request(). A request() that takes simulated time lets enabled edges
pass that the BFM never serves. The stub HDL presents a read on every edge,
each at its own address. The model answers at once, after 15 ns, or after one
clock in the delta in which that edge fires. In that delta the Accellera kernel
runs the edge monitor, a method, before the BFM thread, so the monitor counts
the edge and the thread's same-delta branch finds it counted. The probe does
not force the other order, in which only that branch would count the edge. The
BFM must count exactly the presented accesses the model never saw, log the
first with its time and the total at the end, and
set the exit code only under bfmContractCheck::failOnBreak.
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
#include "bfmContractCheck.h"
#include "memory_bfm.h"
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <format>
#include <map>
#include <set>
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
    std::string prt( bool = false ) const { return std::format( "0x{:x}", w ); }
    bool operator==( const wordSt& o ) const { return w == o.w; }
};

using hdlIf = memory_hdl_if<sc_bv<64>, sc_bv<64>>;

// A model requester in front of memory_dst_bfm, and a stub HDL memory behind
// it that registers read_data on the access edge, in the next delta (rtl) or
// 100 ps later (uvm).
SC_MODULE( dstProbe )
{
    sc_in<bool> clk, rst_n;
    memory_channel<wordSt, wordSt> ch;
    memory_out<wordSt, wordSt> out;
    hdlIf hdl;
    memory_dst_bfm<wordSt, wordSt, sc_bv<64>, sc_bv<64>> bfm;
    bool uvmTiming;
    std::map<std::uint64_t, std::uint64_t> mem;
    std::vector<std::uint64_t> accessNs;
    std::string reads;
    bool done = false;
    bool resumesOnPosedge = true;

    SC_HAS_PROCESS( dstProbe );
    dstProbe( sc_module_name n, bool uvmTiming_ )
      : sc_module( n ), ch( "ch", "tb" ), out( "out" ), bfm( "bfm" ), uvmTiming( uvmTiming_ )
    {
        out( ch ); bfm.if_p( ch ); bfm.hdl_if_p( hdl ); bfm.clk( clk ); bfm.rst_n( rst_n );
        SC_THREAD( requester ); SC_THREAD( memory );
    }
    void requester()
    {
        wait( 32, SC_NS );
        for (std::uint64_t i = 0; i < 4; i++) {
            wordSt a, d;
            a.w = i;
            d.w = 0x100 + i;
            out->request( true, a, d );
        }
        for (std::uint64_t i : { 2, 0, 3, 1 }) {
            wordSt a, d;
            a.w = i;
            out->request( false, a, d );
            if (sc_time_stamp() % sc_time( 10, SC_NS ) != SC_ZERO_TIME || !clk.read()) { resumesOnPosedge = false; }
            reads += std::format( "{}0x{:x}", reads.empty() ? "" : ",", d.w );
        }
        done = true;
    }
    void memory()
    {
        while (true) {
            wait( clk.posedge_event() );
            if (!hdl.enable.read()) { continue; }
            accessNs.push_back( (std::uint64_t)(sc_time_stamp() / sc_time( 1, SC_NS )) );
            std::uint64_t addr = hdl.addr.read().to_uint64();
            if (hdl.wr_en.read()) {
                mem[addr] = hdl.write_data.read().to_uint64();
                continue;
            }
            std::uint64_t word = mem[addr];
            if (uvmTiming) { wait( 100, SC_PS ); }
            hdl.read_data = sc_bv<64>( word );
        }
    }
};

// Stub HDL in front of memory_src_bfm presenting a read at address k on edge
// k, and a model memory behind it that answers after delayNs; at 10 ns it
// answers in the delta of the next edge's posedge event.
SC_MODULE( srcProbe )
{
    sc_in<bool> clk, rst_n;
    memory_channel<wordSt, wordSt> ch;
    memory_in<wordSt, wordSt> in;
    hdlIf hdl;
    memory_src_bfm<wordSt, wordSt, sc_bv<64>, sc_bv<64>> bfm;
    int delayNs;
    std::vector<std::uint64_t> presented;
    std::map<std::uint64_t, sc_time> presentedAt;
    std::set<std::uint64_t> served;

    SC_HAS_PROCESS( srcProbe );
    srcProbe( sc_module_name n, int delayNs_ )
      : sc_module( n ), ch( "ch", "tb" ), in( "in" ), bfm( "bfm" ), delayNs( delayNs_ )
    {
        in( ch ); bfm.if_p( ch ); bfm.hdl_if_p( hdl ); bfm.clk( clk ); bfm.rst_n( rst_n );
        SC_THREAD( responder ); SC_THREAD( hdlThread );
    }
    void responder()
    {
        while (true) {
            bool isWrite;
            wordSt a, d;
            in->reqReceive( isWrite, a, d );
            served.insert( a.w );
            if (delayNs) { wait( delayNs, SC_NS ); }
            // One delta later is the delta the edge's posedge event fires in.
            if (delayNs == 10) { wait( SC_ZERO_TIME ); }
            d.w = a.w * 3;
            in->complete( d );
        }
    }
    void hdlThread()
    {
        std::uint64_t edge = 0;
        while (true) {
            wait( clk.posedge_event() );
            if (hdl.enable.read()) {
                std::uint64_t addr = hdl.addr.read().to_uint64();
                presented.push_back( addr );
                presentedAt[addr] = sc_time_stamp();
            }
            if (!rst_n.read()) { continue; }
            edge++;
            hdl.enable = edge <= 30;
            hdl.wr_en = false;
            hdl.addr = sc_bv<64>( edge );
        }
    }
};

int sc_main( int argc, char *argv[] )
{
    logging::GetInstance().setDefaultVerbosity( VERBOSITY_MEDIUM );
    std::string scenario = argv[1];
    sc_clock clk( "clk", 10, SC_NS );
    sc_signal<bool> rst_n( "rst_n", false );
    struct releaser : sc_module {
        sc_out<bool> rst_n;
        SC_HAS_PROCESS( releaser );
        releaser( sc_module_name n ) : sc_module( n ), rst_n( "rst_n" ) { SC_THREAD( run ); }
        void run() { wait( 25, SC_NS ); rst_n = true; }
    } rel( "rel" );
    rel.rst_n( rst_n );
    if (scenario == "dst_rtl" || scenario == "dst_uvm") {
        dstProbe p( "p", scenario == "dst_uvm" );
        p.clk( clk ); p.rst_n( rst_n );
        sc_start( 1, SC_US );
        std::string edges, gaps;
        for (std::size_t i = 0; i < p.accessNs.size(); i++) {
            edges += std::format( "{}{}", i ? "," : "", p.accessNs[i] );
            if (i) { gaps += std::format( "{}{}", i > 1 ? "," : "", p.accessNs[i] - p.accessNs[i - 1] ); }
        }
        std::printf( "done=%d\\nreads=%s\\nedges=%s\\ngaps=%s\\nresumes_on_posedge=%d\\n", p.done, p.reads.c_str(),
                     edges.c_str(), gaps.c_str(), p.resumesOnPosedge );
    } else {
        bfmContractCheck::failOnBreak = scenario == "src_fail";
        int delayNs = scenario == "src_fast" ? 0 : scenario == "src_edge" ? 10 : 15;
        srcProbe p( "p", delayNs );
        p.clk( clk ); p.rst_n( rst_n );
        sc_start( 1, SC_US );
        std::size_t skipped = 0;
        std::string first = "none";
        for (std::uint64_t addr : p.presented) {
            if (!p.served.count( addr )) {
                if (skipped++ == 0) { first = p.presentedAt[addr].to_string(); }
            }
        }
        std::printf( "presented=%zu\\nskipped=%zu\\nfirst=%s\\n", p.presented.size(), skipped, first.c_str() );
        sc_stop();
    }
    std::printf( "exit=%d\\n", errorCode::getExitCode() );
    return 0;
}
"""

FAILURES = []
SKIPPED = 'HDL made a memory access while SystemC was still serving the previous one, so the BFM did not take it'


def check(condition, message):
    print(f"  {'PASS' if condition else 'FAIL'}: {message}")
    if not condition:
        FAILURES.append(message)


def field(output, name):
    match = re.search(rf'^{name}=(.*)$', output, re.M)
    return match.group(1) if match else None


def bfmLines(output):
    return [line for line in output.splitlines() if line.startswith('p.bfm:')]


def runScenario(binPath, scenario):
    run = subprocess.run([binPath, scenario], capture_output=True, text=True, timeout=60,
                         env=dict(os.environ, LD_LIBRARY_PATH=os.environ.get('SYSTEMC_LIBDIR', '')))
    output = run.stdout + run.stderr
    check(run.returncode == 0 and field(output, 'exit') is not None,
          f"{scenario} probe runs to completion (status {run.returncode})")
    return output


def test_memory_bfms():
    tmpdir = tempfile.mkdtemp(prefix='a2c_memory_bfms_')
    try:
        binPath = buildProbe(tmpdir, PROBE_SRC)
        if not os.path.isfile(binPath):
            check(False, f"memory BFM probe must build and link: {binPath}")
            return
        before = len(FAILURES)
        outputs = dict()

        for scenario in ('dst_rtl', 'dst_uvm'):
            outputs[scenario] = output = runScenario(binPath, scenario)
            check(field(output, 'done') == '1', f"{scenario}: the requester finishes")
            check(field(output, 'reads') == '0x102,0x100,0x103,0x101',
                  f"{scenario}: each read returns the word written to its address (reads={field(output, 'reads')})")
            check(field(output, 'gaps') == '10,10,10,10,20,20,20',
                  f"{scenario}: the writes take consecutive edges and each later read a second edge "
                  f"(edges={field(output, 'edges')})")
            check(field(output, 'resumes_on_posedge') == '1',
                  f"{scenario}: every read resumes the model in a rising edge's timestep")

        outputs['src_fast'] = output = runScenario(binPath, 'src_fast')
        check(field(output, 'presented') == '30' and field(output, 'skipped') == '0',
              f"src_fast serves all 30 accesses (presented={field(output, 'presented')}, "
              f"skipped={field(output, 'skipped')})")
        check(bfmLines(output) == [], f"src_fast logs nothing (got {bfmLines(output)})")

        for scenario in ('src_slow', 'src_edge', 'src_fail'):
            outputs[scenario] = output = runScenario(binPath, scenario)
            skipped = field(output, 'skipped')
            check(skipped not in (None, '0'), f"{scenario}: the model's delay skips accesses (skipped={skipped})")
            check(bfmLines(output) == [f"p.bfm:{SKIPPED} at {field(output, 'first')}",
                                       f"p.bfm:{SKIPPED}, {skipped} accesses in total"],
                  f"{scenario}: the BFM logs the first skipped access at {field(output, 'first')} and "
                  f"{skipped} in total (got {bfmLines(output)})")
            fails = scenario == 'src_fail'
            check((field(output, 'exit') != '-1') == fails,
                  f"{scenario}: the exit code is {'set' if fails else 'unset'} (exit={field(output, 'exit')})")

        if len(FAILURES) > before:
            for scenario, output in outputs.items():
                print(f"--- {scenario}\n{output}")
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == '__main__':
    test_memory_bfms()
    if FAILURES:
        print(f"\n  SOME TESTS FAILED ({len(FAILURES)})")
        sys.exit(1)
    print("\n  ALL TESTS PASSED!")
    sys.exit(0)
