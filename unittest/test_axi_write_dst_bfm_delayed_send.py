#!/usr/bin/env python3
"""The axi_write dst BFM sends every B response an HDL slave hands over while
the channel's send blocks across clock edges.

Under --delay N every rdy_vld_channel write first waits N ns
(interfaceBase::delay), so sendRespCycle keeps the B thread away for several
edges after it samples a response. A transfer happens on every edge where
BVALID && BREADY, so the BFM must hold bready low while it is away, as
rdy_vld_src_bfm does with rdy. With bready left high, a slave that returns its
responses back to back hands over a B the BFM never samples, and the model
waits forever for that burst's response.

The probe drives the BFM's hdl_if signals from a SystemC thread standing in for
the RTL slave, which honours only the handshake rule, on a 2.5 ns clock. It
accepts every AW and W beat, and returns each burst's B as soon as the burst's
last beat is in ('each'), or holds the responses until both bursts are in and
then returns them back to back ('batch'), as a slave that posts writes may. The
model sends two four-beat bursts without waiting for B and reads B through
receiveResp. A channel subclass records each sendRespCycle the BFM makes.
Every case runs with no delay and with setTimed(10). Every B the HDL hands
over must reach the BFM's sendRespCycle, and the model must receive every B
in order.

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
#include "axi_write_bfm.h"
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <deque>
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
using strbSt = bitsSt<4>;
using chanT = axi_write_channel<wordSt, wordSt, strbSt>;
using hdlT = axi_write_hdl_if<sc_bv<32>, sc_bv<32>, sc_bv<4>>;
using bfmT = axi_write_dst_bfm<wordSt, wordSt, strbSt, sc_bv<32>, sc_bv<32>, sc_bv<4>>;
using awT = axiWriteAddressSt<wordSt>;
using wT = axiWriteDataSt<wordSt, strbSt>;
using bT = axiWriteRespSt<>;

constexpr int BURSTS = 2;
constexpr int LEN = 3;                     // four beats per burst

static bool g_trace = false;
static void ev( const char *what, std::uint64_t v )
{
    if (g_trace) { std::printf( "EV %.3f %s %llx\\n", sc_time_stamp().to_seconds() * 1e9, what, (unsigned long long)v ); }
}

// The BFM finds its channel with dynamic_cast<axi_write_channel *>, which a
// subclass satisfies, so the probe sees every sendRespCycle the BFM makes.
struct probeChan : chanT {
    sc_signal<bool> *busy = nullptr;
    std::vector<std::uint64_t> bfmB;
    probeChan( const char *n ) : chanT( n, "tb" ) {}
    void sendRespCycle( const bT &b ) override
    {
        ev( "bfm_b", b.bid );
        bfmB.push_back( b.bid );
        busy->write( true );
        chanT::sendRespCycle( b );
        busy->write( false );
    }
};

SC_MODULE( delayedSend )
{
    sc_in<bool> clk, rst_n;
    sc_signal<bool> busy{ "bfm_b_busy" };
    sc_signal<int> modelB{ "model_b_count" };
    probeChan ch;
    axi_write_out<wordSt, wordSt, strbSt> out;
    hdlT hdl;
    bfmT bfm;
    bool batch;
    std::vector<std::uint64_t> hdlB, received;

    SC_HAS_PROCESS( delayedSend );
    delayedSend( sc_module_name n, bool batch_ ) : sc_module( n ), ch( "ch" ), out( "out" ), bfm( "bfm" ), batch( batch_ )
    {
        ch.busy = &busy;
        out( ch ); bfm.if_p( ch ); bfm.hdl_if_p( hdl ); bfm.clk( clk ); bfm.rst_n( rst_n );
        SC_THREAD( slave ); SC_THREAD( addrThread ); SC_THREAD( dataThread ); SC_THREAD( respThread );
    }

    // Burst n is at 0x1000 * (n + 1) with ID n + 1; beat i carries 0x100 * (n + 1) + i.
    void addrThread()
    {
        for (int n = 0; n < BURSTS; n++) {
            awT aw;
            aw.awid = n + 1;
            aw.awaddr.w = 0x1000 * (n + 1);
            aw.awlen = LEN;
            aw.awsize = 2;
            aw.awburst = AXIBURST_INCR;
            out->sendAddr( aw );
        }
    }

    void dataThread()
    {
        for (int n = 0; n < BURSTS; n++) {
            for (int i = 0; i <= LEN; i++) {
                wT w;
                w.wid = n + 1;
                w.wdata.w = 0x100 * (n + 1) + i;
                w.wstrb.w = 0xf;
                w.wlast = i == LEN;
                out->sendDataCycle( w );
            }
        }
    }

    void respThread()
    {
        while (true) {
            bT b;
            out->receiveResp( b );
            received.push_back( b.bid );
            modelB.write( (int)received.size() );
        }
    }

    // Values read right after an edge are the ones that edge sampled.
    void slave()
    {
        std::deque<int> ids, resps;
        int written = 0;
        bool bUp = false;
        while (true) {
            wait( clk.posedge_event() );
            if (!rst_n) { hdl.awready = 0; hdl.wready = 0; hdl.bvalid = 0; continue; }
            hdl.awready = 1;
            hdl.wready = 1;
            if (hdl.awvalid && hdl.awready) {
                ids.push_back( (int)hdl.awid.read().to_uint() );
                ev( "hdl_aw", hdl.awaddr.read().to_uint64() );
            }
            if (hdl.wvalid && hdl.wready) {
                ev( "hdl_w", hdl.wdata.read().to_uint64() );
                if (hdl.wlast) { resps.push_back( (int)hdl.wid.read().to_uint() ); written++; }
            }
            if (hdl.bvalid && hdl.bready) {
                hdlB.push_back( hdl.bid.read().to_uint() );
                ev( "hdl_b", hdlB.back() );
                bUp = false;
            }
            if (!bUp && !resps.empty() && (!batch || written == BURSTS)) {
                hdl.bvalid = 1;
                hdl.bid = resps.front();
                hdl.bresp = 0;
                resps.pop_front();
                bUp = true;
            } else if (!bUp) {
                hdl.bvalid = 0;
            }
        }
    }
};

SC_MODULE( probe )
{
    sc_clock clk;
    sc_signal<bool> rst_n;
    delayedSend dut;
    int delayNs;

    SC_HAS_PROCESS( probe );
    probe( sc_module_name n, int delayNs_, bool batch ) :
        sc_module( n ), clk( "clk", 2500, SC_PS ), dut( "dut", batch ), delayNs( delayNs_ )
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
        std::printf( "delayed hdl_b=%s bfm_b=%s recv=%s\\n", list( dut.hdlB ).c_str(),
                     list( dut.ch.bfmB ).c_str(), list( dut.received ).c_str() );
        sc_stop();
    }
};

int sc_main( int argc, char *argv[] )
{
    logging::GetInstance().setDefaultVerbosity( VERBOSITY_MEDIUM );
    probe p( "p", std::atoi( argv[1] ), std::string( argv[2] ) == "batch" );
    sc_trace_file *tf = nullptr;
    if (argc > 3) {
        g_trace = true;
        tf = sc_create_vcd_trace_file( argv[3] );
        tf->set_time_unit( 1, SC_PS );
        auto &h = p.dut.hdl;
        sc_trace( tf, p.clk, "clk" );
        sc_trace( tf, h.awvalid, "awvalid" );
        sc_trace( tf, h.awready, "awready" );
        sc_trace( tf, h.wvalid, "wvalid" );
        sc_trace( tf, h.wready, "wready" );
        sc_trace( tf, h.wlast, "wlast" );
        sc_trace( tf, h.wdata, "wdata" );
        sc_trace( tf, h.bvalid, "bvalid" );
        sc_trace( tf, h.bready, "bready" );
        sc_trace( tf, h.bid, "bid" );
        sc_trace( tf, p.dut.busy, "bfm_b_busy" );
        sc_trace( tf, p.dut.modelB, "model_b_count" );
    }
    sc_start();
    if (tf) { sc_close_vcd_trace_file( tf ); }
    std::printf( "probe done\\n" );
    return 0;
}
"""

BURSTS = 2
EXPECTED_B = [n + 1 for n in range(BURSTS)]
CASES = [(slave, delay) for slave in ('each', 'batch') for delay in (0, 10)]
FAILURES = []


def check(condition, message):
    print(f"  {'PASS' if condition else 'FAIL'}: {message}")
    if not condition:
        FAILURES.append(message)


def hexes(s):
    return [int(v, 16) for v in s.split(',') if v]


def runCase(binPath, slave, delay, scLibdir, traceDir):
    tag = f"{slave} slave, delay {delay} ns"
    cmd = [binPath, str(delay), slave]
    if traceDir:
        cmd.append(os.path.join(traceDir, f"b_{slave}_d{delay}"))
    try:
        run = subprocess.run(cmd, capture_output=True, text=True, timeout=60,
                             env=dict(os.environ, LD_LIBRARY_PATH=scLibdir))
    except subprocess.TimeoutExpired:
        check(False, f"{tag}: probe finishes within 60 s")
        return
    output = run.stdout + run.stderr
    if traceDir:
        with open(os.path.join(traceDir, f"b_{slave}_d{delay}.log"), 'w') as fh:
            fh.write(output)
    before = len(FAILURES)
    check(run.returncode == 0 and 'probe done' in output, f"{tag}: probe runs to completion (status {run.returncode})")
    m = re.search(r'^delayed hdl_b=(\S*) bfm_b=(\S*) recv=(\S*)$', output, re.M)
    if not m:
        check(False, f"{tag}: probe printed its record")
    else:
        hdlB, bfmB, received = (hexes(m.group(i)) for i in range(1, 4))
        check(hdlB == EXPECTED_B and bfmB == hdlB,
              f"{tag}: the BFM sent every B the HDL handed over (hdl bid={hdlB} bfm bid={bfmB})")
        check(received == EXPECTED_B, f"{tag}: the model received every B in order (bid={received})")
    if len(FAILURES) > before and not traceDir:
        print(output)


def test_axi_write_dst_bfm_delayed_send():
    scLibdir = os.environ.get('SYSTEMC_LIBDIR', '')
    traceDir = os.environ.get('A2C_PROBE_TRACE_DIR')
    if traceDir:
        os.makedirs(traceDir, exist_ok=True)
    tmpdir = tempfile.mkdtemp(prefix='a2c_axi_write_dst_delayed_send_')
    try:
        binPath = buildProbe(tmpdir, PROBE_SRC)
        if not os.path.isfile(binPath):
            check(False, f"probe must build and link: {binPath}")
            return
        for slave, delay in CASES:
            runCase(binPath, slave, delay, scLibdir, traceDir)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == '__main__':
    test_axi_write_dst_bfm_delayed_send()
    if FAILURES:
        print(f"\n  SOME TESTS FAILED ({len(FAILURES)})")
        sys.exit(1)
    print("\n  ALL TESTS PASSED!")
    sys.exit(0)
