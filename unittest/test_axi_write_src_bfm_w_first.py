#!/usr/bin/env python3
"""The axi_write src BFM delivers every W beat of an HDL master that sends W
before AW to a transactional SystemC receiver.

AXI lets a master put a burst's W beats on the bus before its AW. A
transactional receiver needs the AW first, so the channel's sendDataCycle
waits for the address when a new burst starts with none queued. The BFM must
hold wready low for as long as that wait would last. With wready high, the
HDL goes on handing over beats that the blocked BFM thread never samples.

The probe drives the BFM's hdl_if signals from a SystemC thread standing in
for the RTL master. The master presents each burst's W beats first and its AW
two clocks after the burst's first W beat, never waiting on wready. The model
reads W bursts and AWs on two threads, so it waits in receiveData before the
AW arrives, which is what holds the data channel ready. The data thread
pairs each burst with the next AW and answers B. Every beat the HDL hands
over must reach the model, in order, and every burst must get its B.
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

constexpr int BURSTS = 3;
constexpr int LEN = 3;                     // four beats per burst
constexpr int IDS[BURSTS] = { 1, 2, 1 };
constexpr int AW_LAG = 2;                  // clocks from a burst's first W beat to its AW

SC_MODULE( wFirst )
{
    sc_in<bool> clk, rst_n;
    chanT ch;
    axi_write_in<wordSt, wordSt, strbSt> in;
    hdlT hdl;
    bfmT bfm;
    int hdlBeats = 0;
    int bResps = 0;
    std::vector<std::uint64_t> received;
    std::deque<axiWriteAddressSt<wordSt>> addrs;
    sc_event addrArrived;

    SC_HAS_PROCESS( wFirst );
    wFirst( sc_module_name n ) : sc_module( n ), ch( "ch", "tb", "api_list_size", 256, "" ), in( "in" ), bfm( "bfm" )
    {
        in( ch ); bfm.if_p( ch ); bfm.hdl_if_p( hdl ); bfm.clk( clk ); bfm.rst_n( rst_n );
        SC_THREAD( addrThread ); SC_THREAD( dataThread ); SC_THREAD( master );
    }

    void addrThread()
    {
        while (true) {
            axiWriteAddressSt<wordSt> a;
            in->receiveAddr( a );
            addrs.push_back( a );
            addrArrived.notify();
        }
    }

    void dataThread()
    {
        while (true) {
            axiWriteDataSt<wordSt, strbSt> first;
            in->receiveData( first );
            auto *beats = reinterpret_cast<axiWriteDataSt<wordSt, strbSt> *>( in->getReceiveDataPtr() );
            for (unsigned i = 0; i < in->getReceiveBeatCount(); i++) { received.push_back( beats[i].wdata.w ); }
            while (addrs.empty()) { wait( addrArrived ); }
            axiWriteRespSt<> b;
            b.bid = addrs.front().awid;
            addrs.pop_front();
            b.bresp = AXIRESP_OKAY;
            in->sendResp( b );
        }
    }

    // Beat i of burst n carries 16 * n + i. W runs ahead of AW: a burst's
    // AW goes up AW_LAG clocks after its first W beat, whatever wready does.
    void master()
    {
        int wBurst = 0, wBeat = 0, awBurst = 0, presented = -1, clocks = 0;
        int wStart[BURSTS] = {};
        hdl.bready = 1;
        while (true) {
            wait( clk.posedge_event() );
            if (!rst_n) { hdl.awvalid = 0; hdl.wvalid = 0; continue; }
            clocks++;
            if (hdl.awvalid && hdl.awready) { awBurst++; }
            if (hdl.wvalid && hdl.wready) {
                hdlBeats++;
                if (++wBeat > LEN) { wBeat = 0; wBurst++; }
            }
            if (hdl.bvalid && hdl.bready) { bResps++; }
            hdl.wvalid = wBurst < BURSTS;
            if (wBurst < BURSTS) {
                if (wBurst > presented) { presented = wBurst; wStart[wBurst] = clocks; }
                hdl.wid = IDS[wBurst];
                hdl.wdata = sc_bv<32>( 16 * wBurst + wBeat );
                hdl.wstrb = sc_bv<4>( 0xf );
                hdl.wlast = wBeat == LEN;
            }
            hdl.awvalid = awBurst < BURSTS && awBurst <= presented && clocks - wStart[awBurst] >= AW_LAG;
            if (awBurst < BURSTS) {
                hdl.awid = IDS[awBurst];
                hdl.awaddr = sc_bv<32>( 0x100 * awBurst );
                hdl.awlen = LEN;
                hdl.awsize = 2;
                hdl.awburst = 1;
            }
        }
    }
};

SC_MODULE( probe )
{
    sc_clock clk;
    sc_signal<bool> rst_n;
    wFirst dut;

    SC_HAS_PROCESS( probe );
    probe( sc_module_name n ) : sc_module( n ), clk( "clk", 10, SC_NS ), dut( "dut" )
    {
        dut.clk( clk ); dut.rst_n( rst_n );
        SC_THREAD( run );
    }

    void run()
    {
        rst_n = 0;
        wait( 25, SC_NS );
        rst_n = 1;
        wait( 2, SC_US );
        std::string recv;
        for (auto v : dut.received) { recv += std::format( "{},", v ); }
        std::printf( "wfirst hdl=%d resps=%d recv=%s\\n", dut.hdlBeats, dut.bResps, recv.c_str() );
        sc_stop();
    }
};

int sc_main( int, char *[] )
{
    logging::GetInstance().setDefaultVerbosity( VERBOSITY_MEDIUM );
    probe p( "p" );
    sc_start();
    std::printf( "probe done\\n" );
    return 0;
}
"""

BURSTS = 3
BEATS = 4
EXPECTED = [16 * n + i for n in range(BURSTS) for i in range(BEATS)]
FAILURES = []


def check(condition, message):
    print(f"  {'PASS' if condition else 'FAIL'}: {message}")
    if not condition:
        FAILURES.append(message)


def test_axi_write_src_bfm_w_first():
    scLibdir = os.environ.get('SYSTEMC_LIBDIR', '')
    tmpdir = tempfile.mkdtemp(prefix='a2c_axi_write_w_first_')
    try:
        binPath = buildProbe(tmpdir, PROBE_SRC)
        if not os.path.isfile(binPath):
            check(False, f"probe must build and link: {binPath}")
            return
        try:
            run = subprocess.run([binPath], capture_output=True, text=True, timeout=60,
                                 env=dict(os.environ, LD_LIBRARY_PATH=scLibdir))
        except subprocess.TimeoutExpired:
            check(False, "probe finishes within 60 s")
            return
        output = run.stdout + run.stderr
        before = len(FAILURES)
        check(run.returncode == 0 and 'probe done' in output, f"probe runs to completion (status {run.returncode})")
        m = re.search(r'^wfirst hdl=(\d+) resps=(\d+) recv=([\d,]*)$', output, re.M)
        if not m:
            check(False, "probe printed its record")
        else:
            hdl, resps = int(m.group(1)), int(m.group(2))
            received = [int(v) for v in m.group(3).split(',') if v]
            check(hdl == len(EXPECTED), f"the HDL master handed over all {len(EXPECTED)} W beats (hdl={hdl})")
            check(received == EXPECTED, f"the model received every beat in order (received={received})")
            check(resps == BURSTS, f"every burst got its B (resps={resps})")
        if len(FAILURES) > before:
            print(output)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == '__main__':
    test_axi_write_src_bfm_w_first()
    if FAILURES:
        print(f"\n  SOME TESTS FAILED ({len(FAILURES)})")
        sys.exit(1)
    print("\n  ALL TESTS PASSED!")
    sys.exit(0)
