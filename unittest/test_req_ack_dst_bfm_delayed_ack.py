#!/usr/bin/env python3
"""The req_ack dst BFM drops req after the ack cycle while a delayed ack()
runs, so the HDL serves each request once.

Under --delay N req_ack_channel::ack first waits N ns (interfaceBase::delay),
so ack() keeps the BFM thread away for several edges after it samples the
HDL's ack. req_ack_if.sv's waveform drops req after the ack cycle, so an HDL
that sees req still high on the next edge takes it as a new request and serves
the same operation again. The BFM must drop req before it calls ack(), as
push_ack_dst_bfm and notify_ack_dst_bfm drop push / notify.

The probe drives the BFM's hdl_if signals from a SystemC thread standing in for
the RTL, which follows only the req_ack_if.sv waveform, on a 2.5 ns clock. It
starts an operation on an edge where it is idle and req is high, raises ack on
the next edge ('fast') or the third ('slow') with rdata = data + 0x1000, holds
it for one cycle, and is idle again from the edge that samples it. The model makes
three requests through req(). A channel subclass records each ack() the BFM
makes. Every case runs with no delay and with setTimed(10). The HDL must start
exactly the model's requests, the BFM must ack each once, and the model must
get each request's own rdata.

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
#include "req_ack_bfm.h"
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
using chanT = req_ack_channel<wordSt, wordSt>;
using hdlT = req_ack_hdl_if<sc_bv<32>, sc_bv<32>>;
using bfmT = req_ack_dst_bfm<wordSt, wordSt, sc_bv<32>, sc_bv<32>>;

constexpr int REQUESTS = 3;

static bool g_trace = false;
static void ev( const char *what, std::uint64_t v )
{
    if (g_trace) { std::printf( "EV %.3f %s %llx\\n", sc_time_stamp().to_seconds() * 1e9, what, (unsigned long long)v ); }
}

// The BFM calls the channel through its port, so a subclass sees every
// request it takes and every ack() it makes.
struct probeChan : chanT {
    sc_signal<bool> *busy = nullptr;
    std::vector<std::uint64_t> bfmAck;
    probeChan( const char *n ) : chanT( n, "tb" ) {}
    void reqReceive( wordSt &d ) override
    {
        chanT::reqReceive( d );
        ev( "bfm_req", d.w );
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
    req_ack_out<wordSt, wordSt> out;
    hdlT hdl;
    bfmT bfm;
    int latency;
    std::vector<std::uint64_t> hdlReq, received;

    SC_HAS_PROCESS( delayedAck );
    delayedAck( sc_module_name n, int latency_ ) : sc_module( n ), ch( "ch" ), out( "out" ), bfm( "bfm" ), latency( latency_ )
    {
        ch.busy = &busy;
        out( ch ); bfm.if_p( ch ); bfm.hdl_if_p( hdl ); bfm.clk( clk ); bfm.rst_n( rst_n );
        SC_THREAD( rtl ); SC_THREAD( model );
    }

    // Request i carries 0xa0 + i.
    void model()
    {
        for (int i = 0; i < REQUESTS; i++) {
            wordSt d, r;
            d.w = 0xa0 + i;
            out->req( d, r );
            received.push_back( r.w );
            modelAcks.write( (int)received.size() );
        }
    }

    // Values read right after an edge are the ones that edge sampled.
    void rtl()
    {
        int left = -1;                      // -1: idle; >= 0: edges left before ack
        std::uint64_t data = 0;
        while (true) {
            wait( clk.posedge_event() );
            if (!rst_n) { hdl.ack = 0; left = -1; continue; }
            if (hdl.ack) {                  // the ack cycle ends here
                hdl.ack = 0;
                left = -1;
            } else if (left == -1 && hdl.req) {
                data = hdl.data.read().to_uint64();
                hdlReq.push_back( data );
                ev( "hdl_req", data );
                left = latency;
            }
            if (left == 0) {
                hdl.ack = 1;
                hdl.rdata = sc_bv<32>( data + 0x1000 );
                ev( "hdl_ack", data + 0x1000 );
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
        std::printf( "delayed hdl_req=%s bfm_ack=%s recv=%s\\n", list( dut.hdlReq ).c_str(),
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
        sc_trace( tf, h.req, "req" );
        sc_trace( tf, h.data, "data" );
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

REQUESTS = 3
EXPECTED_REQ = [0xa0 + i for i in range(REQUESTS)]
EXPECTED_ACK = [v + 0x1000 for v in EXPECTED_REQ]
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
        cmd.append(os.path.join(traceDir, f"req_ack_{rtl}_d{delay}"))
    try:
        run = subprocess.run(cmd, capture_output=True, text=True, timeout=60,
                             env=dict(os.environ, LD_LIBRARY_PATH=scLibdir))
    except subprocess.TimeoutExpired:
        check(False, f"{tag}: probe finishes within 60 s")
        return
    output = run.stdout + run.stderr
    if traceDir:
        with open(os.path.join(traceDir, f"req_ack_{rtl}_d{delay}.log"), 'w') as fh:
            fh.write(output)
    before = len(FAILURES)
    check(run.returncode == 0 and 'probe done' in output, f"{tag}: probe runs to completion (status {run.returncode})")
    m = re.search(r'^delayed hdl_req=(\S*) bfm_ack=(\S*) recv=(\S*)$', output, re.M)
    if not m:
        check(False, f"{tag}: probe printed its record")
    else:
        hdlReq, bfmAck, received = (hexes(m.group(i)) for i in range(1, 4))
        check(hdlReq == EXPECTED_REQ,
              f"{tag}: the HDL started each request once (started {[hex(v) for v in hdlReq]})")
        check(bfmAck == EXPECTED_ACK, f"{tag}: the BFM acked each request once ({[hex(v) for v in bfmAck]})")
        check(received == EXPECTED_ACK, f"{tag}: the model got each request's rdata ({[hex(v) for v in received]})")
    if len(FAILURES) > before and not traceDir:
        print(output)


def test_req_ack_dst_bfm_delayed_ack():
    scLibdir = os.environ.get('SYSTEMC_LIBDIR', '')
    traceDir = os.environ.get('A2C_PROBE_TRACE_DIR')
    if traceDir:
        os.makedirs(traceDir, exist_ok=True)
    tmpdir = tempfile.mkdtemp(prefix='a2c_req_ack_dst_delayed_ack_')
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
    test_req_ack_dst_bfm_delayed_ack()
    if FAILURES:
        print(f"\n  SOME TESTS FAILED ({len(FAILURES)})")
        sys.exit(1)
    print("\n  ALL TESTS PASSED!")
    sys.exit(0)
