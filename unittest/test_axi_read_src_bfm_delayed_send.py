#!/usr/bin/env python3
"""The axi_read src BFM sends every AR an HDL master hands over while the
channel's send blocks across clock edges.

Under --delay N every rdy_vld_channel write first waits N ns
(interfaceBase::delay), so sendAddr keeps the AR thread away for several edges
after it samples a transfer. A transfer happens on every edge where
ARVALID && ARREADY, so the BFM must hold arready low while it is away, as
rdy_vld_src_bfm does with rdy. With arready left high, a master that issues its
next AR straight away hands over an address the BFM never samples, and the
master waits forever for that burst's R beats.

The probe drives the BFM's hdl_if signals from a SystemC thread standing in for
the RTL master, which honours only the handshake rule, on a 2.5 ns clock. The
'seq' master issues an AR and waits for its last R beat before the next; the
'pipe' master issues both ARs back to back. The model answers each AR with four
R beats through sendDataCycle. A channel subclass records each sendAddr the BFM
makes. Every case runs with no delay and with setTimed(10). Every AR the HDL
hands over must reach the BFM's sendAddr, and the HDL must get every R beat in
order.

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
#include "axi_read_bfm.h"
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
using chanT = axi_read_channel<wordSt, wordSt>;
using hdlT = axi_read_hdl_if<sc_bv<32>, sc_bv<32>>;
using bfmT = axi_read_src_bfm<wordSt, wordSt, sc_bv<32>, sc_bv<32>>;
using arT = axiReadAddressSt<wordSt>;
using rT = axiReadRespSt<wordSt>;

constexpr int BURSTS = 2;
constexpr int LEN = 3;                     // four beats per burst

static bool g_trace = false;
static void ev( const char *what, std::uint64_t v )
{
    if (g_trace) { std::printf( "EV %.3f %s %llx\\n", sc_time_stamp().to_seconds() * 1e9, what, (unsigned long long)v ); }
}

// The BFM finds its channel with dynamic_cast<axi_read_channel *>, which a
// subclass satisfies, so the probe sees every sendAddr the BFM makes.
struct probeChan : chanT {
    sc_signal<bool> *busy = nullptr;
    std::vector<std::uint64_t> bfmAddr;
    probeChan( const char *n ) : chanT( n, "tb" ) {}
    void sendAddr( const arT &a, std::optional<std::string> s ) override
    {
        ev( "bfm_ar", a.araddr.w );
        bfmAddr.push_back( a.araddr.w );
        busy->write( true );
        chanT::sendAddr( a, s );
        busy->write( false );
    }
};

SC_MODULE( delayedSend )
{
    sc_in<bool> clk, rst_n;
    sc_signal<bool> busy{ "bfm_ar_busy" };
    probeChan ch;
    axi_read_in<wordSt, wordSt> in;
    hdlT hdl;
    bfmT bfm;
    bool pipe;
    std::vector<std::uint64_t> hdlAddr, hdlData;
    std::deque<arT> addrs;
    sc_event addrArrived;

    SC_HAS_PROCESS( delayedSend );
    delayedSend( sc_module_name n, bool pipe_ ) : sc_module( n ), ch( "ch" ), in( "in" ), bfm( "bfm" ), pipe( pipe_ )
    {
        ch.busy = &busy;
        in( ch ); bfm.if_p( ch ); bfm.hdl_if_p( hdl ); bfm.clk( clk ); bfm.rst_n( rst_n );
        SC_THREAD( master ); SC_THREAD( addrThread ); SC_THREAD( dataThread );
    }

    void addrThread()
    {
        while (true) {
            arT ar;
            in->receiveAddr( ar );
            addrs.push_back( ar );
            addrArrived.notify();
        }
    }

    // Beat i of the burst at address a carries a / 0x10 + i.
    void dataThread()
    {
        while (true) {
            while (addrs.empty()) { wait( addrArrived ); }
            arT ar = addrs.front();
            addrs.pop_front();
            for (unsigned i = 0; i < unsigned( ar.arlen ) + 1; i++) {
                rT r;
                r.rid = ar.arid;
                r.rdata.w = ar.araddr.w / 0x10 + i;
                r.rresp = AXIRESP_OKAY;
                r.rlast = i == unsigned( ar.arlen );
                in->sendDataCycle( r );
            }
        }
    }

    // Values read right after an edge are the ones that edge sampled.
    void master()
    {
        int arNext = 0, rDone = 0;
        bool arUp = false;
        hdl.rready = 1;
        while (true) {
            wait( clk.posedge_event() );
            if (!rst_n) { hdl.arvalid = 0; continue; }
            if (hdl.arvalid && hdl.arready) {
                hdlAddr.push_back( hdl.araddr.read().to_uint64() );
                ev( "hdl_ar", hdlAddr.back() );
                arUp = false;
            }
            if (hdl.rvalid && hdl.rready) {
                hdlData.push_back( hdl.rdata.read().to_uint64() );
                ev( "hdl_r", hdlData.back() );
                if (hdl.rlast) { rDone++; }
            }
            // seq: the next AR waits for the previous burst's last R beat.
            if (!arUp && arNext < BURSTS && (pipe || rDone == arNext)) {
                hdl.arvalid = 1;
                hdl.arid = arNext + 1;
                hdl.araddr = sc_bv<32>( 0x1000 * (arNext + 1) );
                hdl.arlen = LEN;
                hdl.arsize = 2;
                hdl.arburst = 1;
                arNext++;
                arUp = true;
            } else if (!arUp) {
                hdl.arvalid = 0;
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
    probe( sc_module_name n, int delayNs_, bool pipe ) :
        sc_module( n ), clk( "clk", 2500, SC_PS ), dut( "dut", pipe ), delayNs( delayNs_ )
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
        std::printf( "delayed hdl_ar=%s bfm_ar=%s hdl_r=%s\\n", list( dut.hdlAddr ).c_str(),
                     list( dut.ch.bfmAddr ).c_str(), list( dut.hdlData ).c_str() );
        sc_stop();
    }
};

int sc_main( int argc, char *argv[] )
{
    logging::GetInstance().setDefaultVerbosity( VERBOSITY_MEDIUM );
    probe p( "p", std::atoi( argv[1] ), std::string( argv[2] ) == "pipe" );
    sc_trace_file *tf = nullptr;
    if (argc > 3) {
        g_trace = true;
        tf = sc_create_vcd_trace_file( argv[3] );
        tf->set_time_unit( 1, SC_PS );
        auto &h = p.dut.hdl;
        sc_trace( tf, p.clk, "clk" );
        sc_trace( tf, h.arvalid, "arvalid" );
        sc_trace( tf, h.arready, "arready" );
        sc_trace( tf, h.araddr, "araddr" );
        sc_trace( tf, h.rvalid, "rvalid" );
        sc_trace( tf, h.rready, "rready" );
        sc_trace( tf, h.rlast, "rlast" );
        sc_trace( tf, h.rdata, "rdata" );
        sc_trace( tf, p.dut.busy, "bfm_ar_busy" );
    }
    sc_start();
    if (tf) { sc_close_vcd_trace_file( tf ); }
    std::printf( "probe done\\n" );
    return 0;
}
"""

BURSTS = 2
BEATS = 4
EXPECTED_AR = [0x1000 * (n + 1) for n in range(BURSTS)]
EXPECTED_R = [0x100 * (n + 1) + i for n in range(BURSTS) for i in range(BEATS)]
CASES = [(master, delay) for master in ('seq', 'pipe') for delay in (0, 10)]
FAILURES = []


def check(condition, message):
    print(f"  {'PASS' if condition else 'FAIL'}: {message}")
    if not condition:
        FAILURES.append(message)


def hexes(s):
    return [int(v, 16) for v in s.split(',') if v]


def runCase(binPath, master, delay, scLibdir, traceDir):
    tag = f"{master} master, delay {delay} ns"
    cmd = [binPath, str(delay), master]
    if traceDir:
        cmd.append(os.path.join(traceDir, f"ar_{master}_d{delay}"))
    try:
        run = subprocess.run(cmd, capture_output=True, text=True, timeout=60,
                             env=dict(os.environ, LD_LIBRARY_PATH=scLibdir))
    except subprocess.TimeoutExpired:
        check(False, f"{tag}: probe finishes within 60 s")
        return
    output = run.stdout + run.stderr
    if traceDir:
        with open(os.path.join(traceDir, f"ar_{master}_d{delay}.log"), 'w') as fh:
            fh.write(output)
    before = len(FAILURES)
    check(run.returncode == 0 and 'probe done' in output, f"{tag}: probe runs to completion (status {run.returncode})")
    m = re.search(r'^delayed hdl_ar=(\S*) bfm_ar=(\S*) hdl_r=(\S*)$', output, re.M)
    if not m:
        check(False, f"{tag}: probe printed its record")
    else:
        hdlAr, bfmAr, hdlR = (hexes(m.group(i)) for i in range(1, 4))
        check(hdlAr == EXPECTED_AR and bfmAr == hdlAr,
              f"{tag}: the BFM sent every AR the HDL handed over (hdl={[hex(v) for v in hdlAr]} bfm={[hex(v) for v in bfmAr]})")
        check(hdlR == EXPECTED_R, f"{tag}: the HDL got every R beat in order ({[hex(v) for v in hdlR]})")
    if len(FAILURES) > before and not traceDir:
        print(output)


def test_axi_read_src_bfm_delayed_send():
    scLibdir = os.environ.get('SYSTEMC_LIBDIR', '')
    traceDir = os.environ.get('A2C_PROBE_TRACE_DIR')
    if traceDir:
        os.makedirs(traceDir, exist_ok=True)
    tmpdir = tempfile.mkdtemp(prefix='a2c_axi_read_src_delayed_send_')
    try:
        binPath = buildProbe(tmpdir, PROBE_SRC)
        if not os.path.isfile(binPath):
            check(False, f"probe must build and link: {binPath}")
            return
        for master, delay in CASES:
            runCase(binPath, master, delay, scLibdir, traceDir)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == '__main__':
    test_axi_read_src_bfm_delayed_send()
    if FAILURES:
        print(f"\n  SOME TESTS FAILED ({len(FAILURES)})")
        sys.exit(1)
    print("\n  ALL TESTS PASSED!")
    sys.exit(0)
