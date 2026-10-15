#!/usr/bin/env python3
"""The rdy_vld and axi4_stream BFMs keep the HDL handshake in step with the channel.

A BFM reads the backpressure rule from the channel its if_p is bound to. The
probe drives each BFM's hdl_if signals from a SystemC thread standing in for
the RTL, and expects:

- a dst BFM on a BACKPRESSURE_NONE channel warns once when the HDL holds rdy
  low under vld, and reports the stalled edge count at end of simulation;
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

PROBE_SRC = """
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
    rvDst( sc_module_name n, channelBackpressure bp ) : sc_module( n ), ch( "ch", "tb", bp ), out( "out" ), bfm( "bfm" )
    {
        out( ch ); bfm.if_p( ch ); bfm.hdl_if_p( hdl ); bfm.clk( clk ); bfm.rst_n( rst_n );
        SC_THREAD( tb ); SC_THREAD( hdlThread );
    }
    void tb() { for (int i = 0; i < 4; i++) { wordSt v; v.w = i; out->write( v ); } }
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
    axDst( sc_module_name n, channelBackpressure bp ) : sc_module( n ), ch( "ch", "tb", bp ), out( "out" ), bfm( "bfm" )
    {
        out( ch ); bfm.if_p( ch ); bfm.hdl_if_p( hdl ); bfm.clk( clk ); bfm.rst_n( rst_n );
        SC_THREAD( tb ); SC_THREAD( hdlThread );
    }
    void tb() { for (int i = 0; i < 4; i++) { streamInfo s; s.tdata.w = i; out->sendInfo( s, std::nullopt ); } }
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
                if rec and name != 'AllowedGap':
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

        # The HDL ignores rdy on a no-backpressure channel. With the reader
        # stalled, beat two is sampled at 50 ns and the write blocks across 60 ns.
        rec = records.get('rvSrcNoneGap', {'hdl': 0, 'recv': []})
        hdl, received = rec['hdl'], len(rec['recv'])
        lines = bfmLines(output, 'rvSrcNoneGap')
        check(hdl == BEATS and received < hdl, f"rvSrcNoneGap loses beats (hdl={hdl} received={received})")
        check(lines == [f'p.rvSrcNoneGap.bfm:{SC_STALL} at 60 ns',
                        f'p.rvSrcNoneGap.bfm:{SC_STALL}, {hdl - received} clock edges in total'],
              f"rvSrcNoneGap warns of the SystemC stall at 60 ns and counts {hdl - received} stalled edges, "
              f"one per lost beat, with no lost-beat warning (got {lines})")

        # The HDL honours rdy on a no-backpressure channel, so the slow reader
        # stalls it from the 60 ns edge but loses nothing.
        for family in ['rv', 'ax']:
            scenario = f'{family}SrcNoneHonour'
            rec = records.get(scenario)
            lines = bfmLines(output, scenario)
            check(rec is not None and rec['hdl'] == BEATS and rec['recv'] == IN_ORDER,
                  f"{scenario} delivers all {BEATS} beats in order ({rec})")
            check(not any(LOST in line for line in lines), f"{scenario} logs no lost beat (got {lines})")
            check(len(lines) == 2 and lines[0] == f'p.{scenario}.bfm:{SC_STALL} at 60 ns'
                  and lines[1].startswith(f'p.{scenario}.bfm:{SC_STALL}, '),
                  f"{scenario} warns that SystemC stalled the producer, first at 60 ns (got {lines})")
        if len(FAILURES) > before:
            print(output)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == '__main__':
    test_bfm_backpressure_checks()
    if FAILURES:
        print(f"\n  SOME TESTS FAILED ({len(FAILURES)})")
        sys.exit(1)
    print("\n  ALL TESTS PASSED!")
    sys.exit(0)
