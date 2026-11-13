#!/usr/bin/env python3
"""The rdy_vld and axi4_stream BFMs keep the HDL handshake in step with the channel.

A BFM reads the backpressure rule from the channel its if_p is bound to. The
probe drives each BFM's hdl_if signals from a SystemC thread standing in for
the RTL, and expects:

- a dst BFM on a BACKPRESSURE_NONE channel warns once when the HDL holds rdy
  low under vld, and reports the stalled edge count at end of simulation;
- a dst BFM reads a value from the channel only on the edge the HDL transfers
  it, so each write returns on that edge and the BFM holds no value of its own;
- the same stall on a BACKPRESSURE_ALLOWED channel logs nothing;
- a src BFM holds rdy low while a delayed channel write blocks, so on an
  allowed channel every beat the HDL sends arrives in order and nothing warns.
  That holds for a fixed delay, a delay that ends on a clock edge, a random
  delay, an HDL whose vld follows rdy combinationally, a reset that asserts
  while a write blocks, and a multicycle channel that delays only at a
  transaction border;
- a reset edge with vld and rdy high logs nothing. The BFM delivers the beat
  it samples on that edge, and the HDL sends it again after reset;
- without a delay the src BFM takes one beat per clock edge, also when the
  reader comes back for the next beat a few delta cycles later, and rdy rises
  on the second edge after reset release;
- a src BFM whose reader is away holds rdy low until the reader is back, so it
  takes no beat the reader has no room for;
- a src BFM on a no-backpressure channel whose reader stalls lowers rdy, and
  warns that SystemC stalled the producer. When the HDL ignores rdy it loses
  beats, and the stalled edge count equals the beats sent minus the beats
  delivered. When the HDL honours rdy every beat arrives in order. Neither
  case reports a lost beat, because a transfer needs rdy high.
"""

import os
import re
import shutil
import subprocess
import sys
import tempfile

from test_watchdog_no_terminator import buildProbe

PROBE_HEADER = """
#include "systemc.h"
#include "logging.h"
#include "q_assert.h"
#include "rdy_vld_bfm.h"
#include "axi4_stream_bfm.h"
#include <cstdint>
#include <cstdio>
#include <format>
#include <memory>
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

using streamInfo = axi4StreamInfoSt<wordSt, wordSt, wordSt>;
using rvHdl = rdy_vld_hdl_if<sc_bv<64>>;
using axHdl = axi4_stream_hdl_if<sc_bv<64>, sc_bv<64>, sc_bv<64>, sc_bv<8>, sc_bv<8>>;
"""

PROBE_SRC = PROBE_HEADER + """
constexpr int BEATS = 8;
constexpr int TRACE_EDGES = 6;

// The HDL consumer takes the first beat, then holds rdy low for two edges.
void stallingConsumer( sc_in<bool> &clk, sc_in<bool> &rst_n, sc_signal<bool> &vld, sc_signal<bool> &rdy )
{
    rdy = 1;
    int taken = 0;
    while (true) {
        wait( clk.posedge_event() );
        if (rst_n && vld && rdy && ++taken == 1) {
            rdy = 0;
            wait( clk.posedge_event() );
            wait( clk.posedge_event() );
            rdy = 1;
        }
    }
}

struct srcCfg {
    channelBackpressure bp = BACKPRESSURE_ALLOWED;
    int delayNs = 0;
    timedDelayMode delayMode = TIMED_DELAY_FIXED_INIT;
    int readGapNs = 0;
    int readDeltas = 0;     // delta cycles the reader spends before it reads again
    bool combVld = false;   // the HDL drives vld from rdy combinationally
    bool honourRdy = false; // on a no-backpressure channel the HDL still waits for rdy
    bool multiCycle = false;
};

// What the HDL stand-in sent, what the reader received, and the rdy the HDL
// saw on the first edges.
struct srcRecord {
    int hdlBeats = 0;
    std::vector<std::uint64_t> received;
    std::vector<std::uint64_t> transferNs;
    std::vector<int> rdyTrace;
    void print( const char *name )
    {
        std::string recv, times, trace;
        for (auto v : received) { recv += std::format( "{},", v ); }
        for (auto t : transferNs) { times += std::format( "{},", t ); }
        for (auto r : rdyTrace) { trace += std::format( "{},", r ); }
        std::printf( "src %s hdl=%d recv=%s times=%s rdy=%s\\n", name, hdlBeats, recv.c_str(), times.c_str(), trace.c_str() );
    }
};

// The HDL producer offers BEATS beats back to back from a register. With
// ignoreRdy it treats every vld edge as a transfer, as a backpressure: false
// producer does. Reset drops vld and keeps the beat count.
template <typename SETDATA>
void producer( sc_in<bool> &clk, sc_in<bool> &rst_n, sc_signal<bool> &vld, sc_signal<bool> &rdy,
               bool ignoreRdy, srcRecord &rec, SETDATA setData )
{
    while (true) {
        wait( clk.posedge_event() );
        if ((int)rec.rdyTrace.size() < TRACE_EDGES) { rec.rdyTrace.push_back( rdy.read() ); }
        if (!rst_n) { vld = 0; continue; }
        if (vld && (ignoreRdy || rdy)) { rec.transferNs.push_back( sc_time_stamp().value() / 1000 ); rec.hdlBeats++; }
        vld = rec.hdlBeats < BEATS;
        setData( rec.hdlBeats );
    }
}

// The same producer with vld = rdy && beat pending, re-evaluated whenever rdy
// or reset changes, so a delta-cycle rdy pulse also pulses vld.
template <typename SETDATA>
void combProducer( sc_in<bool> &clk, sc_in<bool> &rst_n, sc_signal<bool> &vld, sc_signal<bool> &rdy,
                   srcRecord &rec, SETDATA setData )
{
    while (true) {
        wait( clk.posedge_event() | rdy.value_changed_event() | rst_n.value_changed_event() );
        if (clk.posedge()) {
            if ((int)rec.rdyTrace.size() < TRACE_EDGES) { rec.rdyTrace.push_back( rdy.read() ); }
            if (rst_n && vld && rdy) { rec.transferNs.push_back( sc_time_stamp().value() / 1000 ); rec.hdlBeats++; }
        }
        vld = rst_n && rdy && rec.hdlBeats < BEATS;
        setData( rec.hdlBeats );
    }
}

template <typename SETDATA>
void hdlSource( const srcCfg &cfg, sc_in<bool> &clk, sc_in<bool> &rst_n, sc_signal<bool> &vld, sc_signal<bool> &rdy,
                srcRecord &rec, SETDATA setData )
{
    if (cfg.combVld) {
        combProducer( clk, rst_n, vld, rdy, rec, setData );
    } else {
        producer( clk, rst_n, vld, rdy, cfg.bp == BACKPRESSURE_NONE && !cfg.honourRdy, rec, setData );
    }
}

void readerPause( const srcCfg &cfg )
{
    for (int i = 0; i < cfg.readDeltas; i++) { wait( SC_ZERO_TIME ); }
    if (cfg.readGapNs) { wait( cfg.readGapNs, SC_NS ); }
}

SC_MODULE( rvDst )
{
    sc_in<bool> clk, rst_n;
    rdy_vld_channel<wordSt> ch;
    rdy_vld_out<wordSt> out;
    rvHdl hdl;
    rdy_vld_dst_bfm<wordSt, sc_bv<64>> bfm;

    SC_HAS_PROCESS( rvDst );
    std::string writeNs;
    rvDst( sc_module_name n, channelBackpressure bp ) : sc_module( n ), ch( "ch", "tb", bp ), out( "out" ), bfm( "bfm" )
    {
        out( ch ); bfm.if_p( ch ); bfm.hdl_if_p( hdl ); bfm.clk( clk ); bfm.rst_n( rst_n );
        SC_THREAD( tb ); SC_THREAD( hdlThread );
    }
    void tb()
    {
        for (int i = 0; i < 4; i++) {
            wordSt v; v.w = i; out->write( v );
            writeNs += std::format( "{},", sc_time_stamp().value() / 1000 );
        }
    }
    void hdlThread() { stallingConsumer( clk, rst_n, hdl.vld, hdl.rdy ); }
};

// A multicycle channel of four-beat transactions delays only the beat that
// completes a transaction. The ping-pong buffer adds a beat less one byte to
// the size it is given, so 25 bytes become 32.
std::unique_ptr<rdy_vld_channel<wordSt>> rvChannel( const srcCfg &cfg )
{
    if (cfg.multiCycle) {
        return std::make_unique<rdy_vld_channel<wordSt>>( "ch", "tb", cfg.bp, "fixed_size", 3 * sizeof( wordSt ) + 1, "" );
    }
    return std::make_unique<rdy_vld_channel<wordSt>>( "ch", "tb", cfg.bp );
}

SC_MODULE( rvSrc )
{
    sc_in<bool> clk, rst_n;
    srcCfg cfg;
    std::unique_ptr<rdy_vld_channel<wordSt>> ch;
    rdy_vld_in<wordSt> in;
    rvHdl hdl;
    rdy_vld_src_bfm<wordSt, sc_bv<64>> bfm;
    srcRecord rec;

    SC_HAS_PROCESS( rvSrc );
    rvSrc( sc_module_name n, srcCfg cfg_ ) : sc_module( n ), cfg( cfg_ ), ch( rvChannel( cfg_ ) ), in( "in" ), bfm( "bfm" )
    {
        in( *ch ); bfm.if_p( *ch ); bfm.hdl_if_p( hdl ); bfm.clk( clk ); bfm.rst_n( rst_n );
        ch->setTimed( cfg.delayNs, cfg.delayMode );
        SC_THREAD( tb ); SC_THREAD( hdlThread );
    }
    void tb()
    {
        while (true) {
            wordSt v;
            if (cfg.multiCycle) { in->readClocked( v ); } else { in->read( v ); }
            rec.received.push_back( v.w );
            readerPause( cfg );
        }
    }
    void hdlThread()
    {
        hdlSource( cfg, clk, rst_n, hdl.vld, hdl.rdy, rec, [this]( int i ) { wordSt v; v.w = i; hdl.data = v.sc_pack(); } );
    }
};

SC_MODULE( axDst )
{
    sc_in<bool> clk, rst_n;
    axi4_stream_channel<wordSt, wordSt, wordSt> ch;
    axi4_stream_out<wordSt, wordSt, wordSt> out;
    axHdl hdl;
    axi4_stream_dst_bfm<wordSt, wordSt, wordSt, sc_bv<64>, sc_bv<64>, sc_bv<64>, sc_bv<8>, sc_bv<8>> bfm;

    SC_HAS_PROCESS( axDst );
    std::string writeNs;
    axDst( sc_module_name n, channelBackpressure bp ) : sc_module( n ), ch( "ch", "tb", bp ), out( "out" ), bfm( "bfm" )
    {
        out( ch ); bfm.if_p( ch ); bfm.hdl_if_p( hdl ); bfm.clk( clk ); bfm.rst_n( rst_n );
        SC_THREAD( tb ); SC_THREAD( hdlThread );
    }
    void tb()
    {
        for (int i = 0; i < 4; i++) {
            streamInfo s; s.tdata.w = i; out->sendInfo( s, std::nullopt );
            writeNs += std::format( "{},", sc_time_stamp().value() / 1000 );
        }
    }
    void hdlThread() { stallingConsumer( clk, rst_n, hdl.tvalid, hdl.tready ); }
};

SC_MODULE( axSrc )
{
    sc_in<bool> clk, rst_n;
    srcCfg cfg;
    axi4_stream_channel<wordSt, wordSt, wordSt> ch;
    axi4_stream_in<wordSt, wordSt, wordSt> in;
    axHdl hdl;
    axi4_stream_src_bfm<wordSt, wordSt, wordSt, sc_bv<64>, sc_bv<64>, sc_bv<64>, sc_bv<8>, sc_bv<8>> bfm;
    srcRecord rec;

    SC_HAS_PROCESS( axSrc );
    axSrc( sc_module_name n, srcCfg cfg_ ) : sc_module( n ), cfg( cfg_ ), ch( "ch", "tb", cfg_.bp ), in( "in" ), bfm( "bfm" )
    {
        in( ch ); bfm.if_p( ch ); bfm.hdl_if_p( hdl ); bfm.clk( clk ); bfm.rst_n( rst_n );
        ch.setTimed( cfg.delayNs, cfg.delayMode );
        SC_THREAD( tb ); SC_THREAD( hdlThread );
    }
    void tb()
    {
        while (true) {
            streamInfo s;
            in->receiveInfo( s );
            rec.received.push_back( s.tdata.w );
            readerPause( cfg );
        }
    }
    void hdlThread()
    {
        hdlSource( cfg, clk, rst_n, hdl.tvalid, hdl.tready, rec, [this]( int i ) { wordSt v; v.w = i; hdl.tdata = v.sc_pack(); } );
    }
};

srcCfg delayed( int ns, timedDelayMode mode = TIMED_DELAY_FIXED_INIT ) { srcCfg c; c.delayNs = ns; c.delayMode = mode; return c; }
srcCfg gapped( channelBackpressure bp, int gapNs ) { srcCfg c; c.bp = bp; c.readGapNs = gapNs; return c; }
srcCfg comb( int ns ) { srcCfg c = delayed( ns ); c.combVld = true; return c; }
srcCfg pipelined() { srcCfg c; c.readDeltas = 3; return c; }
srcCfg multi( int ns ) { srcCfg c = delayed( ns ); c.multiCycle = true; return c; }
srcCfg honouring() { srcCfg c = gapped( BACKPRESSURE_NONE, 25 ); c.honourRdy = true; return c; }

SC_MODULE( probe )
{
    sc_clock clk;
    sc_signal<bool> rst_n, rstMid;
    rvDst rvDstNone, rvDstAllowed;
    axDst axDstNone, axDstAllowed;
    std::vector<std::unique_ptr<rvSrc>> rv;
    std::vector<std::unique_ptr<axSrc>> ax;

    SC_HAS_PROCESS( probe );
    probe( sc_module_name n )
      : sc_module( n ), clk( "clk", 10, SC_NS ),
        rvDstNone( "rvDstNone", BACKPRESSURE_NONE ), rvDstAllowed( "rvDstAllowed", BACKPRESSURE_ALLOWED ),
        axDstNone( "axDstNone", BACKPRESSURE_NONE ), axDstAllowed( "axDstAllowed", BACKPRESSURE_ALLOWED )
    {
        for (auto *m : { &rvDstNone, &rvDstAllowed }) { m->clk( clk ); m->rst_n( rst_n ); }
        for (auto *m : { &axDstNone, &axDstAllowed }) { m->clk( clk ); m->rst_n( rst_n ); }
        // Shared by both families. rv only: no-backpressure and multicycle.
        std::vector<std::pair<std::string, srcCfg>> both = {
            { "Throughput", srcCfg() }, { "Pipelined", pipelined() },
            { "AllowedGap", gapped( BACKPRESSURE_ALLOWED, 25 ) },
            { "Delay15", delayed( 15 ) }, { "Delay20", delayed( 20 ) },
            { "DelayRand", delayed( 33, TIMED_DELAY_RAND_FULL ) },
            { "Comb", comb( 0 ) }, { "CombDelay", comb( 15 ) }, { "ResetDelay", delayed( 45 ) },
            { "ResetHot", srcCfg() }, { "NoneHonour", honouring() },
        };
        for (auto &[suffix, cfg] : both) {
            rv.push_back( std::make_unique<rvSrc>( ( "rvSrc" + suffix ).c_str(), cfg ) );
            ax.push_back( std::make_unique<axSrc>( ( "axSrc" + suffix ).c_str(), cfg ) );
        }
        rv.push_back( std::make_unique<rvSrc>( "rvSrcNone", gapped( BACKPRESSURE_NONE, 0 ) ) );
        rv.push_back( std::make_unique<rvSrc>( "rvSrcNoneGap", gapped( BACKPRESSURE_NONE, 25 ) ) );
        rv.push_back( std::make_unique<rvSrc>( "rvSrcMulti", multi( 0 ) ) );
        rv.push_back( std::make_unique<rvSrc>( "rvSrcMultiDelay", multi( 15 ) ) );
        auto midReset = []( const std::string &n ) { return n.ends_with( "ResetDelay" ) || n.ends_with( "ResetHot" ); };
        for (auto &m : rv) { m->clk( clk ); m->rst_n( midReset( m->basename() ) ? rstMid : rst_n ); }
        for (auto &m : ax) { m->clk( clk ); m->rst_n( midReset( m->basename() ) ? rstMid : rst_n ); }
        SC_THREAD( run );
    }

    // rstMid repeats the boot reset, then asserts again from 75 to 95 ns.
    // ResetDelay's 45 ns write of the first beat (sampled at 40 ns) blocks
    // across it. ResetHot's 80 ns edge sees reset with vld and rdy high.
    void run()
    {
        rst_n = 0;
        rstMid = 0;
        wait( 25, SC_NS );
        rst_n = 1;
        rstMid = 1;
        wait( 50, SC_NS );
        rstMid = 0;
        wait( 20, SC_NS );
        rstMid = 1;
        wait( 2, SC_US );
        for (auto &m : rv) { m->rec.print( m->name() ); }
        for (auto &m : ax) { m->rec.print( m->name() ); }
        std::printf( "dst p.rvDstNone writes=%s\\n", rvDstNone.writeNs.c_str() );
        std::printf( "dst p.axDstNone writes=%s\\n", axDstNone.writeNs.c_str() );
        sc_stop();
    }
};

int sc_main( int, char *[] )
{
    // A BFM reads the default verbosity when it is built, as sc_main does in a real run.
    logging::GetInstance().setDefaultVerbosity( VERBOSITY_MEDIUM );
    probe p( "p" );
    sc_start();
    std::printf( "probe done\\n" );
    return 0;
}
"""

RATE_PROBE_SRC = PROBE_HEADER + """
constexpr int RATE_BEATS = 3 * bfmClockPaced::threshold;
constexpr int RELAY_BEATS = 1000;

std::uint64_t nowNs() { return sc_time_stamp().value() / 1000; }

std::string join( const std::vector<std::uint64_t> &v )
{
    std::string s;
    for (auto x : v) { s += std::format( "{},", x ); }
    return s;
}

// The two families behind one set of probe modules.
struct rvFamily {
    using chan = rdy_vld_channel<wordSt>;
    using in = rdy_vld_in<wordSt>;
    using out = rdy_vld_out<wordSt>;
    using hdl = rvHdl;
    using src = rdy_vld_src_bfm<wordSt, sc_bv<64>>;
    using dst = rdy_vld_dst_bfm<wordSt, sc_bv<64>>;
    static std::uint64_t get( in &p ) { wordSt v; p->read( v ); return v.w; }
    static void put( out &p, std::uint64_t w ) { wordSt v; v.w = w; p->write( v ); }
    static sc_signal<bool> &vld( hdl &h ) { return h.vld; }
    static sc_signal<bool> &rdy( hdl &h ) { return h.rdy; }
    static void setData( hdl &h, std::uint64_t w ) { wordSt v; v.w = w; h.data = v.sc_pack(); }
    static std::uint64_t data( hdl &h ) { return sc_bv<64>( h.data.read() ).to_uint64(); }
};

struct axFamily {
    using chan = axi4_stream_channel<wordSt, wordSt, wordSt>;
    using in = axi4_stream_in<wordSt, wordSt, wordSt>;
    using out = axi4_stream_out<wordSt, wordSt, wordSt>;
    using hdl = axHdl;
    using src = axi4_stream_src_bfm<wordSt, wordSt, wordSt, sc_bv<64>, sc_bv<64>, sc_bv<64>, sc_bv<8>, sc_bv<8>>;
    using dst = axi4_stream_dst_bfm<wordSt, wordSt, wordSt, sc_bv<64>, sc_bv<64>, sc_bv<64>, sc_bv<8>, sc_bv<8>>;
    static std::uint64_t get( in &p ) { streamInfo s; p->receiveInfo( s ); return s.tdata.w; }
    static void put( out &p, std::uint64_t w ) { streamInfo s; s.tdata.w = w; p->sendInfo( s, std::nullopt ); }
    static sc_signal<bool> &vld( hdl &h ) { return h.tvalid; }
    static sc_signal<bool> &rdy( hdl &h ) { return h.tready; }
    static void setData( hdl &h, std::uint64_t w ) { wordSt v; v.w = w; h.tdata = v.sc_pack(); }
    static std::uint64_t data( hdl &h ) { return sc_bv<64>( h.tdata.read() ).to_uint64(); }
};

// The HDL offers `count` beats back to back from a register and honours rdy.
template <typename F>
void hdlProducer( sc_in<bool> &clk, sc_in<bool> &rst_n, typename F::hdl &h, int count, std::vector<std::uint64_t> &times )
{
    int sent = 0;
    while (true) {
        wait( clk.posedge_event() );
        if (!rst_n) { F::vld( h ) = 0; continue; }
        if (F::vld( h ) && F::rdy( h )) { times.push_back( nowNs() ); sent++; }
        F::vld( h ) = sent < count;
        F::setData( h, sent );
    }
}

// The HDL raises rdy on the edge at rdyFromNs and keeps it high or, with a
// seed, drives it from a random bit on every edge.
template <typename F>
void hdlConsumer( sc_in<bool> &clk, sc_in<bool> &rst_n, typename F::hdl &h, std::uint64_t rdyFromNs, std::uint32_t seed,
                  std::vector<std::uint64_t> &times, std::vector<std::uint64_t> &vals )
{
    std::uint32_t lcg = seed;
    F::rdy( h ) = 0;
    while (true) {
        wait( clk.posedge_event() );
        if (rst_n && F::vld( h ) && F::rdy( h )) { times.push_back( nowNs() ); vals.push_back( F::data( h ) ); }
        if (seed) {
            lcg = lcg * 1664525u + 1013904223u;
            F::rdy( h ) = (lcg >> 16) & 1;
        } else {
            F::rdy( h ) = nowNs() >= rdyFromNs;
        }
    }
}

// A model reader behind a src BFM. A transactional reader calls the port
// again at once; a clock-paced one first waits for the next edge.
template <typename F>
struct srcRate : sc_module {
    sc_in<bool> clk, rst_n;
    typename F::chan ch;
    typename F::in in;
    typename F::hdl hdl;
    typename F::src bfm;
    bool paced;
    std::vector<std::uint64_t> times, recv;
    SC_HAS_PROCESS( srcRate );
    srcRate( sc_module_name n, bool paced_ ) : sc_module( n ), ch( "ch", "tb", BACKPRESSURE_ALLOWED ), in( "in" ), bfm( "bfm" ), paced( paced_ )
    {
        in( ch ); bfm.if_p( ch ); bfm.hdl_if_p( hdl ); bfm.clk( clk ); bfm.rst_n( rst_n );
        SC_THREAD( model ); SC_THREAD( hdlThread );
    }
    void model() { while (true) { recv.push_back( F::get( in ) ); if (paced) { wait( clk.posedge_event() ); } } }
    void hdlThread() { hdlProducer<F>( clk, rst_n, hdl, RATE_BEATS, times ); }
    void print() { std::printf( "rec %s times=%s recv=%s\\n", name(), join( times ).c_str(), join( recv ).c_str() ); }
};

// A model writer behind a dst BFM, transactional or clock-paced, into an HDL
// that is always ready.
template <typename F>
struct dstRate : sc_module {
    sc_in<bool> clk, rst_n;
    typename F::chan ch;
    typename F::out out;
    typename F::hdl hdl;
    typename F::dst bfm;
    bool paced;
    std::vector<std::uint64_t> times, vals, returns;
    SC_HAS_PROCESS( dstRate );
    dstRate( sc_module_name n, bool paced_, int delayNs = 0 ) : sc_module( n ), ch( "ch", "tb", BACKPRESSURE_ALLOWED ), out( "out" ), bfm( "bfm" ), paced( paced_ )
    {
        out( ch ); bfm.if_p( ch ); bfm.hdl_if_p( hdl ); bfm.clk( clk ); bfm.rst_n( rst_n );
        ch.setTimed( delayNs, TIMED_DELAY_FIXED_INIT );
        SC_THREAD( model ); SC_THREAD( hdlThread );
    }
    void model()
    {
        do { wait( clk.posedge_event() ); } while (!rst_n);
        for (int i = 0; i < RATE_BEATS; i++) {
            F::put( out, i );
            returns.push_back( nowNs() );
            if (paced) { wait( clk.posedge_event() ); }
        }
    }
    void hdlThread() { hdlConsumer<F>( clk, rst_n, hdl, 0, 0, times, vals ); }
    void print() { std::printf( "rec %s times=%s recv=%s returns=%s\\n", name(), join( times ).c_str(), join( vals ).c_str(), join( returns ).c_str() ); }
};

// A transactional model that passes each beat from a src BFM to a dst BFM in
// one thread, so it comes back to its input on the edge its output write
// completes. With a seed the HDL sink is ready on a random half of the edges;
// without one it is always ready, and the model then comes back to its input
// on the first edge after each input transfer, a delta after the edge's own.
template <typename F>
struct relay : sc_module {
    sc_in<bool> clk, rst_n;
    typename F::chan inCh, outCh;
    typename F::in in;
    typename F::out out;
    typename F::hdl inHdl, outHdl;
    typename F::src inBfm;
    typename F::dst outBfm;
    std::vector<std::uint64_t> inTimes, times, vals;
    SC_HAS_PROCESS( relay );
    std::uint32_t seed;
    relay( sc_module_name n, std::uint32_t seed_ ) : sc_module( n ), seed( seed_ ), inCh( "inCh", "tb", BACKPRESSURE_ALLOWED ), outCh( "outCh", "tb", BACKPRESSURE_ALLOWED ),
        in( "in" ), out( "out" ), inBfm( "inBfm" ), outBfm( "outBfm" )
    {
        in( inCh ); inBfm.if_p( inCh ); inBfm.hdl_if_p( inHdl ); inBfm.clk( clk ); inBfm.rst_n( rst_n );
        out( outCh ); outBfm.if_p( outCh ); outBfm.hdl_if_p( outHdl ); outBfm.clk( clk ); outBfm.rst_n( rst_n );
        SC_THREAD( model ); SC_THREAD( producer ); SC_THREAD( consumer );
    }
    void model() { while (true) { F::put( out, F::get( in ) ); } }
    void producer() { hdlProducer<F>( clk, rst_n, inHdl, RELAY_BEATS, inTimes ); }
    void consumer() { hdlConsumer<F>( clk, rst_n, outHdl, 0, seed, times, vals ); }
    void print() { std::printf( "rec %s times=%s recv=%s\\n", name(), join( times ).c_str(), join( vals ).c_str() ); }
};

// The same relay in two threads with a channel between them, as an RTL
// output register queues one beat, into an always-ready sink.
template <typename F>
struct relayTwo : sc_module {
    sc_in<bool> clk, rst_n;
    typename F::chan inCh, outCh;
    rdy_vld_channel<wordSt> mid;
    typename F::in in;
    typename F::out out;
    rdy_vld_out<wordSt> midOut;
    rdy_vld_in<wordSt> midIn;
    typename F::hdl inHdl, outHdl;
    typename F::src inBfm;
    typename F::dst outBfm;
    std::vector<std::uint64_t> inTimes, times, vals;
    SC_HAS_PROCESS( relayTwo );
    relayTwo( sc_module_name n ) : sc_module( n ), inCh( "inCh", "tb", BACKPRESSURE_ALLOWED ), outCh( "outCh", "tb", BACKPRESSURE_ALLOWED ),
        mid( "mid", "tb", BACKPRESSURE_ALLOWED ), in( "in" ), out( "out" ), midOut( "midOut" ), midIn( "midIn" ), inBfm( "inBfm" ), outBfm( "outBfm" )
    {
        in( inCh ); inBfm.if_p( inCh ); inBfm.hdl_if_p( inHdl ); inBfm.clk( clk ); inBfm.rst_n( rst_n );
        out( outCh ); outBfm.if_p( outCh ); outBfm.hdl_if_p( outHdl ); outBfm.clk( clk ); outBfm.rst_n( rst_n );
        midOut( mid ); midIn( mid );
        SC_THREAD( input ); SC_THREAD( output ); SC_THREAD( producer ); SC_THREAD( consumer );
    }
    void input() { while (true) { wordSt v; v.w = F::get( in ); midOut->write( v ); } }
    void output() { while (true) { wordSt v; midIn->read( v ); F::put( out, v.w ); } }
    void producer() { hdlProducer<F>( clk, rst_n, inHdl, RELAY_BEATS, inTimes ); }
    void consumer() { hdlConsumer<F>( clk, rst_n, outHdl, 0, 0, times, vals ); }
    void print() { std::printf( "rec %s times=%s recv=%s\\n", name(), join( times ).c_str(), join( vals ).c_str() ); }
};

// A model with room for three beats behind a src BFM: an input thread that
// takes a beat and passes it on, and a worker that keeps two and stops. The
// HDL offers a beat on every edge.
template <typename F>
struct srcDepth : sc_module {
    sc_in<bool> clk, rst_n;
    typename F::chan ch;
    rdy_vld_channel<wordSt> q;
    typename F::in in;
    rdy_vld_out<wordSt> qo;
    rdy_vld_in<wordSt> qi;
    typename F::hdl hdl;
    typename F::src bfm;
    std::vector<std::uint64_t> times, recv;
    SC_HAS_PROCESS( srcDepth );
    srcDepth( sc_module_name n ) : sc_module( n ), ch( "ch", "tb", BACKPRESSURE_ALLOWED ), q( "q", "tb", BACKPRESSURE_ALLOWED ),
        in( "in" ), qo( "qo" ), qi( "qi" ), bfm( "bfm" )
    {
        in( ch ); qo( q ); qi( q ); bfm.if_p( ch ); bfm.hdl_if_p( hdl ); bfm.clk( clk ); bfm.rst_n( rst_n );
        SC_THREAD( input ); SC_THREAD( worker ); SC_THREAD( hdlThread );
    }
    void input() { while (true) { wordSt v; v.w = F::get( in ); qo->write( v ); } }
    void worker() { for (int i = 0; i < 2; i++) { wordSt v; qi->read( v ); recv.push_back( v.w ); } }
    void hdlThread() { hdlProducer<F>( clk, rst_n, hdl, RATE_BEATS, times ); }
    void print() { std::printf( "rec %s times=%s recv=%s\\n", name(), join( times ).c_str(), join( recv ).c_str() ); }
};

// A model that writes four beats back to back behind a dst BFM, while the
// HDL holds rdy low until the 70 ns edge. With multi, the channel carries
// four-beat bursts and the model writes two of them with writeClocked().
template <typename F>
struct dstDepth : sc_module {
    sc_in<bool> clk, rst_n;
    std::unique_ptr<typename F::chan> ch;
    typename F::out out;
    typename F::hdl hdl;
    typename F::dst bfm;
    bool multi;
    std::vector<std::uint64_t> times, vals, returns;
    SC_HAS_PROCESS( dstDepth );
    dstDepth( sc_module_name n, bool multi_ ) : sc_module( n ), out( "out" ), bfm( "bfm" ), multi( multi_ )
    {
        if constexpr (std::is_same_v<F, rvFamily>) {
            if (multi) { ch = std::make_unique<typename F::chan>( "ch", "tb", BACKPRESSURE_ALLOWED, "fixed_size", 3 * sizeof( wordSt ) + 1, "" ); }
        }
        if (!ch) { ch = std::make_unique<typename F::chan>( "ch", "tb", BACKPRESSURE_ALLOWED ); }
        out( *ch ); bfm.if_p( *ch ); bfm.hdl_if_p( hdl ); bfm.clk( clk ); bfm.rst_n( rst_n );
        SC_THREAD( model ); SC_THREAD( hdlThread );
    }
    void model()
    {
        do { wait( clk.posedge_event() ); } while (!rst_n);
        for (int i = 0; i < (multi ? 8 : 4); i++) {
            if constexpr (std::is_same_v<F, rvFamily>) {
                if (multi) { wordSt v; v.w = i; out->writeClocked( v ); returns.push_back( nowNs() ); continue; }
            }
            F::put( out, i );
            returns.push_back( nowNs() );
        }
    }
    void hdlThread() { hdlConsumer<F>( clk, rst_n, hdl, 70, 0, times, vals ); }
    void print() { std::printf( "rec %s times=%s recv=%s returns=%s\\n", name(), join( times ).c_str(), join( vals ).c_str(), join( returns ).c_str() ); }
};

SC_MODULE( rateProbe )
{
    sc_clock clk;
    sc_signal<bool> rst_n;
    srcRate<rvFamily> rvSrcTxn, rvSrcPaced;
    srcRate<axFamily> axSrcTxn, axSrcPaced;
    dstRate<rvFamily> rvDstTxn, rvDstPaced, rvDstDelay;
    dstRate<axFamily> axDstTxn, axDstPaced, axDstDelay;
    relay<rvFamily> rvRelay, rvRelayReady;
    relay<axFamily> axRelay, axRelayReady;
    relayTwo<rvFamily> rvRelayTwo;
    relayTwo<axFamily> axRelayTwo;
    srcDepth<rvFamily> rvSrcDepth;
    srcDepth<axFamily> axSrcDepth;
    dstDepth<rvFamily> rvDstDepth, rvDstMulti;
    dstDepth<axFamily> axDstDepth;

    SC_HAS_PROCESS( rateProbe );
    rateProbe( sc_module_name n )
      : sc_module( n ), clk( "clk", 10, SC_NS ),
        rvSrcTxn( "rvSrcTxn", false ), rvSrcPaced( "rvSrcPaced", true ), axSrcTxn( "axSrcTxn", false ), axSrcPaced( "axSrcPaced", true ),
        rvDstTxn( "rvDstTxn", false ), rvDstPaced( "rvDstPaced", true ), axDstTxn( "axDstTxn", false ), axDstPaced( "axDstPaced", true ),
        rvDstDelay( "rvDstDelay", false, 10 ), axDstDelay( "axDstDelay", false, 10 ),
        rvRelay( "rvRelay", 7 ), axRelay( "axRelay", 7 ), rvRelayReady( "rvRelayReady", 0 ), axRelayReady( "axRelayReady", 0 ), rvRelayTwo( "rvRelayTwo" ), axRelayTwo( "axRelayTwo" ), rvSrcDepth( "rvSrcDepth" ), axSrcDepth( "axSrcDepth" ),
        rvDstDepth( "rvDstDepth", false ), rvDstMulti( "rvDstMulti", true ), axDstDepth( "axDstDepth", false )
    {
        auto bind = [this]( auto &m ) { m.clk( clk ); m.rst_n( rst_n ); };
        bind( rvSrcTxn ); bind( rvSrcPaced ); bind( axSrcTxn ); bind( axSrcPaced );
        bind( rvDstTxn ); bind( rvDstPaced ); bind( axDstTxn ); bind( axDstPaced );
        bind( rvDstDelay ); bind( axDstDelay ); bind( rvRelayReady ); bind( axRelayReady );
        bind( rvRelayTwo ); bind( axRelayTwo );
        bind( rvRelay ); bind( axRelay ); bind( rvSrcDepth ); bind( axSrcDepth );
        bind( rvDstDepth ); bind( rvDstMulti ); bind( axDstDepth );
        SC_THREAD( run );
    }

    void run()
    {
        rst_n = 0;
        wait( 25, SC_NS );
        rst_n = 1;
        wait( 50, SC_US );
        rvSrcTxn.print(); rvSrcPaced.print(); axSrcTxn.print(); axSrcPaced.print();
        rvDstTxn.print(); rvDstPaced.print(); axDstTxn.print(); axDstPaced.print();
        rvDstDelay.print(); axDstDelay.print(); rvRelayReady.print(); axRelayReady.print();
        rvRelayTwo.print(); axRelayTwo.print();
        rvRelay.print(); axRelay.print(); rvSrcDepth.print(); axSrcDepth.print();
        rvDstDepth.print(); rvDstMulti.print(); axDstDepth.print();
        sc_stop();
    }
};

int sc_main( int, char *[] )
{
    logging::GetInstance().setDefaultVerbosity( VERBOSITY_MEDIUM );
    rateProbe p( "p" );
    sc_start();
    std::printf( "probe done\\n" );
    return 0;
}
"""

FAILURES = []
STALL = 'HDL stalled a backpressure: false interface'
LOST = 'HDL transferred a beat the BFM did not sample'
SC_STALL = 'SystemC stalled a backpressure: false producer'
BEATS = 8
IN_ORDER = list(range(BEATS))
# Reset releases at 25 ns, the BFM drives rdy from the channel on the 30 ns
# edge, and the HDL first sees it high on the 40 ns edge.
FIRST_BEAT_NS = 40
RDY_TRACE = [0, 0, 0, 0, 1, 1]
BACK_TO_BACK = [FIRST_BEAT_NS + 10 * i for i in range(BEATS)]


def check(condition, message):
    print(f"  {'PASS' if condition else 'FAIL'}: {message}")
    if not condition:
        FAILURES.append(message)


def bfmLines(output, scenario):
    return [line for line in output.splitlines() if line.startswith(f'p.{scenario}.bfm:')]


def parseRecords(output):
    def ints(s):
        return [int(v) for v in s.split(',') if v]
    return {m.group(1): {'hdl': int(m.group(2)), 'recv': ints(m.group(3)),
                         'times': ints(m.group(4)), 'rdy': ints(m.group(5))}
            for m in re.finditer(r'^src p\.(\w+) hdl=(\d+) recv=([\d,]*) times=([\d,]*) rdy=([\d,]*)$',
                                 output, re.M)}


def checkDelivered(output, records, scenario):
    rec = records.get(scenario)
    if rec is None:
        check(False, f"{scenario} printed its record")
        return None
    check(rec['hdl'] == BEATS and rec['recv'] == IN_ORDER,
          f"{scenario} delivers all {BEATS} beats in order (hdl={rec['hdl']} recv={rec['recv']})")
    check(bfmLines(output, scenario) == [], f"{scenario} logs no lost beat")
    return rec


def test_bfm_backpressure_checks():
    scLibdir = os.environ.get('SYSTEMC_LIBDIR', '')
    tmpdir = tempfile.mkdtemp(prefix='a2c_bfm_backpressure_')
    try:
        binPath = buildProbe(tmpdir, PROBE_SRC)
        if not os.path.isfile(binPath):
            check(False, f"BFM probe must build and link: {binPath}")
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

        # The stall starts on the second beat: edges at 50 and 60 ns.
        for scenario in ['rvDstNone', 'axDstNone']:
            check(bfmLines(output, scenario) == [f'p.{scenario}.bfm:{STALL} at 50 ns',
                                                  f'p.{scenario}.bfm:{STALL}, 2 clock edges in total'],
                  f"{scenario} warns once at the first stalled edge and reports two stalled edges")
            # The HDL takes the values at 40, 70, 80 and 90 ns.
            writes = re.search(rf'^dst p\.{scenario} writes=([\d,]*)$', output, re.M)
            check(writes is not None and writes.group(1) == '40,70,80,90,',
                  f"{scenario}: each write returns on the edge the HDL transfers its value "
                  f"(got {writes.group(1) if writes else None})")
        for scenario in ['rvDstAllowed', 'axDstAllowed']:
            check(bfmLines(output, scenario) == [], f"{scenario} stalls silently, backpressure is allowed")

        records = parseRecords(output)
        for family in ['rv', 'ax']:
            for name in ['Throughput', 'Pipelined', 'Comb']:
                rec = checkDelivered(output, records, f'{family}Src{name}')
                if rec:
                    check(rec['times'] == BACK_TO_BACK,
                          f"{family}Src{name} takes one beat per edge from {FIRST_BEAT_NS} ns (times={rec['times']})")
            rec = records.get(f'{family}SrcThroughput')
            if rec:
                check(rec['rdy'] == RDY_TRACE,
                      f"{family}SrcThroughput rdy on the edges from 0 ns is {RDY_TRACE} (got {rec['rdy']})")
            for name in ['AllowedGap', 'Delay15', 'Delay20', 'DelayRand', 'CombDelay', 'ResetDelay']:
                rec = checkDelivered(output, records, f'{family}Src{name}')
                if rec and name == 'AllowedGap':
                    # The reader is away for 25 ns after each beat and back
                    # before the third edge after it.
                    check(rec['times'] == [FIRST_BEAT_NS + 40 * i for i in range(BEATS)],
                          f"{family}SrcAllowedGap takes a beat only when the reader is back for it (times={rec['times']})")
                elif rec:
                    check(rec['times'][-1] > BACK_TO_BACK[-1],
                          f"{family}Src{name}: the HDL waits on rdy while the write blocks (last beat at {rec['times'][-1]} ns)")
            rec = records.get(f'{family}SrcResetDelay')
            if rec:
                check(all(t < 75 or t > 95 for t in rec['times']),
                      f"{family}SrcResetDelay transfers nothing during reset (times={rec['times']})")
            # The driver still delivers the beat it samples on the 80 ns reset
            # edge, and the HDL sends that beat again after reset.
            scenario = f'{family}SrcResetHot'
            rec = records.get(scenario)
            check(rec is not None and rec['hdl'] == BEATS and rec['times'][:4] == BACK_TO_BACK[:4]
                  and all(t < 75 or t > 95 for t in rec['times']),
                  f"{scenario} sends {BEATS} beats with reset over the 80 and 90 ns edges ({rec})")
            check(bfmLines(output, scenario) == [], f"{scenario} logs nothing (got {bfmLines(output, scenario)})")
        checkDelivered(output, records, 'rvSrcNone')
        rec = checkDelivered(output, records, 'rvSrcMulti')
        if rec:
            check(rec['times'] == BACK_TO_BACK, f"rvSrcMulti takes one beat per edge (times={rec['times']})")
        rec = checkDelivered(output, records, 'rvSrcMultiDelay')
        if rec:
            # Beats inside a transaction carry no delay, so only beats 3 and 7 wait.
            gaps = [b - a for a, b in zip(rec['times'], rec['times'][1:])]
            check(gaps[:3] == [10, 10, 10] and gaps[3] > 10,
                  f"rvSrcMultiDelay waits only after the transaction border beat (gaps={gaps})")

        # The HDL ignores rdy on a no-backpressure channel. The reader is away
        # after the 40 ns beat, so rdy is low on the 50 ns edge.
        rec = records.get('rvSrcNoneGap', {'hdl': 0, 'recv': []})
        hdl, received = rec['hdl'], len(rec['recv'])
        lines = bfmLines(output, 'rvSrcNoneGap')
        check(hdl == BEATS and received < hdl, f"rvSrcNoneGap loses beats (hdl={hdl} received={received})")
        check(lines == [f'p.rvSrcNoneGap.bfm:{SC_STALL} at 50 ns',
                        f'p.rvSrcNoneGap.bfm:{SC_STALL}, {hdl - received} clock edges in total'],
              f"rvSrcNoneGap warns of the SystemC stall at 50 ns and counts {hdl - received} stalled edges, "
              f"one per lost beat, with no lost-beat warning (got {lines})")

        # The HDL honours rdy on a no-backpressure channel, so the slow reader
        # stalls it from the 50 ns edge but loses nothing.
        for family in ['rv', 'ax']:
            scenario = f'{family}SrcNoneHonour'
            rec = records.get(scenario)
            lines = bfmLines(output, scenario)
            check(rec is not None and rec['hdl'] == BEATS and rec['recv'] == IN_ORDER,
                  f"{scenario} delivers all {BEATS} beats in order ({rec})")
            check(not any(LOST in line for line in lines), f"{scenario} logs no lost beat (got {lines})")
            check(len(lines) == 2 and lines[0] == f'p.{scenario}.bfm:{SC_STALL} at 50 ns'
                  and lines[1].startswith(f'p.{scenario}.bfm:{SC_STALL}, '),
                  f"{scenario} warns that SystemC stalled the producer, first at 50 ns (got {lines})")
        if len(FAILURES) > before:
            print(output)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


PACED = 'the model came back exactly one clock after each of'
THRESHOLD = 32
RATE_BEATS = 3 * THRESHOLD
RELAY_BEATS = 1000


def parseRateRecords(output):
    def ints(s):
        return [int(v) for v in s.split(',') if v]
    return {m.group(1): {k: ints(v) for k, v in re.findall(r'(\w+)=([\d,]*)', m.group(2))}
            for m in re.finditer(r'^rec p\.(\w+) (.*)$', output, re.M)}


def gaps(times):
    return sorted({b - a for a, b in zip(times, times[1:])})


def pacedLines(output, scenario):
    return [line for line in output.splitlines() if line.startswith(f'p.{scenario}.') and PACED in line]


def test_bfm_model_rates():
    """A BFM moves one beat per clock for a transactional model and holds no beat of its own.

    - a transactional model reader or writer moves a beat on every edge, and
      no notice is logged;
    - a model that waits on the clock between port calls moves one beat per
      two clocks, and the BFM logs one notice that names the port;
    - a transactional writer whose channel has a fixed one-clock delay logs
      no notice;
    - a transactional model between a src BFM and a dst BFM, with a sink that
      is ready on a random half of the edges or always ready, logs no notice
      on either port. Into the always-ready sink it moves one beat per two
      clocks in one thread, and one beat per clock in two threads with a
      channel between them;
    - a model with room for three beats behind a src BFM is handed exactly
      three, and a dst write() returns on the edge the HDL takes its value;
    - a multicycle rdy_vld dst BFM takes a burst from the model when the first
      beat goes on the pins, so the model's last writeClocked() of the burst
      returns before the HDL takes any of it.
    """
    scLibdir = os.environ.get('SYSTEMC_LIBDIR', '')
    tmpdir = tempfile.mkdtemp(prefix='a2c_bfm_rates_')
    try:
        binPath = buildProbe(tmpdir, RATE_PROBE_SRC)
        if not os.path.isfile(binPath):
            check(False, f"rate probe must build and link: {binPath}")
            return
        try:
            run = subprocess.run([binPath], capture_output=True, text=True, timeout=60,
                                 env=dict(os.environ, LD_LIBRARY_PATH=scLibdir))
        except subprocess.TimeoutExpired:
            check(False, "rate probe finishes within 60 s")
            return
        output = run.stdout + run.stderr
        before = len(FAILURES)
        check(run.returncode == 0 and 'probe done' in output, f"rate probe runs to completion (status {run.returncode})")
        records = parseRateRecords(output)
        inOrder = list(range(RATE_BEATS))
        for family in ['rv', 'ax']:
            for side in ['Src', 'Dst']:
                for pace, gap in [('Txn', 10), ('Paced', 20)]:
                    scenario = f'{family}{side}{pace}'
                    rec = records.get(scenario, {})
                    check(rec.get('recv') == inOrder, f"{scenario} moves all {RATE_BEATS} beats in order")
                    check(gaps(rec.get('times', [])) == [gap],
                          f"{scenario} moves one beat per {gap // 10} clock(s) (gaps {gaps(rec.get('times', []))})")
                    if side == 'Dst':
                        check(rec.get('returns') == rec.get('times'),
                              f"{scenario}: each write() returns on the edge the HDL takes its value")
                    lines = pacedLines(output, scenario)
                    if pace == 'Txn':
                        check(lines == [], f"{scenario} logs no clock-paced notice (got {lines})")
                    else:
                        check(len(lines) == 1 and lines[0].startswith(f'p.{scenario}.bfm:port p.{scenario}.ch')
                              and f'{PACED} {THRESHOLD} transfers in a row' in lines[0]
                              and 'one beat per two clocks' in lines[0]
                              and 'removing that wait restores one beat per clock' in lines[0]
                              and 'needs no change' in lines[0],
                              f"{scenario} logs one notice naming its port (got {lines})")

            # The write is stamped before its delay, so the writer is seen
            # coming back on its transfer edge, not one clock later.
            scenario = f'{family}DstDelay'
            rec = records.get(scenario, {})
            check(rec.get('recv') == inOrder and gaps(rec.get('times', [])) == [20],
                  f"{scenario}: a transactional writer with a fixed one-clock delay moves one beat per two clocks "
                  f"(gaps {gaps(rec.get('times', []))})")
            check(pacedLines(output, scenario) == [],
                  f"{scenario} logs no clock-paced notice (got {pacedLines(output, scenario)})")

            scenario = f'{family}Relay'
            rec = records.get(scenario, {})
            check(rec.get('recv') == list(range(RELAY_BEATS)), f"{scenario} moves all {RELAY_BEATS} beats in order")
            check(pacedLines(output, scenario) == [],
                  f"{scenario}: a transactional model held up by a randomly ready peer logs no notice "
                  f"(got {pacedLines(output, scenario)})")

            # Both ports move one beat per two clocks and the model comes back
            # to its input on the first edge after each input transfer, but a
            # delta after the edge's own, so only the delta rule keeps the src
            # BFM quiet.
            scenario = f'{family}RelayReady'
            rec = records.get(scenario, {})
            check(rec.get('recv') == list(range(RELAY_BEATS)) and gaps(rec.get('times', [])) == [20],
                  f"{scenario}: a one-thread relay into an always-ready sink moves one beat per two clocks "
                  f"(gaps {gaps(rec.get('times', []))})")
            check(pacedLines(output, scenario) == [],
                  f"{scenario} logs no clock-paced notice on either port (got {pacedLines(output, scenario)})")

            scenario = f'{family}RelayTwo'
            rec = records.get(scenario, {})
            check(rec.get('recv') == list(range(RELAY_BEATS)) and gaps(rec.get('times', [])) == [10],
                  f"{scenario}: the relay in two threads with a channel between moves one beat per clock "
                  f"(gaps {gaps(rec.get('times', []))})")
            check(pacedLines(output, scenario) == [],
                  f"{scenario} logs no clock-paced notice (got {pacedLines(output, scenario)})")

            scenario = f'{family}SrcDepth'
            rec = records.get(scenario, {})
            check(len(rec.get('times', [])) == 3 and rec.get('recv') == [0, 1],
                  f"{scenario}: the HDL hands exactly three beats to a model with room for three "
                  f"(handed {len(rec.get('times', []))}, worker kept {rec.get('recv')})")

            scenario = f'{family}DstDepth'
            rec = records.get(scenario, {})
            check(rec.get('times') == [80, 90, 100, 110] and rec.get('recv') == [0, 1, 2, 3]
                  and rec.get('returns') == rec.get('times'),
                  f"{scenario}: write(0) returns at 80 ns, the edge the HDL takes it, and each later write on "
                  f"its own edge ({rec})")

        rec = records.get('rvDstMulti', {})
        check(rec.get('times') == list(range(80, 160, 10)) and rec.get('recv') == list(range(8)),
              f"rvDstMulti: the HDL takes both bursts in order from 80 ns ({rec})")
        returns = rec.get('returns', [])
        # writeClocked() returns at once for a beat inside a burst and blocks
        # only on the beat that completes one.
        check(returns == [30] * 7 + [110],
              f"rvDstMulti: the first burst leaves the model at 30 ns, before the HDL takes its first beat at "
              f"80 ns, and the second on the 110 ns edge, when the HDL has taken the first (returns {returns})")
        check(pacedLines(output, 'rvDstMulti') == [], "rvDstMulti logs no clock-paced notice")
        if len(FAILURES) > before:
            print(output)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

USER_READY_PROBE_SRC = PROBE_HEADER + """
#include <cstring>

// A reader that takes control of rdy on a channel a src BFM writes, before
// elaboration ends or once the simulation runs.
SC_MODULE( userReady )
{
    sc_in<bool> clk, rst_n;
    rdy_vld_channel<wordSt> ch;
    rdy_vld_in<wordSt> in;
    rvHdl hdl;
    rdy_vld_src_bfm<wordSt, sc_bv<64>> bfm;
    bool atRun;
    SC_HAS_PROCESS( userReady );
    userReady( sc_module_name n, bool atRun_ ) : sc_module( n ), ch( "ch", "tb", BACKPRESSURE_ALLOWED ), in( "in" ), bfm( "bfm" ), atRun( atRun_ )
    {
        in( ch ); bfm.if_p( ch ); bfm.hdl_if_p( hdl ); bfm.clk( clk ); bfm.rst_n( rst_n );
        if (!atRun) { ch.enable_user_ready_control(); }
        SC_THREAD( model );
    }
    void model() { if (atRun) { in->enable_user_ready_control(); } }
};

int sc_main( int argc, char *argv[] )
{
    logging::GetInstance().setDefaultVerbosity( VERBOSITY_MEDIUM );
    sc_clock clk( "clk", 10, SC_NS );
    sc_signal<bool> rst_n;
    userReady u( "u", argc > 1 && std::strcmp( argv[1], "run" ) == 0 );
    u.clk( clk ); u.rst_n( rst_n );
    sc_start( 100, SC_NS );
    std::printf( "probe done\\n" );
    return errorCode::getExitCode();
}
"""


def test_bfm_user_ready_control():
    """A reader may not control rdy on a channel a src BFM writes.

    The BFM drives rdy from whether the reader waits in read(), so a reader
    that drives rdy itself could leave it high while away and the BFM would
    hold a beat. The channel asserts when the BFM binds to a channel whose
    reader already took control, and when the reader takes control of a
    channel the BFM writes.
    """
    scLibdir = os.environ.get('SYSTEMC_LIBDIR', '')
    tmpdir = tempfile.mkdtemp(prefix='a2c_bfm_user_ready_')
    try:
        binPath = buildProbe(tmpdir, USER_READY_PROBE_SRC)
        if not os.path.isfile(binPath):
            check(False, f"user ready probe must build and link: {binPath}")
            return
        for mode in ['elab', 'run']:
            run = subprocess.run([binPath, mode], capture_output=True, text=True, timeout=60,
                                 env=dict(os.environ, LD_LIBRARY_PATH=scLibdir))
            output = run.stdout + run.stderr
            asserts = [line for line in output.splitlines() if line.startswith('[Q_ASSERT]')]
            check(len(asserts) == 1 and asserts[0].startswith('[Q_ASSERT][u.ch] user ready control on a channel '
                                                              'a src BFM writes'),
                  f"user ready control enabled at {mode} on a channel a src BFM writes asserts once on the "
                  f"channel (got {asserts})")
            check(run.returncode != 0, f"the run that enables it at {mode} fails (status {run.returncode})")
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

if __name__ == '__main__':
    test_bfm_backpressure_checks()
    test_bfm_model_rates()
    test_bfm_user_ready_control()
    if FAILURES:
        print(f"\n  SOME TESTS FAILED ({len(FAILURES)})")
        sys.exit(1)
    print("\n  ALL TESTS PASSED!")
    sys.exit(0)
