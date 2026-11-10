#!/usr/bin/env python3
"""The pop_ack dst BFM takes every one-cycle ack, and drops pop after the ack
cycle while a delayed ack() runs, so the HDL pops each entry once.

pop_ack_if.sv's waveform holds ack for one cycle and drops pop after it. Two
things in the BFM broke that:
- It was an SC_CTHREAD that waits with wait(clk.posedge_event()). SystemC 2.3.4
  runs wait(event) in an SC_CTHREAD as wait(event) followed by wait() on the
  clock (sc_wait.cpp), so each wait took two edges and the BFM sampled every
  other edge. With no delay it missed every ack that fell on an edge it did not
  sample, pop stayed high, and the HDL popped the next entry. The BFM is now an
  SC_THREAD, like the other BFMs.
- Under --delay N, pop_ack_channel::ack first waits N ns (interfaceBase::delay),
  so ack() keeps the BFM thread away for several edges after it samples the
  HDL's ack. pop was still high on them, so the HDL popped more entries that
  the model never received. The BFM now drops pop before it calls ack(), as
  push_ack_dst_bfm and notify_ack_dst_bfm drop push / notify.

The probe drives the BFM's hdl_if signals from a SystemC thread standing in for
the RTL, which follows only the pop_ack_if.sv waveform, on a 2.5 ns clock. It
holds a queue 0x10, 0x11, ...; it starts a pop on an edge where it is idle and
pop is high, raises ack with the head entry on the next edge ('fast') or the
third ('slow'), holds it for one cycle, and is idle again from the edge that
samples it. The model pops three times through pop(). A channel subclass
records each ack() the BFM makes. Every case runs with no delay and with
setTimed(10). The HDL must pop exactly three entries, the BFM must ack each
once, and the model must get 0x10, 0x11 and 0x12.

Set A2C_PROBE_TRACE_DIR to keep a VCD and an event log for each case.
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
#include "pop_ack_bfm.h"
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <format>
#include <string>
#include <vector>

template <int W>
struct bitsSt {
    std::uint64_t w = 0;
    static constexpr std::uint16_t _bitWidth = W;
    static constexpr std::uint16_t _byteWidth = (W + 7) / 8;
    typedef std::uint64_t _packedSt;
    static const char* getValueType() { return ""; }
    std::uint64_t getStructValue() const { return w; }
    void pack( _packedSt& v ) const { v = w; }
    void unpack( const _packedSt& v ) { w = v; }
    sc_bv<W> sc_pack() const { sc_bv<W> p; p = w; return p; }
    void sc_unpack( sc_bv<W> p ) { w = p.to_uint64(); }
    std::string prt( bool = false ) const { return std::format( "0x{:x}", w ); }
    bool operator==( const bitsSt& o ) const { return w == o.w; }
};

using wordSt = bitsSt<32>;
using chanT = pop_ack_channel<wordSt>;
using hdlT = pop_ack_hdl_if<sc_bv<32>>;
using bfmT = pop_ack_dst_bfm<wordSt, sc_bv<32>>;

constexpr int POPS = 3;

static bool g_trace = false;
static void ev( const char *what, std::uint64_t v )
{
    if (g_trace) { std::printf( "EV %.3f %s %llx\\n", sc_time_stamp().to_seconds() * 1e9, what, (unsigned long long)v ); }
}

// The BFM calls the channel through its port, so a subclass sees every
// pop it takes and every ack() it makes.
struct probeChan : chanT {
    sc_signal<bool> *busy = nullptr;
    std::vector<std::uint64_t> bfmAck;
    probeChan( const char *n ) : chanT( n, "tb" ) {}
    void popReceive() override
    {
        chanT::popReceive();
        ev( "bfm_pop", 0 );
    }
    void ack( const wordSt &a ) override
    {
        ev( "bfm_ack", a.w );
        bfmAck.push_back( a.w );
        busy->write( true );
        chanT::ack( a );
        busy->write( false );
    }
};

SC_MODULE( delayedAck )
{
    sc_in<bool> clk, rst_n;
    sc_signal<bool> busy{ "bfm_ack_busy" };
    sc_signal<int> modelAcks{ "model_acks" };
    probeChan ch;
    pop_ack_out<wordSt> out;
    hdlT hdl;
    bfmT bfm;
    int latency;
    std::vector<std::uint64_t> hdlPop, received;

    SC_HAS_PROCESS( delayedAck );
    delayedAck( sc_module_name n, int latency_ ) : sc_module( n ), ch( "ch" ), out( "out" ), bfm( "bfm" ), latency( latency_ )
    {
        ch.busy = &busy;
        out( ch ); bfm.if_p( ch ); bfm.hdl_if_p( hdl ); bfm.clk( clk ); bfm.rst_n( rst_n );
        SC_THREAD( rtl ); SC_THREAD( model );
    }

    void model()
    {
        for (int i = 0; i < POPS; i++) {
            wordSt r;
            out->pop( r );
            received.push_back( r.w );
            modelAcks.write( (int)received.size() );
        }
    }

    // Values read right after an edge are the ones that edge sampled.
    void rtl()
    {
        int left = -1;                      // -1: idle; >= 0: edges left before ack
        std::uint64_t head = 0x10, data = 0;
        while (true) {
            wait( clk.posedge_event() );
            if (!rst_n) { hdl.ack = 0; left = -1; continue; }
            if (hdl.ack) {                  // the ack cycle ends here
                hdl.ack = 0;
                left = -1;
            } else if (left == -1 && hdl.pop) {
                data = head++;
                hdlPop.push_back( data );
                ev( "hdl_pop", data );
                left = latency;
            }
            if (left == 0) {
                hdl.ack = 1;
                hdl.rdata = sc_bv<32>( data );
                ev( "hdl_ack", data );
                left = -2;
            } else if (left > 0) {
                left--;
            }
        }
    }
};

SC_MODULE( probe )
{
    sc_clock clk;
    sc_signal<bool> rst_n;
    delayedAck dut;
    int delayNs;

    SC_HAS_PROCESS( probe );
    probe( sc_module_name n, int delayNs_, int latency ) :
        sc_module( n ), clk( "clk", 2500, SC_PS ), dut( "dut", latency ), delayNs( delayNs_ )
    {
        dut.clk( clk ); dut.rst_n( rst_n );
        SC_THREAD( run );
    }

    // --delay N --delayMode fixedInit reaches the channel this way.
    void start_of_simulation() override
    {
        if (delayNs > 0) { dut.ch.setTimed( delayNs, TIMED_DELAY_FIXED_INIT ); }
    }

    void run()
    {
        rst_n = 0;
        wait( 11250, SC_PS );
        rst_n = 1;
        wait( 1, SC_US );
        auto list = []( const std::vector<std::uint64_t> &v ) {
            std::string s;
            for (auto x : v) { s += std::format( "{:x},", x ); }
            return s;
        };
        std::printf( "delayed hdl_pop=%s bfm_ack=%s recv=%s\\n", list( dut.hdlPop ).c_str(),
                     list( dut.ch.bfmAck ).c_str(), list( dut.received ).c_str() );
        sc_stop();
    }
};

int sc_main( int argc, char *argv[] )
{
    logging::GetInstance().setDefaultVerbosity( VERBOSITY_MEDIUM );
    probe p( "p", std::atoi( argv[1] ), std::string( argv[2] ) == "slow" ? 3 : 1 );
    sc_trace_file *tf = nullptr;
    if (argc > 3) {
        g_trace = true;
        tf = sc_create_vcd_trace_file( argv[3] );
        tf->set_time_unit( 1, SC_PS );
        auto &h = p.dut.hdl;
        sc_trace( tf, p.clk, "clk" );
        sc_trace( tf, h.pop, "pop" );
        sc_trace( tf, h.ack, "ack" );
        sc_trace( tf, h.rdata, "rdata" );
        sc_trace( tf, p.dut.busy, "bfm_ack_busy" );
        sc_trace( tf, p.dut.modelAcks, "model_acks" );
    }
    sc_start();
    if (tf) { sc_close_vcd_trace_file( tf ); }
    std::printf( "probe done\\n" );
    return 0;
}
"""

POPS = 3
EXPECTED = [0x10 + i for i in range(POPS)]
CASES = [(rtl, delay) for rtl in ('fast', 'slow') for delay in (0, 10)]
FAILURES = []


def check(condition, message):
    print(f"  {'PASS' if condition else 'FAIL'}: {message}")
    if not condition:
        FAILURES.append(message)


def hexes(s):
    return [int(v, 16) for v in s.split(',') if v]


def runCase(binPath, rtl, delay, scLibdir, traceDir):
    tag = f"{rtl} RTL, delay {delay} ns"
    cmd = [binPath, str(delay), rtl]
    if traceDir:
        cmd.append(os.path.join(traceDir, f"pop_ack_{rtl}_d{delay}"))
    try:
        run = subprocess.run(cmd, capture_output=True, text=True, timeout=60,
                             env=dict(os.environ, LD_LIBRARY_PATH=scLibdir))
    except subprocess.TimeoutExpired:
        check(False, f"{tag}: probe finishes within 60 s")
        return
    output = run.stdout + run.stderr
    if traceDir:
        with open(os.path.join(traceDir, f"pop_ack_{rtl}_d{delay}.log"), 'w') as fh:
            fh.write(output)
    before = len(FAILURES)
    check(run.returncode == 0 and 'probe done' in output, f"{tag}: probe runs to completion (status {run.returncode})")
    m = re.search(r'^delayed hdl_pop=(\S*) bfm_ack=(\S*) recv=(\S*)$', output, re.M)
    if not m:
        check(False, f"{tag}: probe printed its record")
    else:
        hdlPop, bfmAck, received = (hexes(m.group(i)) for i in range(1, 4))
        check(hdlPop == EXPECTED, f"{tag}: the HDL popped one entry per model pop (popped {[hex(v) for v in hdlPop]})")
        check(bfmAck == EXPECTED, f"{tag}: the BFM acked each pop once ({[hex(v) for v in bfmAck]})")
        check(received == EXPECTED, f"{tag}: the model got every entry in order ({[hex(v) for v in received]})")
    if len(FAILURES) > before and not traceDir:
        print(output)


def test_pop_ack_dst_bfm_delayed_ack():
    scLibdir = os.environ.get('SYSTEMC_LIBDIR', '')
    traceDir = os.environ.get('A2C_PROBE_TRACE_DIR')
    if traceDir:
        os.makedirs(traceDir, exist_ok=True)
    tmpdir = tempfile.mkdtemp(prefix='a2c_pop_ack_dst_delayed_ack_')
    try:
        binPath = buildProbe(tmpdir, PROBE_SRC)
        if not os.path.isfile(binPath):
            check(False, f"probe must build and link: {binPath}")
            return
        for rtl, delay in CASES:
            runCase(binPath, rtl, delay, scLibdir, traceDir)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == '__main__':
    test_pop_ack_dst_bfm_delayed_ack()
    if FAILURES:
        print(f"\n  SOME TESTS FAILED ({len(FAILURES)})")
        sys.exit(1)
    print("\n  ALL TESTS PASSED!")
    sys.exit(0)
