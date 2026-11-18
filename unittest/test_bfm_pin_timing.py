#!/usr/bin/env python3
"""A dst BFM changes its pins only while the clock is high, and a ready the
HDL lowers after the sample point fails the run.

A dst BFM completes the model's call at the sample point, so the HDL must
keep ready high to the next rising edge. On BFM ports an HDL ready, ack or
read data must not depend combinationally on a pin another BFM drives: a
BFM that drives at the sample point changes it after the first BFM read it.
The probe drives the hdl_if signals from SystemC methods and threads
standing in for the RTL, outside UVM, and expects:

- an arbiter whose req_ack ack on port A falls when push_ack port B's push
  rises, with B's push raised at A's sample point, fails the run once with
  `HDL lowered ready after the sample point`, naming A's BFM and channel
  and B's as the BFM port that drove a pin in that time step, and not the
  BFM on port C, which drove its pins earlier;
- a rdy_vld dst BFM whose rdy falls when another rdy_vld dst BFM raises vld
  at its sample point names that other BFM, though the other's transfer was
  certain there and it drives its next beat at the rising edge where the
  break is found, with either BFM constructed first;
- a rdy_vld dst BFM on a multicycle channel and an axi_write dst BFM
  carrying W bursts, behind model writers that send each burst in the
  clock's low phase, raise vld and wvalid only in the high phase, where a
  UVM monitor sampling at the falling edge sees them, and deliver every
  beat;
- with a model writer that sends in the high phase, the same BFMs put the
  burst's first beat on the pins at once, so the fix costs no clock;
- a memory_dst_bfm puts a read the model makes in the low phase on the
  pins one step after the next rising edge, and one made in the high phase
  at once;
- a push_ack dst BFM that raises push at its own sample point, because a
  src BFM handed the model its input there, against a destination whose ack
  follows push combinationally, as a UVM same-clock responder's does, reads
  the ack it had before its own push and takes each push at the next rising
  edge: every value once, in order, one per clock, and no break.
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
#include "push_ack_bfm.h"
#include "req_ack_bfm.h"
#include "rdy_vld_bfm.h"
#include "axi_write_bfm.h"
#include "memory_bfm.h"
#include <cstdint>
#include <cstdio>
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
using bv = sc_bv<32>;

std::uint64_t ps() { return sc_time_stamp().value() / sc_time( 1, SC_PS ).value(); }

std::string join( const std::vector<std::uint64_t> &v )
{
    std::string s;
    for (auto x : v) { s += std::format( "{},", x ); }
    return s;
}

// A combinational priority arbiter standing in for Verilated RTL: B wins
// over A, so ack on A falls when B's push rises.
SC_MODULE( arbiter )
{
    sc_in<bool> clk, rst_n;
    req_ack_channel<wordSt, wordSt> chA;
    push_ack_channel<wordSt> chB, chC;
    req_ack_out<wordSt, wordSt> pA;
    push_ack_out<wordSt> pB, pC;
    req_ack_hdl_if<bv, bv> hA;
    push_ack_hdl_if<bv> hB, hC;
    req_ack_dst_bfm<wordSt, wordSt, bv, bv> bA;
    push_ack_dst_bfm<wordSt, bv> bB, bC;
    SC_HAS_PROCESS( arbiter );
    arbiter( sc_module_name n ) : sc_module( n ), chA( "chA", "blk" ), chB( "chB", "blk" ), chC( "chC", "blk" ),
        bA( "bA" ), bB( "bB" ), bC( "bC" )
    {
        pA( chA ); pB( chB ); pC( chC );
        bA.if_p( chA ); bB.if_p( chB ); bC.if_p( chC );
        bA.hdl_if_p( hA ); bB.hdl_if_p( hB ); bC.hdl_if_p( hC );
        bA.clk( clk ); bB.clk( clk ); bC.clk( clk );
        bA.rst_n( rst_n ); bB.rst_n( rst_n ); bC.rst_n( rst_n );
        SC_METHOD( comb ); sensitive << hA.req << hB.push << hC.push;
        SC_THREAD( modelA ); SC_THREAD( modelBC );
    }
    void comb()
    {
        hA.ack = hA.req.read() && !hB.push.read();
        hA.rdata = bv( 100 );
        hB.ack = hB.push.read();
        hC.ack = hC.push.read();
    }
    void modelA()
    {
        wait( 41, SC_NS );
        wordSt v, r;
        pA->req( v, r );
    }
    // C's push completes at its sample point, and B's push follows at once,
    // in the time step A samples its ack.
    void modelBC()
    {
        wait( 41, SC_NS );
        wordSt v;
        v.w = 7;
        pC->push( v );
        pB->push( v );
    }
};

// A model that writes two four-beat bursts to a rdy_vld dst BFM on a
// multicycle channel, and two to an axi_write dst BFM, the first of each
// pair in the clock's low phase and the second in its high phase. The HDL
// is always ready and answers B at once.
SC_MODULE( bursts )
{
    sc_in<bool> clk, rst_n;
    rdy_vld_channel<wordSt> rvCh;
    rdy_vld_out<wordSt> rvOut;
    rdy_vld_hdl_if<bv> rvHdl;
    rdy_vld_dst_bfm<wordSt, bv> rvBfm;
    axi_write_channel<wordSt, wordSt, strbSt> axCh;
    axi_write_out<wordSt, wordSt, strbSt> axOut;
    axi_write_hdl_if<bv, bv, sc_bv<4>> axHdl;
    axi_write_dst_bfm<wordSt, wordSt, strbSt, bv, bv, sc_bv<4>> axBfm;
    std::vector<std::uint64_t> rvRise, axRise, rvSend, axSend, rvVals, axVals;
    SC_HAS_PROCESS( bursts );
    bursts( sc_module_name n ) : sc_module( n ),
        rvCh( "rvCh", "blk", BACKPRESSURE_ALLOWED, "fixed_size", 3 * sizeof( wordSt ) + 1, "" ), rvOut( "rvOut" ), rvBfm( "rvBfm" ),
        axCh( "axCh", "blk", "api_list_size", 4, "" ), axOut( "axOut" ), axBfm( "axBfm" )
    {
        rvOut( rvCh ); rvBfm.if_p( rvCh ); rvBfm.hdl_if_p( rvHdl ); rvBfm.clk( clk ); rvBfm.rst_n( rst_n );
        axOut( axCh ); axBfm.if_p( axCh ); axBfm.hdl_if_p( axHdl ); axBfm.clk( clk ); axBfm.rst_n( rst_n );
        SC_METHOD( rvWatch ); sensitive << rvHdl.vld; dont_initialize();
        SC_METHOD( axWatch ); sensitive << axHdl.wvalid; dont_initialize();
        SC_METHOD( sink ); sensitive << clk.pos(); dont_initialize();
        SC_THREAD( rvModel ); SC_THREAD( axAddr ); SC_THREAD( axData ); SC_THREAD( axResp );
    }
    void rvWatch() { if (rvHdl.vld.read()) rvRise.push_back( ps() ); }
    void axWatch() { if (axHdl.wvalid.read()) axRise.push_back( ps() ); }
    void sink()
    {
        if (!rst_n) { rvHdl.rdy = 0; axHdl.awready = 0; axHdl.wready = 0; axHdl.bvalid = 0; return; }
        if (rvHdl.vld && rvHdl.rdy) rvVals.push_back( rvHdl.data.read().to_uint64() );
        if (axHdl.wvalid && axHdl.wready) axVals.push_back( axHdl.wdata.read().to_uint64() );
        const bool bTaken = axHdl.bvalid && axHdl.bready;
        const bool last = axHdl.wvalid && axHdl.wready && axHdl.wlast;
        rvHdl.rdy = 1; axHdl.awready = 1; axHdl.wready = 1;
        axHdl.bvalid = last || (axHdl.bvalid && !bTaken);
        axHdl.bid = 0; axHdl.bresp = 0;
    }
    // Waits to the low phase (7 ns into a 10 ns clock) or the high phase
    // (2 ns into it) of a clock after reset, once the last burst is done.
    void phase( bool low )
    {
        do { wait( clk.posedge_event() ); } while (!rst_n);
        wait( 80, SC_NS );
        wait( low ? 7 : 2, SC_NS );
    }
    void rvModel()
    {
        for (int b = 0; b < 2; b++) {
            phase( b == 0 );
            rvSend.push_back( ps() );
            for (int i = 0; i < 4; i++) { wordSt v; v.w = 16 * b + i; rvOut->writeClocked( v ); }
        }
    }
    void axAddr()
    {
        for (int b = 0; b < 2; b++) {
            axiWriteAddressSt<wordSt> a;
            a.awid = 0; a.awaddr.w = 0x100 * b; a.awlen = 3; a.awsize = 2; a.awburst = AXIBURST_INCR;
            axOut->sendAddr( a );
        }
    }
    void axData()
    {
        for (int b = 0; b < 2; b++) {
            phase( b == 0 );
            axSend.push_back( ps() );
            auto *beats = reinterpret_cast<axiWriteDataSt<wordSt, strbSt> *>( axOut->getSendDataPtr() );
            for (int i = 0; i < 4; i++) {
                beats[i].wid = 0; beats[i].wdata.w = 16 * b + i; beats[i].wstrb.w = 0xf; beats[i].wlast = i == 3;
            }
            axOut->sendData( beats[0], 4 );
        }
    }
    void axResp() { while (true) { axiWriteRespSt<> r; axOut->receiveResp( r ); } }
};

// A model that relays a push_ack input to a push_ack output. From 200 ns,
// clear of the arbiter, the HDL source pushes a new value every clock. The src BFM hands each to the
// model at its sample point, so the model's output push reaches the dst BFM
// there, and the dst BFM raises push in the time step it samples ack. The
// destination's ack follows push combinationally, as a UVM same-clock
// responder's does, and is the only process that drives it.
SC_MODULE( follow )
{
    sc_in<bool> clk, rst_n;
    push_ack_channel<wordSt> inCh, outCh;
    push_ack_in<wordSt> in;
    push_ack_out<wordSt> out;
    push_ack_hdl_if<bv> inHdl, outHdl;
    push_ack_src_bfm<wordSt, bv> inBfm;
    push_ack_dst_bfm<wordSt, bv> outBfm;
    std::vector<std::uint64_t> pushed, taken, vals;
    int next = 0;
    SC_HAS_PROCESS( follow );
    follow( sc_module_name n ) : sc_module( n ), inCh( "inCh", "blk" ), outCh( "outCh", "blk" ), in( "in" ), out( "out" ),
        inBfm( "inBfm" ), outBfm( "outBfm" )
    {
        in( inCh ); out( outCh );
        inBfm.if_p( inCh ); inBfm.hdl_if_p( inHdl ); inBfm.clk( clk ); inBfm.rst_n( rst_n );
        outBfm.if_p( outCh ); outBfm.hdl_if_p( outHdl ); outBfm.clk( clk ); outBfm.rst_n( rst_n );
        SC_METHOD( responder ); sensitive << outHdl.push;
        SC_METHOD( edge ); sensitive << clk.pos(); dont_initialize();
        SC_THREAD( model );
    }
    void responder() { outHdl.ack = outHdl.push.read(); }
    void edge()
    {
        if (!rst_n) { inHdl.push = 0; return; }
        if (outHdl.push && outHdl.ack) { taken.push_back( ps() ); vals.push_back( outHdl.data.read().to_uint64() ); }
        if (inHdl.push && inHdl.ack) { next++; }
        inHdl.push = next < 6 && sc_time_stamp() >= sc_time( 200, SC_NS );
        inHdl.data = bv( 200 + next );
    }
    void model()
    {
        while (true) {
            wordSt v;
            in->pushReceive( v );
            in->ack();
            pushed.push_back( ps() );
            out->push( v );
        }
    }
};

// A model that makes a memory read in the clock's low phase, and one in its
// high phase, behind a memory_dst_bfm. The HDL memory answers each read at
// the access edge with 300 plus the address.
SC_MODULE( memPhase )
{
    sc_in<bool> clk, rst_n;
    memory_channel<wordSt, wordSt> ch;
    memory_out<wordSt, wordSt> out;
    memory_hdl_if<bv, bv> hdl;
    memory_dst_bfm<wordSt, wordSt, bv, bv> bfm;
    std::vector<std::uint64_t> sent, rise, data;
    SC_HAS_PROCESS( memPhase );
    memPhase( sc_module_name n ) : sc_module( n ), ch( "ch", "blk" ), out( "out" ), bfm( "bfm" )
    {
        out( ch ); bfm.if_p( ch ); bfm.hdl_if_p( hdl ); bfm.clk( clk ); bfm.rst_n( rst_n );
        SC_METHOD( watch ); sensitive << hdl.enable; dont_initialize();
        SC_METHOD( memory ); sensitive << clk.pos(); dont_initialize();
        SC_THREAD( model );
    }
    void watch() { if (hdl.enable.read()) rise.push_back( ps() ); }
    void memory() { if (hdl.enable) hdl.read_data = bv( 300 + hdl.addr.read().to_uint64() ); }
    void model()
    {
        for (int k = 0; k < 2; k++) {
            wait( sc_time( 300 + 50 * k, SC_NS ) - sc_time_stamp() );
            wait( k == 0 ? 7 : 2, SC_NS );
            sent.push_back( ps() );
            wordSt a, d;
            a.w = k;
            out->request( false, a, d );
            data.push_back( d.w );
        }
    }
};

// Two rdy_vld dst BFMs. The victim's HDL rdy is low while the culprit's vld
// is high. The victim offers a beat early in the clock that starts at at_ and
// samples rdy high at the sample point. The culprit's model offers two beats
// at that sample point, so the culprit raises vld there, its own transfer is
// certain there, and it drives its second beat again at the next rising edge,
// where the victim finds rdy low. culpritFirst constructs the culprit's BFM
// before the victim's, which decides whose thread runs first at that edge.
SC_MODULE( culprit )
{
    sc_in<bool> clk, rst_n;
    rdy_vld_channel<wordSt> ch0, ch1;
    rdy_vld_out<wordSt> o0, o1;
    rdy_vld_hdl_if<bv> h0, h1;
    rdy_vld_dst_bfm<wordSt, bv> b0, b1;
    rdy_vld_out<wordSt> &oC, &oV;
    rdy_vld_hdl_if<bv> &hC, &hV;
    const sc_time at_;
    SC_HAS_PROCESS( culprit );
    culprit( sc_module_name n, bool culpritFirst, sc_time at ) : sc_module( n ),
        ch0( "ch0", "blk", BACKPRESSURE_ALLOWED ), ch1( "ch1", "blk", BACKPRESSURE_ALLOWED ), o0( "o0" ), o1( "o1" ),
        b0( "b0" ), b1( "b1" ), oC( culpritFirst ? o0 : o1 ), oV( culpritFirst ? o1 : o0 ),
        hC( culpritFirst ? h0 : h1 ), hV( culpritFirst ? h1 : h0 ), at_( at )
    {
        o0( ch0 ); b0.if_p( ch0 ); b0.hdl_if_p( h0 ); b0.clk( clk ); b0.rst_n( rst_n );
        o1( ch1 ); b1.if_p( ch1 ); b1.hdl_if_p( h1 ); b1.clk( clk ); b1.rst_n( rst_n );
        SC_METHOD( comb ); sensitive << hC.vld << rst_n;
        SC_THREAD( victimModel ); SC_THREAD( culpritModel );
    }
    void comb()
    {
        hC.rdy = 1;
        hV.rdy = rst_n.read() && !hC.vld.read();
    }
    void victimModel()
    {
        wait( at_ + sc_time( 2, SC_NS ) - sc_time_stamp() );
        wordSt v;
        oV->write( v );
    }
    void culpritModel()
    {
        wait( at_ + sc_time( 4999, SC_PS ) - sc_time_stamp() );
        wordSt v;
        oC->write( v );
        oC->write( v );
    }
};

SC_MODULE( probe )
{
    sc_clock clk;
    sc_signal<bool> rst_n;
    arbiter arb;
    bursts bur;
    follow fol;
    memPhase mem;
    culprit cuA, cuB;
    SC_HAS_PROCESS( probe );
    probe( sc_module_name n ) : sc_module( n ), clk( "clk", 10, SC_NS ), arb( "arb" ), bur( "bur" ), fol( "fol" ), mem( "mem" ),
        cuA( "cuA", true, sc_time( 400, SC_NS ) ), cuB( "cuB", false, sc_time( 440, SC_NS ) )
    {
        arb.clk( clk ); arb.rst_n( rst_n ); bur.clk( clk ); bur.rst_n( rst_n ); fol.clk( clk ); fol.rst_n( rst_n );
        mem.clk( clk ); mem.rst_n( rst_n ); cuA.clk( clk ); cuA.rst_n( rst_n ); cuB.clk( clk ); cuB.rst_n( rst_n );
        SC_THREAD( run );
    }
    void run()
    {
        rst_n = 0;
        wait( 25, SC_NS );
        rst_n = 1;
        // The culprit breaks later overwrite the run's error string.
        wait( 125, SC_NS );
        std::printf( "exit code %d: %s\\n", errorCode::getExitCode(), errorCode::getErrorString().c_str() );
        wait( 375, SC_NS );
        std::printf( "rec bursts rvRise=%s axRise=%s rvSend=%s axSend=%s rvVals=%s axVals=%s\\n",
                     join( bur.rvRise ).c_str(), join( bur.axRise ).c_str(), join( bur.rvSend ).c_str(),
                     join( bur.axSend ).c_str(), join( bur.rvVals ).c_str(), join( bur.axVals ).c_str() );
        std::printf( "rec mem sent=%s rise=%s data=%s\\n", join( mem.sent ).c_str(), join( mem.rise ).c_str(), join( mem.data ).c_str() );
        std::printf( "rec follow pushed=%s taken=%s vals=%s\\n", join( fol.pushed ).c_str(), join( fol.taken ).c_str(),
                     join( fol.vals ).c_str() );
        sc_stop();
    }
};

int sc_main( int, char *[] )
{
    logging::GetInstance().setDefaultVerbosity( VERBOSITY_MEDIUM );
    probe p( "p" );
    sc_start();
    std::printf( "exit code %d: %s\\n", errorCode::getExitCode(), errorCode::getErrorString().c_str() );
    std::printf( "probe done\\n" );
    return 0;
}
"""

LOWERED = 'HDL lowered ready after the sample point'
FAILURES = []


def check(condition, message):
    print(f"  {'PASS' if condition else 'FAIL'}: {message}")
    if not condition:
        FAILURES.append(message)


def nums(rec, key):
    return [int(v) for v in rec.get(key, '').split(',') if v]


def test_bfm_pin_timing():
    scLibdir = os.environ.get('SYSTEMC_LIBDIR', '')
    tmpdir = tempfile.mkdtemp(prefix='a2c_bfm_pin_timing_')
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

        lowered = [line for line in output.splitlines() if line.startswith('p.arb.bA:') and LOWERED in line]
        first = lowered[0] if lowered else ''
        check(len(lowered) == 2 and 'at 50 ns' in first and '(p.arb.bA on p.arb.chA, ready sampled high at 44999 ps)' in first,
              f"arbiter: ack on A lowered by B's push logs the break on A at the 50 ns edge, naming A's BFM, its "
              f"channel and its sample point, and its total at the end (got {lowered})")
        check(first.endswith("BFM ports that drove a pin in the sample point's time step: p.arb.bB on p.arb.chB")
              and 'depend combinationally on a pin another BFM drives' in first,
              f"arbiter: the break names the precondition and lists B, which drove its push then, and not C "
              f"(got {first[-160:]})")
        m = re.search(r'^exit code (\d+): (.*)$', output, re.M)
        check(m is not None and m.group(1) == '1' and m.group(2).startswith('p.arb.bA:' + LOWERED),
              f"arbiter: outside UVM the break fails the run (got {m.group(0) if m else None})")

        for mod, culpritBfm, victimBfm, edge in [('cuA', 'b0', 'b1', '410 ns'), ('cuB', 'b1', 'b0', '450 ns')]:
            line = next((line for line in output.splitlines()
                         if line.startswith(f'p.{mod}.{victimBfm}:') and LOWERED in line), '')
            check(f'at {edge}' in line and line.endswith(
                      f"BFM ports that drove a pin in the sample point's time step: p.{mod}.{culpritBfm} on p.{mod}.ch{culpritBfm[1]}"),
                  f"{mod}: a culprit that drove at the sample point and drives again at the next rising edge is named, "
                  f"whichever BFM thread runs first there (got {line[-200:]})")

        rec = {}
        mb = re.search(r'^rec bursts (.*)$', output, re.M)
        if mb:
            rec = dict(re.findall(r'(\w+)=([\d,]*)', mb.group(1)))
        expected = [str(16 * b + i) for b in range(2) for i in range(4)]
        for name, rise, send, vals in [('rdy_vld multicycle', 'rvRise', 'rvSend', 'rvVals'),
                                       ('axi_write W burst', 'axRise', 'axSend', 'axVals')]:
            rises, sends = nums(rec, rise), nums(rec, send)
            check(rec.get(vals, '').split(',')[:-1] == expected,
                  f"{name}: every beat of both bursts reaches the HDL, in order (got {rec.get(vals)})")
            check(len(rises) >= 2 and all(t % 10000 < 5000 for t in rises),
                  f"{name}: the valid pin rises only while the clock is high (rises in ps={rises})")
            check(len(sends) == 2 and len(rises) >= 2 and rises[0] == sends[0] - 7000 + 10001 and rises[0] % 10000 == 1,
                  f"{name}: a burst sent in the low phase goes on the pins one step after the next rising edge "
                  f"(sent={sends[:1]} rose={rises[:1]})")
            check(len(sends) == 2 and sends[1] in rises,
                  f"{name}: a burst sent in the high phase goes on the pins at once (sent={sends[1:]} rises={rises})")
        mm = re.search(r'^rec mem (.*)$', output, re.M)
        mem = dict(re.findall(r'(\w+)=([\d,]*)', mm.group(1))) if mm else {}
        sent, rise = nums(mem, 'sent'), nums(mem, 'rise')
        check(sent == [307000, 352000] and rise == [310001, 352000] and mem.get('data') == '300,301,',
              f"memory: a read made in the low phase drives enable one step after the next rising edge, one made in "
              f"the high phase at once, and both return their data (sent={sent} rise={rise} data={mem.get('data')})")
        mf = re.search(r'^rec follow (.*)$', output, re.M)
        fol = dict(re.findall(r'(\w+)=([\d,]*)', mf.group(1))) if mf else {}
        pushed, taken = nums(fol, 'pushed'), nums(fol, 'taken')
        check(len(pushed) == 6 and all(t % 10000 == 4999 for t in pushed),
              f"follow: the model gets each input at the src BFM's sample point (pushed in ps={pushed})")
        check(fol.get('vals', '').split(',')[:-1] == [str(200 + k) for k in range(6)]
              and len(taken) == 6 and all(t == p + 5001 for p, t in zip(pushed, taken)),
              f"follow: each push raised at the sample point is taken at the next rising edge, once and in order "
              f"(taken={taken} vals={fol.get('vals')})")
        check(not any(line.startswith('p.fol.') and LOWERED in line for line in output.splitlines()),
              "follow: an ack that follows push in the sample point's time step breaks nothing")
        if len(FAILURES) > before:
            print(output[-6000:])
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == '__main__':
    test_bfm_pin_timing()
    if FAILURES:
        print(f"  SOME TESTS FAILED ({len(FAILURES)})")
        sys.exit(1)
    print("  ALL TESTS PASSED!")
