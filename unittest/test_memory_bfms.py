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

In UVM Mode B, memory_dst_bfm takes a credit pin and drives a held pin
(setModelCredit). The probe's creditor raises the credit by one, 100 ps after
a rising edge as a UVM agent drives it, once per access, each later than the
BFM would otherwise go. Every access must reach the pins only on an edge after
its credit came, held must be high while the BFM waits and low once it has
gone, and the reads must still return the words written. With credit for six
of the eight accesses, the seventh must wait to the end, with one log line at
the end of the simulation that names it. Without setModelCredit the BFM runs
as in the first scenarios.

The memory_dst_bfms of a UVM SystemC wrapper share a memory_write_order
(setWriteOrder) when the run holds the model alone. The probe gives three
BFMs one stub memory that serves a read and a write sampled at the same edge
read-first, as the UVM memory agent does, and runs each scenario of
orderProbe with the order and without it. With the order, an access is
sampled after every earlier write on another port, and a write no earlier
than every earlier read on another port, in the model's program order as its
channel stamped it: a read after such a write gets the written word (order,
tri2), a write after a read held by an earlier write lands on the read's
edge, not before it (overtake), a read waits only for the writes issued
before it (stream, where a write stream does not hold it to the end), and two
threads ready in one phase follow the kernel's order (threads). An access
still waiting at the end is logged with the write it waits for (stuck).
x2Probe's stub samples each port at the falling edge of its port's clock,
as the UVM memory agent does. It checks the two ways a port can leave its
requester's program order: a write relayed by a producer-shape
memory_port_thunker is stamped in the requester's thread, so a later read on
another port gets its word (thunk), and an access behind an access on a port
with a slower clock reaches the pins only after that access was sampled (xclk,
rw, wr). Released by the other clock's edge, it waits for its own rising edge
before it drives, so it is on the pins at its own falling edge (rw, wr, where
the release falls in its clock's low phase).
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
#include "memory_port_thunker.h"
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <format>
#include <map>
#include <memory>
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
    sc_signal<sc_bv<32>> credit;
    sc_signal<bool> held;
    // Credits given, when each came, and whether held was high at any point
    // while an access waited and low after the last grant's access.
    unsigned grants = 0;
    std::vector<sc_time> grantAt;
    bool heldSeen = false;

    SC_HAS_PROCESS( dstProbe );
    dstProbe( sc_module_name n, bool uvmTiming_ )
      : sc_module( n ), ch( "ch", "tb" ), out( "out" ), bfm( "bfm" ), uvmTiming( uvmTiming_ )
    {
        out( ch ); bfm.if_p( ch ); bfm.hdl_if_p( hdl ); bfm.clk( clk ); bfm.rst_n( rst_n );
        SC_THREAD( requester ); SC_THREAD( memory );
    }
    void useCredit( unsigned n )
    {
        grants = n;
        bfm.setModelCredit( &credit, &held );
        SC_THREAD( creditor );
    }
    // Credit k comes 100 ps after the rising edge at 60 + 30 k ns, two
    // edges later than the BFM's own pace.
    void creditor()
    {
        for (unsigned k = 0; k < grants; k++) {
            wait( sc_time( 60 + 30 * k, SC_NS ) + sc_time( 100, SC_PS ) - sc_time_stamp() );
            if (held.read()) { heldSeen = true; }
            grantAt.push_back( sc_time_stamp() );
            credit = sc_bv<32>( k + 1 );
        }
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

// Three BFMs, a, b and c, in front of one stub memory that serves the
// accesses sampled at one edge read-first, as the UVM memory agent does. Each
// scenario's model threads start at 32 ns; a thread named "later" starts one
// delta after the others, so its accesses come later in program order.
//   order:    one thread writes 0x55 to 5 through a and reads 5 through b;
//             at 102 ns one reads 6 through b and a later one writes 0x66 to
//             6 through a.
//   stream:   one thread writes 0x100 + i to i through a for i 0..9, back to
//             back; another reads 8 through b at 52 ns.
//   tri2:     one thread writes 0x11 to 1 through a, 0x77 to 7 through b,
//             then reads 7 through a.
//   overtake: one thread writes 0x55 to 5 through c and reads 6 through b; a
//             later one writes 0x66 to 6 through a.
//   threads:  in one phase, one thread writes 0x33 to 3 through a and reads 4
//             through b, and another writes 0x44 to 4 through c.
//   stuck:    b's BFM clock stops at 36 ns and the memory ignores b, so b's
//             write of 0x22 to 2 is never sampled; one thread makes that
//             write and then reads 2 through a.
SC_MODULE( orderProbe )
{
    sc_in<bool> clk, rst_n;
    memory_channel<wordSt, wordSt> aCh, bCh, cCh;
    memory_out<wordSt, wordSt> aOut, bOut, cOut;
    hdlIf aHdl, bHdl, cHdl;
    memory_dst_bfm<wordSt, wordSt, sc_bv<64>, sc_bv<64>> aBfm, bBfm, cBfm;
    memory_write_order order;
    sc_signal<bool> bClk;
    std::map<std::uint64_t, std::uint64_t> mem;
    std::string scenario, accesses, reads;

    SC_HAS_PROCESS( orderProbe );
    orderProbe( sc_module_name n, const std::string &scenario_, bool ordered )
      : sc_module( n ), aCh( "aCh", "tb" ), bCh( "bCh", "tb" ), cCh( "cCh", "tb" ), aOut( "aOut" ), bOut( "bOut" ),
        cOut( "cOut" ), aBfm( "aBfm" ), bBfm( "bBfm" ), cBfm( "cBfm" ), scenario( scenario_ )
    {
        aOut( aCh ); aBfm.if_p( aCh ); aBfm.hdl_if_p( aHdl ); aBfm.clk( clk ); aBfm.rst_n( rst_n );
        bOut( bCh ); bBfm.if_p( bCh ); bBfm.hdl_if_p( bHdl ); bBfm.rst_n( rst_n );
        if (scenario == "stuck") { bBfm.clk( bClk ); } else { bBfm.clk( clk ); }
        cOut( cCh ); cBfm.if_p( cCh ); cBfm.hdl_if_p( cHdl ); cBfm.clk( clk ); cBfm.rst_n( rst_n );
        if (ordered) { aBfm.setWriteOrder( &order ); bBfm.setWriteOrder( &order ); cBfm.setWriteOrder( &order ); }
        SC_THREAD( first ); SC_THREAD( second ); SC_THREAD( later ); SC_THREAD( memory );
        SC_METHOD( stoppingClock ); sensitive << clk;
    }
    void stoppingClock() { bClk = sc_time_stamp() < sc_time( 36, SC_NS ) && clk.read(); }
    void rd( memory_out<wordSt, wordSt> &p, std::uint64_t addr )
    {
        wordSt a, d;
        a.w = addr;
        p->request( false, a, d );
        reads += std::format( "{}0x{:x}", reads.empty() ? "" : ",", d.w );
    }
    void wr( memory_out<wordSt, wordSt> &p, std::uint64_t addr, std::uint64_t word )
    {
        wordSt a, d;
        a.w = addr;
        d.w = word;
        p->request( true, a, d );
    }
    void first()
    {
        wait( 32, SC_NS );
        if (scenario == "order") { wr( aOut, 5, 0x55 ); rd( bOut, 5 ); }
        if (scenario == "stream") { for (std::uint64_t i = 0; i < 10; i++) { wr( aOut, i, 0x100 + i ); } }
        if (scenario == "tri2") { wr( aOut, 1, 0x11 ); wr( bOut, 7, 0x77 ); rd( aOut, 7 ); }
        if (scenario == "overtake") { wr( cOut, 5, 0x55 ); rd( bOut, 6 ); }
        if (scenario == "threads") { wr( aOut, 3, 0x33 ); rd( bOut, 4 ); }
        if (scenario == "stuck") { wr( bOut, 2, 0x22 ); rd( aOut, 2 ); }
    }
    void second()
    {
        wait( 32, SC_NS );
        if (scenario == "order") { wait( 70, SC_NS ); rd( bOut, 6 ); }
        if (scenario == "stream") { wait( 20, SC_NS ); rd( bOut, 8 ); }
        if (scenario == "threads") { wr( cOut, 4, 0x44 ); }
    }
    void later()
    {
        wait( 32, SC_NS );
        wait( SC_ZERO_TIME );
        if (scenario == "order") { wait( 70, SC_NS ); wait( SC_ZERO_TIME ); wr( aOut, 6, 0x66 ); }
        if (scenario == "overtake") { wr( aOut, 6, 0x66 ); }
    }
    void sample( hdlIf &h, char port, bool writes, std::uint64_t ns, std::vector<std::pair<hdlIf *, std::uint64_t>> &words )
    {
        if (!h.enable.read() || h.wr_en.read() != writes) { return; }
        std::uint64_t addr = h.addr.read().to_uint64();
        if (writes) { mem[addr] = h.write_data.read().to_uint64(); } else { words.push_back( { &h, mem[addr] } ); }
        accesses += std::format( "{}{}{}{}@{}", accesses.empty() ? "" : ",", port, writes ? 'w' : 'r', addr, ns );
    }
    void memory()
    {
        while (true) {
            wait( clk.posedge_event() );
            std::uint64_t ns = (std::uint64_t)(sc_time_stamp() / sc_time( 1, SC_NS ));
            std::vector<std::pair<hdlIf *, std::uint64_t>> words;
            for (bool writes : { false, true }) {
                sample( aHdl, 'a', writes, ns, words );
                if (scenario != "stuck") { sample( bHdl, 'b', writes, ns, words ); }
                sample( cHdl, 'c', writes, ns, words );
            }
            if (!words.empty()) {
                wait( 100, SC_PS );
                for (auto [h, word] : words) { h->read_data = sc_bv<64>( word ); }
            }
        }
    }
};

// Two BFMs, a on clk and b on clk2 or clk, in front of one stub memory that
// samples each port at the falling edge of its port's clock, as the UVM memory
// agent does, and serves the reads before the writes it samples at one edge.
// clk2 has a 40 ns period and rises at clk2Start, 5 ns for x2_* and 7 ns for
// n2_*, then every 40 ns.
//   thunk: b on clk; a's requester sits behind a producer-shape
//          memory_port_thunker; one thread writes 0x77 to 7 through it and
//          then reads 7 through b.
//   xclk, rw: one thread reads 7 through b and a later one writes 0x77 to 7
//          through a.
//   wr:    one thread writes 0x77 to 7 through b and then reads 7 through a.
SC_MODULE( x2Probe )
{
    sc_in<bool> clk, rst_n;
    sc_clock clk2;
    memory_channel<wordSt, wordSt> aCh, bCh;
    memory_out<wordSt, wordSt> bOut, childA;
    hdlIf aHdl, bHdl;
    memory_dst_bfm<wordSt, wordSt, sc_bv<64>, sc_bv<64>> aBfm, bBfm;
    std::unique_ptr<memory_port_thunker<wordSt, wordSt, wordSt, wordSt, true, true>> thunker;
    memory_write_order order;
    std::map<std::uint64_t, std::uint64_t> mem;
    std::string scenario, accesses, reads;

    SC_HAS_PROCESS( x2Probe );
    x2Probe( sc_module_name n, const std::string &scenario_, bool ordered, int clk2Start )
      : sc_module( n ), clk2( "clk2", 40, SC_NS, 0.5, clk2Start, SC_NS, true ), aCh( "aCh", "tb" ), bCh( "bCh", "tb" ),
        bOut( "bOut" ), childA( "childA" ), aBfm( "aBfm" ), bBfm( "bBfm" ), scenario( scenario_ )
    {
        if (scenario == "thunk") {
            thunker = std::make_unique<memory_port_thunker<wordSt, wordSt, wordSt, wordSt, true, true>>( "thunker", aCh, childA, "tb" );
        } else {
            childA( aCh );
        }
        aBfm.if_p( aCh ); aBfm.hdl_if_p( aHdl ); aBfm.clk( clk ); aBfm.rst_n( rst_n );
        bOut( bCh ); bBfm.if_p( bCh ); bBfm.hdl_if_p( bHdl ); bBfm.rst_n( rst_n );
        if (scenario == "thunk") { bBfm.clk( clk ); } else { bBfm.clk( clk2 ); }
        if (ordered) { aBfm.setWriteOrder( &order ); bBfm.setWriteOrder( &order ); }
        SC_THREAD( first ); SC_THREAD( later ); SC_THREAD( memA ); SC_THREAD( memB );
    }
    void rd( memory_out<wordSt, wordSt> &p, std::uint64_t addr )
    {
        wordSt a, d;
        a.w = addr;
        p->request( false, a, d );
        reads += std::format( "{}0x{:x}", reads.empty() ? "" : ",", d.w );
    }
    void wr( memory_out<wordSt, wordSt> &p, std::uint64_t addr, std::uint64_t word )
    {
        wordSt a, d;
        a.w = addr;
        d.w = word;
        p->request( true, a, d );
    }
    void first()
    {
        wait( 32, SC_NS );
        if (scenario == "thunk") { wr( childA, 7, 0x77 ); rd( bOut, 7 ); }
        if (scenario == "xclk" || scenario == "rw") { rd( bOut, 7 ); }
        if (scenario == "wr") { wr( bOut, 7, 0x77 ); rd( childA, 7 ); }
    }
    void later()
    {
        wait( 32, SC_NS );
        wait( SC_ZERO_TIME );
        if (scenario == "xclk" || scenario == "rw") { wr( childA, 7, 0x77 ); }
    }
    void serve( std::vector<std::pair<hdlIf *, char>> ports )
    {
        std::uint64_t ns = (std::uint64_t)(sc_time_stamp() / sc_time( 1, SC_NS ));
        std::vector<std::pair<hdlIf *, std::uint64_t>> words;
        for (bool writes : { false, true }) {
            for (auto [h, port] : ports) {
                if (!h->enable.read() || h->wr_en.read() != writes) { continue; }
                std::uint64_t addr = h->addr.read().to_uint64();
                if (writes) { mem[addr] = h->write_data.read().to_uint64(); } else { words.push_back( { h, mem[addr] } ); }
                accesses += std::format( "{}{}{}{}@{}", accesses.empty() ? "" : ",", port, writes ? 'w' : 'r', addr, ns );
            }
        }
        if (!words.empty()) {
            wait( 100, SC_PS );
            for (auto [h, word] : words) { h->read_data = sc_bv<64>( word ); }
        }
    }
    void memA()
    {
        while (true) {
            wait( clk.negedge_event() );
            if (scenario == "thunk") { serve( { { &aHdl, 'a' }, { &bHdl, 'b' } } ); } else { serve( { { &aHdl, 'a' } } ); }
        }
    }
    void memB()
    {
        if (scenario == "thunk") { return; }
        while (true) {
            wait( clk2.negedge_event() );
            serve( { { &bHdl, 'b' } } );
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
    if (scenario == "dst_rtl" || scenario == "dst_uvm" || scenario == "dst_credit" || scenario == "dst_credit_short") {
        dstProbe p( "p", scenario != "dst_rtl" );
        p.clk( clk ); p.rst_n( rst_n );
        bool credited = scenario.starts_with( "dst_credit" );
        if (credited) { p.useCredit( scenario == "dst_credit" ? 8 : 6 ); }
        sc_start( 1, SC_US );
        if (credited) {
            bool afterGrant = p.accessNs.size() <= p.grantAt.size();
            for (std::size_t i = 0; i < p.accessNs.size() && i < p.grantAt.size(); i++) {
                if (sc_time( p.accessNs[i], SC_NS ) <= p.grantAt[i]) { afterGrant = false; }
            }
            std::printf( "accesses=%zu\\nafter_grant=%d\\nheld_seen=%d\\nheld_end=%d\\n", p.accessNs.size(), afterGrant,
                         p.heldSeen, p.held.read() );
            sc_stop();
        }
        std::string edges, gaps;
        for (std::size_t i = 0; i < p.accessNs.size(); i++) {
            edges += std::format( "{}{}", i ? "," : "", p.accessNs[i] );
            if (i) { gaps += std::format( "{}{}", i > 1 ? "," : "", p.accessNs[i] - p.accessNs[i - 1] ); }
        }
        std::printf( "done=%d\\nreads=%s\\nedges=%s\\ngaps=%s\\nresumes_on_posedge=%d\\n", p.done, p.reads.c_str(),
                     edges.c_str(), gaps.c_str(), p.resumesOnPosedge );
    } else if (scenario.starts_with( "x2_" ) || scenario.starts_with( "n2_" )) {
        // x2_<case>, n2_<case>, or either with _off
        bool ordered = !scenario.ends_with( "_off" );
        std::string name = scenario.substr( 3, ordered ? std::string::npos : scenario.size() - 7 );
        x2Probe p( "p", name, ordered, scenario.starts_with( "n2_" ) ? 7 : 5 );
        p.clk( clk ); p.rst_n( rst_n );
        sc_start( 1, SC_US );
        std::printf( "accesses=%s\\nreads=%s\\n", p.accesses.c_str(), p.reads.c_str() );
        sc_stop();
    } else if (scenario.starts_with( "order_" )) {
        // order_<case> or order_<case>_off
        bool ordered = !scenario.ends_with( "_off" );
        std::string name = scenario.substr( 6, ordered ? std::string::npos : scenario.size() - 10 );
        orderProbe p( "p", name, ordered );
        p.clk( clk ); p.rst_n( rst_n );
        sc_start( 1, SC_US );
        std::printf( "accesses=%s\\nreads=%s\\n", p.accesses.c_str(), p.reads.c_str() );
        sc_stop();
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
# Per scenario of orderProbe and x2Probe, with the write order and without it
# (_off).
# threads holds the order the Accellera kernel runs two threads ready in one
# phase: it stamps c's write first.
ORDER_CASES = {
    'order_order': ('aw5@40,br5@50,br6@110,aw6@110', '0x55,0x0'),
    'order_order_off': ('br5@40,aw5@40,br6@110,aw6@110', '0x0,0x0'),
    'order_stream': ('aw0@40,aw1@50,aw2@60,aw3@70,aw4@80,br8@90,aw5@90,aw6@100,aw7@110,aw8@120,aw9@130', '0x0'),
    'order_stream_off': ('aw0@40,aw1@50,br8@60,aw2@60,aw3@70,aw4@80,aw5@90,aw6@100,aw7@110,aw8@120,aw9@130', '0x0'),
    'order_tri2': ('aw1@40,bw7@50,ar7@60', '0x77'),
    'order_tri2_off': ('aw1@40,bw7@40,ar7@50', '0x77'),
    'order_overtake': ('cw5@40,br6@50,aw6@50', '0x0'),
    'order_overtake_off': ('br6@40,aw6@40,cw5@40', '0x0'),
    'order_threads': ('cw4@40,aw3@50,br4@60', '0x44'),
    'order_threads_off': ('br4@40,aw3@40,cw4@40', '0x0'),
    'order_stuck': ('', ''),
    'order_stuck_off': ('ar2@40', '0x0'),
    'x2_thunk': ('aw7@35,br7@45', '0x77'),
    'x2_thunk_off': ('br7@35,aw7@35', '0x0'),
    'x2_xclk': ('br7@65,aw7@95', '0x0'),
    'x2_xclk_off': ('aw7@35,br7@65', '0x77'),
    'n2_rw': ('br7@67,aw7@95', '0x0'),
    'n2_rw_off': ('aw7@35,br7@67', '0x77'),
    'n2_wr': ('bw7@67,ar7@95', '0x77'),
    'n2_wr_off': ('ar7@35,bw7@67', '0x0'),
}
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

        outputs['dst_credit'] = output = runScenario(binPath, 'dst_credit')
        check(field(output, 'done') == '1' and field(output, 'reads') == '0x102,0x100,0x103,0x101',
              f"dst_credit: the requester finishes and each read returns the word written to its address "
              f"(reads={field(output, 'reads')})")
        check(field(output, 'accesses') == '8' and field(output, 'after_grant') == '1',
              f"dst_credit: each access reaches the pins on an edge after its credit came (edges={field(output, 'edges')})")
        check(field(output, 'held_seen') == '1' and field(output, 'held_end') == '0',
              "dst_credit: held is high while an access waits and low once the last has gone")
        check(bfmLines(output) == [], f"dst_credit logs nothing (got {bfmLines(output)})")

        outputs['dst_credit_short'] = output = runScenario(binPath, 'dst_credit_short')
        check(field(output, 'done') == '0' and field(output, 'accesses') == '6' and field(output, 'after_grant') == '1',
              f"dst_credit_short: six accesses go, each after its credit, and the seventh waits "
              f"(accesses={field(output, 'accesses')})")
        check(field(output, 'held_end') == '1', "dst_credit_short: held stays high while the seventh access waits")
        lines = bfmLines(output)
        check(len(lines) == 1 and re.fullmatch(r"p\.bfm:the model's access 7 \(read 0x3\) waited for credit from \S+ ns "
                                               r"to the end, with 6 issued and credit 6: the DUT lane never made access 7", lines[0]) is not None,
              f"dst_credit_short: the BFM logs the waiting access once at the end (got {lines})")

        for scenario, (accesses, reads) in ORDER_CASES.items():
            outputs[scenario] = output = runScenario(binPath, scenario)
            check(field(output, 'accesses') == accesses and field(output, 'reads') == reads,
                  f"{scenario}: the accesses reach the pins as {accesses} and the reads return {reads} "
                  f"(accesses={field(output, 'accesses')}, reads={field(output, 'reads')})")

        lines = [line for line in outputs['order_stuck'].splitlines() if line.startswith('p.aBfm:')]
        check(len(lines) == 1 and re.fullmatch(r"p\.aBfm:the model's access 1 \(read 0x2\) waited for the write order from 32 ns "
                                               r"to the end, behind the earlier write on p\.bBfm", lines[0]) is not None,
              f"order_stuck: a's BFM logs its read waiting at the end behind b's write (got {lines})")

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
