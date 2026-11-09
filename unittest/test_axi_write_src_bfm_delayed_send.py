#!/usr/bin/env python3
"""The axi_write src BFM delivers every AW and W transfer an HDL master makes
while the channel's send blocks across clock edges.

Under --delay N every rdy_vld_channel write first waits N ns
(interfaceBase::delay), and when both ends of the channel are cycle based
writeClocked writes every beat. sendAddr and sendDataCycle end in that write,
so the BFM thread is away for several edges after it samples a transfer. A
transfer happens on every edge where VALID && READY, so the BFM must hold
awready / wready low while it is away, as rdy_vld_src_bfm does with rdy.
With ready left high the HDL hands over AWs and W beats the BFM never samples,
and the model waits forever for the rest of the burst.

The probe drives the BFM's hdl_if signals from a SystemC thread standing in for
the RTL master, which honours only the handshake rule, on a 2.5 ns clock. The
'seq' master sends an AW, the burst's four W beats from the cycle the AW
handshakes, and waits for B; the 'pipe' master sends both AWs back to back and
the W bursts in AW order without waiting for B. The model reads the channel as
a cycle-based reader on one thread ('ext'), as a Tandem port_tee does with its
address and data on two threads ('tee'), or transactionally ('txn'). A channel
subclass records what the BFM passes to sendAddr / sendDataCycle. Every case
runs with no delay and with setTimed(10). Every AW and W beat the HDL hands over
must reach the BFM's send in order, the model must receive every beat, and each
burst must get its B.
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
using bfmT = axi_write_src_bfm<wordSt, wordSt, strbSt, sc_bv<32>, sc_bv<32>, sc_bv<4>>;
using awT = axiWriteAddressSt<wordSt>;
using wT = axiWriteDataSt<wordSt, strbSt>;

constexpr int BURSTS = 2;
constexpr int LEN = 3;                     // four beats per burst

// The BFM finds its channel with dynamic_cast<axi_write_channel *>, which a
// subclass satisfies, so the probe sees every send the BFM makes.
struct probeChan : chanT {
    std::vector<std::uint64_t> bfmAddr, bfmData;
    probeChan( const char *n ) : chanT( n, "tb", "api_list_size", 256, "" ) {}
    void sendAddr( const awT &a, std::optional<std::string> s ) override
    {
        bfmAddr.push_back( a.awaddr.w );
        chanT::sendAddr( a, s );
    }
    void sendDataCycle( const wT &d ) override
    {
        bfmData.push_back( d.wdata.w );
        chanT::sendDataCycle( d );
    }
};

SC_MODULE( delayedSend )
{
    sc_in<bool> clk, rst_n;
    probeChan ch;
    axi_write_in<wordSt, wordSt, strbSt> in;
    hdlT hdl;
    bfmT bfm;
    std::string mode;
    bool pipe;
    int hdlB = 0;
    std::vector<std::uint64_t> hdlAddr, hdlData, received;
    std::deque<awT> addrs;
    sc_event addrArrived;

    SC_HAS_PROCESS( delayedSend );
    delayedSend( sc_module_name n, std::string mode_, bool pipe_ ) :
        sc_module( n ), ch( "ch" ), in( "in" ), bfm( "bfm" ), mode( mode_ ), pipe( pipe_ )
    {
        in( ch ); bfm.if_p( ch ); bfm.hdl_if_p( hdl ); bfm.clk( clk ); bfm.rst_n( rst_n );
        SC_THREAD( master );
        if (mode == "ext") {
            SC_THREAD( extThread );
        } else {
            SC_THREAD( addrThread );
            if (mode == "tee") { SC_THREAD( teeDataThread ); } else { SC_THREAD( txnDataThread ); }
        }
    }

    void sendB( int id )
    {
        axiWriteRespSt<> b;
        b.bid = id;
        b.bresp = AXIRESP_OKAY;
        if (mode == "txn") { in->sendResp( b ); } else { in->sendRespCycle( b ); }
    }

    // A cycle-based model: the address, then awlen + 1 beats, then B.
    void extThread()
    {
        in->setCycleTransaction( PORTTYPE_IN );
        while (true) {
            awT aw;
            in->receiveAddr( aw );
            for (unsigned i = 0; i < unsigned( aw.awlen ) + 1; i++) {
                wT beat;
                in->receiveDataCycle( beat );
                received.push_back( beat.wdata.w );
            }
            sendB( aw.awid );
        }
    }

    void addrThread()
    {
        while (true) {
            awT aw;
            in->receiveAddr( aw );
            addrs.push_back( aw );
            addrArrived.notify();
        }
    }

    // As a Tandem port_tee: cycle data read apart from the address.
    void teeDataThread()
    {
        in->setCycleTransaction( PORTTYPE_IN );
        while (true) {
            wT beat;
            in->receiveDataCycle( beat );
            received.push_back( beat.wdata.w );
            if (beat.wlast) {
                while (addrs.empty()) { wait( addrArrived ); }
                int id = addrs.front().awid;
                addrs.pop_front();
                sendB( id );
            }
        }
    }

    void txnDataThread()
    {
        while (true) {
            wT first;
            in->receiveData( first );
            auto *beats = reinterpret_cast<wT *>( in->getReceiveDataPtr() );
            for (unsigned i = 0; i < in->getReceiveBeatCount(); i++) { received.push_back( beats[i].wdata.w ); }
            while (addrs.empty()) { wait( addrArrived ); }
            int id = addrs.front().awid;
            addrs.pop_front();
            sendB( id );
        }
    }

    void presentAw( int burst )
    {
        hdl.awvalid = 1;
        hdl.awid = 1;
        hdl.awaddr = sc_bv<32>( 0x1000 * (burst + 1) );
        hdl.awlen = LEN;
        hdl.awsize = 2;
        hdl.awburst = 1;
    }

    void presentW( int burst, int beat )
    {
        hdl.wvalid = 1;
        hdl.wid = 1;
        hdl.wdata = sc_bv<32>( 0x100 * (burst + 1) + beat );
        hdl.wstrb = sc_bv<4>( 0xf );
        hdl.wlast = beat == LEN;
    }

    // Values read right after an edge are the ones that edge sampled.
    void master()
    {
        int awNext = 0, awDone = 0, wBurst = 0, beat = 0, bDone = 0;
        bool awUp = false, wUp = false;
        hdl.bready = 1;
        while (true) {
            wait( clk.posedge_event() );
            if (!rst_n) { hdl.awvalid = 0; hdl.wvalid = 0; hdl.wlast = 0; continue; }
            bool awHs = hdl.awvalid && hdl.awready;
            bool wHs = hdl.wvalid && hdl.wready;
            if (awHs) { hdlAddr.push_back( hdl.awaddr.read().to_uint64() ); awDone++; awUp = false; }
            if (wHs) { hdlData.push_back( hdl.wdata.read().to_uint64() ); }
            if (hdl.bvalid && hdl.bready) { hdlB++; bDone++; }
            // seq: the next AW waits for the previous burst's B.
            if (!awUp && awNext < BURSTS && (pipe || bDone == awNext)) { presentAw( awNext++ ); awUp = true; }
            else if (!awUp) { hdl.awvalid = 0; }
            if (wHs) {
                if (++beat > LEN) { wBurst++; beat = 0; wUp = false; }
                else { presentW( wBurst, beat ); }
            }
            if (!wUp) {
                if (wBurst < awDone) { presentW( wBurst, 0 ); wUp = true; } else { hdl.wvalid = 0; hdl.wlast = 0; }
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
    probe( sc_module_name n, int delayNs_, std::string mode, bool pipe ) :
        sc_module( n ), clk( "clk", 2500, SC_PS ), dut( "dut", mode, pipe ), delayNs( delayNs_ )
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
        std::printf( "delayed hdl_aw=%s bfm_aw=%s hdl_w=%s bfm_w=%s recv=%s b=%d\\n",
                     list( dut.hdlAddr ).c_str(), list( dut.ch.bfmAddr ).c_str(), list( dut.hdlData ).c_str(),
                     list( dut.ch.bfmData ).c_str(), list( dut.received ).c_str(), dut.hdlB );
        sc_stop();
    }
};

int sc_main( int argc, char *argv[] )
{
    logging::GetInstance().setDefaultVerbosity( VERBOSITY_MEDIUM );
    probe p( "p", std::atoi( argv[1] ), argv[2], std::string( argv[3] ) == "pipe" );
    sc_start();
    std::printf( "probe done\\n" );
    return 0;
}
"""

BURSTS = 2
BEATS = 4
EXPECTED_AW = [0x1000 * (n + 1) for n in range(BURSTS)]
EXPECTED_W = [0x100 * (n + 1) + i for n in range(BURSTS) for i in range(BEATS)]
CASES = [(master, mode, delay) for master in ('seq', 'pipe') for mode in ('ext', 'tee', 'txn') for delay in (0, 10)]
FAILURES = []


def check(condition, message):
    print(f"  {'PASS' if condition else 'FAIL'}: {message}")
    if not condition:
        FAILURES.append(message)


def hexes(s):
    return [int(v, 16) for v in s.split(',') if v]


def runCase(binPath, master, mode, delay, scLibdir):
    tag = f"{master} master, {mode} model, delay {delay} ns"
    try:
        run = subprocess.run([binPath, str(delay), mode, master], capture_output=True, text=True, timeout=60,
                             env=dict(os.environ, LD_LIBRARY_PATH=scLibdir))
    except subprocess.TimeoutExpired:
        check(False, f"{tag}: probe finishes within 60 s")
        return
    output = run.stdout + run.stderr
    before = len(FAILURES)
    check(run.returncode == 0 and 'probe done' in output, f"{tag}: probe runs to completion (status {run.returncode})")
    m = re.search(r'^delayed hdl_aw=(\S*) bfm_aw=(\S*) hdl_w=(\S*) bfm_w=(\S*) recv=(\S*) b=(\d+)$', output, re.M)
    if not m:
        check(False, f"{tag}: probe printed its record")
    else:
        hdlAw, bfmAw, hdlW, bfmW, received = (hexes(m.group(i)) for i in range(1, 6))
        b = int(m.group(6))
        check(hdlAw == EXPECTED_AW and bfmAw == hdlAw,
              f"{tag}: the BFM sent every AW the HDL handed over (hdl={[hex(v) for v in hdlAw]} bfm={[hex(v) for v in bfmAw]})")
        check(hdlW == EXPECTED_W and bfmW == hdlW,
              f"{tag}: the BFM sent every W beat the HDL handed over (hdl={len(hdlW)} bfm={[hex(v) for v in bfmW]})")
        check(received == EXPECTED_W, f"{tag}: the model received every beat in order ({len(received)} beats)")
        check(b == BURSTS, f"{tag}: every burst got its B (b={b})")
    if len(FAILURES) > before:
        print(output)


def test_axi_write_src_bfm_delayed_send():
    scLibdir = os.environ.get('SYSTEMC_LIBDIR', '')
    tmpdir = tempfile.mkdtemp(prefix='a2c_axi_write_delayed_send_')
    try:
        binPath = buildProbe(tmpdir, PROBE_SRC)
        if not os.path.isfile(binPath):
            check(False, f"probe must build and link: {binPath}")
            return
        for master, mode, delay in CASES:
            runCase(binPath, master, mode, delay, scLibdir)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == '__main__':
    test_axi_write_src_bfm_delayed_send()
    if FAILURES:
        print(f"\n  SOME TESTS FAILED ({len(FAILURES)})")
        sys.exit(1)
    print("\n  ALL TESTS PASSED!")
    sys.exit(0)
