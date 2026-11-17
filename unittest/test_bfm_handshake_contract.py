#!/usr/bin/env python3
"""The ack-style, APB and AXI BFMs hold no transfer of their own, and the
contract checks on them fire.

The probe drives each BFM's hdl_if signals from a SystemC thread standing in
for the RTL, with bfmContractCheck::toUvm set as in a UVM run, and expects:

- a push_ack, req_ack, pop_ack or notify_ack src BFM whose HDL requester
  holds its request until the ack logs nothing. One that drops its request,
  or changes its data, while the model is still in its call logs the break
  `HDL dropped or changed a request` and queues it for the testbench;
- with a model that answers in zero time, each of those src BFMs acks a
  request in its first clock, one request per clock, as a destination
  whose ack follows the request combinationally does, with the rdata on
  req_ack and pop_ack;
- an apb src BFM raises PREADY on a posted write only after the model's
  reqReceive() has taken it, and logs the same break when the HDL master
  ends an access before PREADY. With a model that answers in zero time it
  raises PREADY in the first access phase, as a slave with no wait states
  does, for writes and reads back to back;
- an apb dst BFM takes a posted write at the sample point before the edge
  the HDL completes it, so the model's next request() returns there and not
  before;
- a push_ack, notify_ack, req_ack or pop_ack dst BFM completes the model's
  call at the sample point before the edge the HDL takes the request, with
  the rdata of its ack, one request per clock on push_ack and notify_ack and
  one per two clocks on req_ack and pop_ack, whose BFMs drop the request for
  a clock between requests. A timed delay on the completion that outlasts
  the edge still drops the request there, and an ack that falls after the
  sample point logs `HDL lowered ready` and keeps the request on the pins
  until the HDL takes it, or under a reset asserted then logs nothing;
- on every axi_read and axi_write channel, a beat the HDL sends reaches the
  model on the edge the HDL transfers it, and a model send returns at the
  sample point before the edge the HDL takes the beat, whether the model or
  the HDL is slow;
- a model that reads and then writes in one thread, between a rdy_vld or
  axi4_stream src BFM and dst BFM, moves one beat per clock into an
  always-ready sink, as RTL whose input ready follows its output ready does.
  Into a sink ready on odd clocks its input ready follows the sink's ready
  once the model holds a beat. An axi_read slave model that takes an address
  and sends its one R beat takes an address on every clock;
- a dst BFM whose HDL lowers ready after the model's send completed at the
  sample point logs `HDL lowered ready` and queues it, outside reset, and
  still delivers the beat; under a reset that asserts in that window it logs
  nothing and delivers the beat after reset;
- a model reader that waits on the clock between reads is logged once with a
  fix-the-model message and never queued, so it does not fail a UVM run.
  Behind a rdy_vld src BFM such a reader leaves rdy low for one clock after
  each transfer, the hold Mode B reports as A2C_MODEL_THROTTLE. A writer that
  waits on the clock between writes moves one beat per clock behind a dst
  BFM and is not reported, and a model that a memory BFM wakes at each edge
  is paced by the HDL and is not reported.
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
#include "pop_ack_bfm.h"
#include "notify_ack_bfm.h"
#include "apb_bfm.h"
#include "axi_read_bfm.h"
#include "axi_write_bfm.h"
#include "memory_bfm.h"
#include "rdy_vld_bfm.h"
#include "axi4_stream_bfm.h"
#include <cstdint>
#include <cstdio>
#include <deque>
#include <format>
#include <string>
#include <vector>

extern "C" const char *a2c_bfm_contract_break(void);

template <int W>
struct bitsSt {
    std::uint64_t w = 0;
    static constexpr std::uint16_t _bitWidth = W;
    static constexpr std::uint16_t _byteWidth = (W + 7) / 8;
    typedef std::uint64_t _packedSt;
    static const char* getValueType() { return ""; }
    std::uint64_t getStructValue() const { return w; }
    std::uint64_t _getAddress() const { return w; }
    std::uint64_t _getData() const { return w; }
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

std::string ns( void ) { return std::format( "{}", sc_time_stamp().value() / 1000 ); }
std::string join( const std::vector<std::string> &v )
{
    std::string s;
    for (auto &e : v) { s += e + ","; }
    return s;
}

// The HDL requester of an ack-style port: 0 holds the request until the ack,
// 1 drops it one edge after raising it, 2 changes its data one edge after
// raising it. The model takes three clocks to ack, so both breaks fall inside
// its call.
template <typename HDL>
void ackRequester( sc_in<bool> &clk, sc_in<bool> &rst_n, sc_signal<bool> &req, sc_signal<bool> &ack,
                   int mode, HDL setData )
{
    do { wait( clk.posedge_event() ); } while (!rst_n);
    for (int k = 0; k < 2; k++) {
        req = 1;
        setData( k );
        wait( clk.posedge_event() );
        if (mode == 1) { req = 0; }
        if (mode == 2) { setData( k + 100 ); }
        do { wait( clk.posedge_event() ); } while (!ack);
        req = 0;
        wait( clk.posedge_event() );
    }
}

SC_MODULE( pushSrc )
{
    sc_in<bool> clk, rst_n;
    push_ack_channel<wordSt> ch;
    push_ack_in<wordSt> in;
    push_ack_hdl_if<bv> hdl;
    push_ack_src_bfm<wordSt, bv> bfm;
    int mode;
    SC_HAS_PROCESS( pushSrc );
    pushSrc( sc_module_name n, int m ) : sc_module( n ), ch( "ch", "tb" ), in( "in" ), bfm( "bfm" ), mode( m )
    {
        in( ch ); bfm.if_p( ch ); bfm.hdl_if_p( hdl ); bfm.clk( clk ); bfm.rst_n( rst_n );
        SC_THREAD( model ); SC_THREAD( hdlThread );
    }
    void model() { while (true) { wordSt v; in->pushReceive( v ); wait( 30, SC_NS ); in->ack(); } }
    void hdlThread() { ackRequester( clk, rst_n, hdl.push, hdl.ack, mode, [this]( int k ) { hdl.data = bv( k ); } ); }
};

SC_MODULE( reqSrc )
{
    sc_in<bool> clk, rst_n;
    req_ack_channel<wordSt, wordSt> ch;
    req_ack_in<wordSt, wordSt> in;
    req_ack_hdl_if<bv, bv> hdl;
    req_ack_src_bfm<wordSt, wordSt, bv, bv> bfm;
    int mode;
    SC_HAS_PROCESS( reqSrc );
    reqSrc( sc_module_name n, int m ) : sc_module( n ), ch( "ch", "tb" ), in( "in" ), bfm( "bfm" ), mode( m )
    {
        in( ch ); bfm.if_p( ch ); bfm.hdl_if_p( hdl ); bfm.clk( clk ); bfm.rst_n( rst_n );
        SC_THREAD( model ); SC_THREAD( hdlThread );
    }
    void model() { while (true) { wordSt r; in->reqReceive( r ); wait( 30, SC_NS ); in->ack( r ); } }
    void hdlThread() { ackRequester( clk, rst_n, hdl.req, hdl.ack, mode, [this]( int k ) { hdl.data = bv( k ); } ); }
};

SC_MODULE( popSrc )
{
    sc_in<bool> clk, rst_n;
    pop_ack_channel<wordSt> ch;
    pop_ack_in<wordSt> in;
    pop_ack_hdl_if<bv> hdl;
    pop_ack_src_bfm<wordSt, bv> bfm;
    int mode;
    SC_HAS_PROCESS( popSrc );
    popSrc( sc_module_name n, int m ) : sc_module( n ), ch( "ch", "tb" ), in( "in" ), bfm( "bfm" ), mode( m )
    {
        in( ch ); bfm.if_p( ch ); bfm.hdl_if_p( hdl ); bfm.clk( clk ); bfm.rst_n( rst_n );
        SC_THREAD( model ); SC_THREAD( hdlThread );
    }
    void model() { while (true) { in->popReceive(); wait( 30, SC_NS ); wordSt v; in->ack( v ); } }
    void hdlThread() { ackRequester( clk, rst_n, hdl.pop, hdl.ack, mode, []( int ) {} ); }
};

SC_MODULE( notifySrc )
{
    sc_in<bool> clk, rst_n;
    notify_ack_channel<bool> ch;
    notify_ack_in<bool> in;
    notify_ack_hdl_if<bool> hdl;
    notify_ack_src_bfm<bool> bfm;
    int mode;
    SC_HAS_PROCESS( notifySrc );
    notifySrc( sc_module_name n, int m ) : sc_module( n ), ch( "ch", "tb" ), in( "in" ), bfm( "bfm" ), mode( m )
    {
        in( ch ); bfm.if_p( ch ); bfm.hdl_if_p( hdl ); bfm.clk( clk ); bfm.rst_n( rst_n );
        SC_THREAD( model ); SC_THREAD( hdlThread );
    }
    void model() { while (true) { in->waitNotify(); wait( 30, SC_NS ); in->ack(); } }
    void hdlThread() { ackRequester( clk, rst_n, hdl.notify, hdl.ack, mode, []( int ) {} ); }
};

// An HDL APB master in front of apb_src_bfm. The model takes each write
// 50 ns after it is posted. With withdraw the master issues a read and ends
// its access after one access-phase edge, while the model is still in its
// call.
SC_MODULE( apbSrc )
{
    sc_in<bool> clk, rst_n;
    apb_channel<wordSt, wordSt> ch;
    apb_in<wordSt, wordSt> in;
    apb_hdl_if<bv, bv> hdl;
    apb_src_bfm<wordSt, wordSt, bv, bv> bfm;
    bool withdraw;
    std::vector<std::string> takeNs, doneNs;
    SC_HAS_PROCESS( apbSrc );
    apbSrc( sc_module_name n, bool w ) : sc_module( n ), ch( "ch", "tb" ), in( "in" ), bfm( "bfm" ), withdraw( w )
    {
        in( ch ); bfm.if_p( ch ); bfm.hdl_if_p( hdl ); bfm.clk( clk ); bfm.rst_n( rst_n );
        SC_THREAD( model ); SC_THREAD( master );
    }
    void model()
    {
        while (true) {
            bool isWrite; wordSt a, d;
            while (in->isNotActive()) { wait( 10, SC_NS ); }
            wait( 50, SC_NS );
            in->reqReceive( isWrite, a, d );
            takeNs.push_back( ns() );
            if (!isWrite) { wait( 30, SC_NS ); in->complete( d ); }
        }
    }
    void master()
    {
        do { wait( clk.posedge_event() ); } while (!rst_n);
        for (int k = 0; k < 2; k++) {
            hdl.psel = 1; hdl.pwrite = !withdraw; hdl.paddr = bv( 4 * k ); hdl.pwdata = bv( k );
            wait( clk.posedge_event() );
            hdl.penable = 1;
            if (withdraw) {
                wait( clk.posedge_event() );
                wait( clk.posedge_event() );
                hdl.psel = 0; hdl.penable = 0;
                do { wait( clk.posedge_event() ); } while (!hdl.pready);
                wait( clk.posedge_event() );
                continue;
            }
            do { wait( clk.posedge_event() ); } while (!hdl.pready);
            doneNs.push_back( ns() );
            hdl.psel = 0; hdl.penable = 0;
            wait( clk.posedge_event() );
        }
    }
};

// An HDL requester of an ack-style port that drives as the UVM src driver
// does, 100 ps after the rising edge, and samples at the falling edge: four
// requests back to back. It records, per request, the sample point of its
// first clock and the one that saw ack. The model answers in zero time.
template <typename SET, typename GET>
void sameClockRequester( sc_in<bool> &clk, sc_in<bool> &rst_n, sc_signal<bool> &req, sc_signal<bool> &ack,
                         SET setData, GET getRdata, std::vector<std::string> &firstNs, std::vector<std::string> &doneNs,
                         std::vector<std::string> &rdata )
{
    const sc_time skew( 100, SC_PS );
    do { wait( clk.posedge_event() ); } while (!rst_n);
    for (int k = 0; k < 4; k++) {
        wait( skew );
        req = 1;
        setData( k );
        wait( clk.negedge_event() );
        firstNs.push_back( ns() );
        while (!ack) {
            wait( clk.negedge_event() );
        }
        doneNs.push_back( ns() );
        rdata.push_back( getRdata() );
        wait( clk.posedge_event() );
    }
    wait( skew );
    req = 0;
}

template <typename CH, typename IN, typename HDL_IF, typename BFM>
struct sameClock : public sc_module
{
    sc_in<bool> clk, rst_n;
    CH ch;
    IN in;
    HDL_IF hdl;
    BFM bfm;
    std::vector<std::string> firstNs, doneNs, rdata;
    int k = 0;
    SC_HAS_PROCESS( sameClock );
    sameClock( sc_module_name n ) : sc_module( n ), ch( "ch", "tb" ), in( "in" ), bfm( "bfm" )
    {
        in( ch ); bfm.if_p( ch ); bfm.hdl_if_p( hdl ); bfm.clk( clk ); bfm.rst_n( rst_n );
        SC_THREAD( model ); SC_THREAD( hdlThread );
    }
    virtual void model() = 0;
    virtual sc_signal<bool> &req() = 0;
    virtual void setData( int ) {}
    virtual std::string getRdata() { return "-"; }
    void hdlThread()
    {
        sameClockRequester( clk, rst_n, req(), hdl.ack, [this]( int i ) { setData( i ); }, [this]() { return getRdata(); },
                            firstNs, doneNs, rdata );
    }
};

struct pushZero : sameClock<push_ack_channel<wordSt>, push_ack_in<wordSt>, push_ack_hdl_if<bv>, push_ack_src_bfm<wordSt, bv>>
{
    using sameClock::sameClock;
    void model() override { while (true) { wordSt v; in->pushReceive( v ); in->ack(); } }
    sc_signal<bool> &req() override { return hdl.push; }
    void setData( int i ) override { hdl.data = bv( i ); }
};

struct reqZero : sameClock<req_ack_channel<wordSt, wordSt>, req_ack_in<wordSt, wordSt>, req_ack_hdl_if<bv, bv>,
                           req_ack_src_bfm<wordSt, wordSt, bv, bv>>
{
    using sameClock::sameClock;
    void model() override { while (true) { wordSt r; in->reqReceive( r ); r.w += 0xa0; in->ack( r ); } }
    sc_signal<bool> &req() override { return hdl.req; }
    void setData( int i ) override { hdl.data = bv( i ); }
    std::string getRdata() override { return std::format( "{}", hdl.rdata.read().to_uint() ); }
};

struct popZero : sameClock<pop_ack_channel<wordSt>, pop_ack_in<wordSt>, pop_ack_hdl_if<bv>, pop_ack_src_bfm<wordSt, bv>>
{
    using sameClock::sameClock;
    void model() override { while (true) { in->popReceive(); wordSt v; v.w = 0xb0 + k++; in->ack( v ); } }
    sc_signal<bool> &req() override { return hdl.pop; }
    std::string getRdata() override { return std::format( "{}", hdl.rdata.read().to_uint() ); }
};

struct notifyZero : sameClock<notify_ack_channel<bool>, notify_ack_in<bool>, notify_ack_hdl_if<bool>, notify_ack_src_bfm<bool>>
{
    using sameClock::sameClock;
    void model() override { while (true) { in->waitNotify(); in->ack(); } }
    sc_signal<bool> &req() override { return hdl.notify; }
};

// An HDL APB master that drives as the UVM master does, 100 ps after the
// rising edge, and samples at the falling edge: two writes, then two reads,
// with no idle clock between transfers. The model answers in zero time.
SC_MODULE( apbSrcZero )
{
    sc_in<bool> clk, rst_n;
    apb_channel<wordSt, wordSt> ch;
    apb_in<wordSt, wordSt> in;
    apb_hdl_if<bv, bv> hdl;
    apb_src_bfm<wordSt, wordSt, bv, bv> bfm;
    std::vector<std::string> setupNs, doneNs, rdata;
    SC_HAS_PROCESS( apbSrcZero );
    apbSrcZero( sc_module_name n ) : sc_module( n ), ch( "ch", "tb" ), in( "in" ), bfm( "bfm" )
    {
        in( ch ); bfm.if_p( ch ); bfm.hdl_if_p( hdl ); bfm.clk( clk ); bfm.rst_n( rst_n );
        SC_THREAD( model ); SC_THREAD( master );
    }
    void model()
    {
        while (true) {
            bool isWrite; wordSt a, d;
            in->reqReceive( isWrite, a, d );
            if (!isWrite) { d.w = 0xa0 + a.w; in->complete( d ); }
        }
    }
    void master()
    {
        const sc_time skew( 100, SC_PS );
        do { wait( clk.posedge_event() ); } while (!rst_n);
        for (int k = 0; k < 4; k++) {
            wait( skew );
            hdl.psel = 1; hdl.penable = 0; hdl.pwrite = k < 2; hdl.paddr = bv( 4 * k ); hdl.pwdata = bv( k < 2 ? k : 0 );
            wait( clk.negedge_event() );
            setupNs.push_back( ns() );
            wait( clk.posedge_event() );
            wait( skew );
            hdl.penable = 1;
            do { wait( clk.negedge_event() ); } while (!hdl.pready);
            doneNs.push_back( ns() );
            if (k >= 2) { rdata.push_back( std::format( "{}", hdl.prdata.read().to_uint() ) ); }
            wait( clk.posedge_event() );
        }
        wait( skew );
        hdl.psel = 0; hdl.penable = 0;
    }
};

// A model APB master behind apb_dst_bfm posts three writes back to back. The
// HDL slave adds two wait states to each.
SC_MODULE( apbDst )
{
    sc_in<bool> clk, rst_n;
    apb_channel<wordSt, wordSt> ch;
    apb_out<wordSt, wordSt> out;
    apb_hdl_if<bv, bv> hdl;
    apb_dst_bfm<wordSt, wordSt, bv, bv> bfm;
    std::vector<std::string> returnNs, doneNs;
    SC_HAS_PROCESS( apbDst );
    apbDst( sc_module_name n ) : sc_module( n ), ch( "ch", "tb" ), out( "out" ), bfm( "bfm" )
    {
        out( ch ); bfm.if_p( ch ); bfm.hdl_if_p( hdl ); bfm.clk( clk ); bfm.rst_n( rst_n );
        SC_THREAD( model ); SC_THREAD( slave );
    }
    void model()
    {
        do { wait( clk.posedge_event() ); } while (!rst_n);
        for (int k = 0; k < 3; k++) {
            wordSt a, d; a.w = 4 * k; d.w = k;
            out->request( true, a, d );
            returnNs.push_back( ns() );
        }
    }
    void slave()
    {
        int waits = 0;
        while (true) {
            wait( clk.posedge_event() );
            if (hdl.psel && hdl.penable && hdl.pready) { doneNs.push_back( ns() ); }
            hdl.pready = 0;
            if (hdl.psel && hdl.penable && !hdl.pready) {
                if (++waits == 2) { hdl.pready = 1; waits = 0; }
            }
        }
    }
};

using rdChanT = axi_read_channel<wordSt, wordSt>;
using rdHdlT = axi_read_hdl_if<bv, bv>;
using wrChanT = axi_write_channel<wordSt, wordSt, strbSt>;
using wrHdlT = axi_write_hdl_if<bv, bv, sc_bv<4>>;
constexpr int AXI_N = 4;

// axi_read src: an HDL master issues AXI_N single-beat reads back to back and
// is ready for R on odd clocks only. The model slave is busy 30 ns after each
// address.
SC_MODULE( rdSrc )
{
    sc_in<bool> clk, rst_n;
    rdChanT ch;
    axi_read_in<wordSt, wordSt> in;
    rdHdlT hdl;
    axi_read_src_bfm<wordSt, wordSt, bv, bv> bfm;
    std::vector<std::string> arHdl, arModel, rHdl, rModel;
    SC_HAS_PROCESS( rdSrc );
    rdSrc( sc_module_name n ) : sc_module( n ), ch( "ch", "tb" ), in( "in" ), bfm( "bfm" )
    {
        in( ch ); bfm.if_p( ch ); bfm.hdl_if_p( hdl ); bfm.clk( clk ); bfm.rst_n( rst_n );
        SC_THREAD( model ); SC_THREAD( master );
    }
    void model()
    {
        while (true) {
            axiReadAddressSt<wordSt> a;
            in->receiveAddr( a );
            arModel.push_back( ns() );
            axiReadRespSt<wordSt> r;
            r.rid = a.arid; r.rdata.w = a.araddr.w; r.rresp = AXIRESP_OKAY; r.rlast = true;
            in->sendDataCycle( r );
            rModel.push_back( ns() );
            wait( 30, SC_NS );
        }
    }
    void master()
    {
        int sent = 0, clocks = 0;
        while (true) {
            wait( clk.posedge_event() );
            if (!rst_n) { hdl.arvalid = 0; hdl.rready = 0; continue; }
            clocks++;
            if (hdl.arvalid && hdl.arready) { arHdl.push_back( ns() ); sent++; }
            if (hdl.rvalid && hdl.rready) { rHdl.push_back( ns() ); }
            hdl.arvalid = sent < AXI_N;
            hdl.arid = 0; hdl.araddr = bv( 0x10 * sent ); hdl.arlen = 0; hdl.arsize = 2; hdl.arburst = 1;
            hdl.rready = clocks % 2;
        }
    }
};

// axi_read dst: a model master sends AXI_N single-beat reads back to back and
// takes R 30 ns after each beat. The HDL slave is ready for AR on odd clocks
// only and returns each read's data at once.
SC_MODULE( rdDst )
{
    sc_in<bool> clk, rst_n;
    rdChanT ch;
    axi_read_out<wordSt, wordSt> out;
    rdHdlT hdl;
    axi_read_dst_bfm<wordSt, wordSt, bv, bv> bfm;
    std::vector<std::string> arHdl, arModel, rHdl, rModel;
    SC_HAS_PROCESS( rdDst );
    rdDst( sc_module_name n ) : sc_module( n ), ch( "ch", "tb" ), out( "out" ), bfm( "bfm" )
    {
        out( ch ); bfm.if_p( ch ); bfm.hdl_if_p( hdl ); bfm.clk( clk ); bfm.rst_n( rst_n );
        SC_THREAD( addrModel ); SC_THREAD( dataModel ); SC_THREAD( slave );
    }
    void addrModel()
    {
        for (int k = 0; k < AXI_N; k++) {
            axiReadAddressSt<wordSt> a;
            a.arid = 0; a.araddr.w = 0x10 * k; a.arlen = 0; a.arsize = 2; a.arburst = AXIBURST_INCR;
            out->sendAddr( a );
            arModel.push_back( ns() );
        }
    }
    void dataModel()
    {
        while (true) {
            axiReadRespSt<wordSt> r;
            out->receiveDataCycle( r );
            rModel.push_back( ns() );
            wait( 30, SC_NS );
        }
    }
    void slave()
    {
        std::deque<std::uint64_t> pending;
        int clocks = 0;
        while (true) {
            wait( clk.posedge_event() );
            if (!rst_n) { hdl.arready = 0; hdl.rvalid = 0; continue; }
            clocks++;
            if (hdl.arvalid && hdl.arready) { arHdl.push_back( ns() ); pending.push_back( hdl.araddr.read().to_uint() ); }
            if (hdl.rvalid && hdl.rready) { rHdl.push_back( ns() ); pending.pop_front(); }
            hdl.arready = clocks % 2;
            hdl.rvalid = !pending.empty();
            hdl.rid = 0; hdl.rdata = bv( pending.empty() ? 0 : pending.front() ); hdl.rresp = 0; hdl.rlast = 1;
        }
    }
};

// axi_write src: an HDL master issues AXI_N single-beat writes, AW and W
// together, and is ready for B on odd clocks only. The model slave takes the
// address, then the data, answers B and is busy 30 ns. A transactional
// receiver behind a cycle-mode sender takes W in bursts.
SC_MODULE( wrSrc )
{
    sc_in<bool> clk, rst_n;
    wrChanT ch;
    axi_write_in<wordSt, wordSt, strbSt> in;
    wrHdlT hdl;
    axi_write_src_bfm<wordSt, wordSt, strbSt, bv, bv, sc_bv<4>> bfm;
    std::vector<std::string> awHdl, awModel, wHdl, wModel, bHdl, bModel;
    SC_HAS_PROCESS( wrSrc );
    wrSrc( sc_module_name n ) : sc_module( n ), ch( "ch", "tb", "api_list_size", 256, "" ), in( "in" ), bfm( "bfm" )
    {
        in( ch ); bfm.if_p( ch ); bfm.hdl_if_p( hdl ); bfm.clk( clk ); bfm.rst_n( rst_n );
        SC_THREAD( model ); SC_THREAD( master );
    }
    void model()
    {
        while (true) {
            axiWriteAddressSt<wordSt> a;
            in->receiveAddr( a );
            awModel.push_back( ns() );
            axiWriteDataSt<wordSt, strbSt> d;
            in->receiveData( d );
            wModel.push_back( ns() );
            axiWriteRespSt<> b;
            b.bid = a.awid; b.bresp = AXIRESP_OKAY;
            in->sendResp( b );
            bModel.push_back( ns() );
            wait( 30, SC_NS );
        }
    }
    void master()
    {
        int aw = 0, w = 0, clocks = 0;
        while (true) {
            wait( clk.posedge_event() );
            if (!rst_n) { hdl.awvalid = 0; hdl.wvalid = 0; hdl.bready = 0; continue; }
            clocks++;
            if (hdl.awvalid && hdl.awready) { awHdl.push_back( ns() ); aw++; }
            if (hdl.wvalid && hdl.wready) { wHdl.push_back( ns() ); w++; }
            if (hdl.bvalid && hdl.bready) { bHdl.push_back( ns() ); }
            hdl.awvalid = aw < AXI_N;
            hdl.awid = 0; hdl.awaddr = bv( 0x10 * aw ); hdl.awlen = 0; hdl.awsize = 2; hdl.awburst = 1;
            hdl.wvalid = w < AXI_N;
            hdl.wid = 0; hdl.wdata = bv( w ); hdl.wstrb = sc_bv<4>( 0xf ); hdl.wlast = 1;
            hdl.bready = clocks % 2;
        }
    }
};

// axi_write dst: a model master sends AXI_N single-beat writes back to back
// and takes B 30 ns after each response. The HDL slave is ready for AW on odd
// clocks and for W on even clocks, and answers B once it has both.
SC_MODULE( wrDst )
{
    sc_in<bool> clk, rst_n;
    wrChanT ch;
    axi_write_out<wordSt, wordSt, strbSt> out;
    wrHdlT hdl;
    axi_write_dst_bfm<wordSt, wordSt, strbSt, bv, bv, sc_bv<4>> bfm;
    std::vector<std::string> awHdl, awModel, wHdl, wModel, bHdl, bModel;
    SC_HAS_PROCESS( wrDst );
    wrDst( sc_module_name n ) : sc_module( n ), ch( "ch", "tb" ), out( "out" ), bfm( "bfm" )
    {
        out( ch ); bfm.if_p( ch ); bfm.hdl_if_p( hdl ); bfm.clk( clk ); bfm.rst_n( rst_n );
        SC_THREAD( addrModel ); SC_THREAD( dataModel ); SC_THREAD( respModel ); SC_THREAD( slave );
    }
    void addrModel()
    {
        for (int k = 0; k < AXI_N; k++) {
            axiWriteAddressSt<wordSt> a;
            a.awid = 0; a.awaddr.w = 0x10 * k; a.awlen = 0; a.awsize = 2; a.awburst = AXIBURST_INCR;
            out->sendAddr( a );
            awModel.push_back( ns() );
        }
    }
    void dataModel()
    {
        for (int k = 0; k < AXI_N; k++) {
            axiWriteDataSt<wordSt, strbSt> d;
            d.wid = 0; d.wdata.w = k; d.wstrb.w = 0xf; d.wlast = true;
            out->sendData( d );
            wModel.push_back( ns() );
        }
    }
    void respModel()
    {
        while (true) {
            axiWriteRespSt<> b;
            out->receiveResp( b );
            bModel.push_back( ns() );
            wait( 30, SC_NS );
        }
    }
    void slave()
    {
        int aw = 0, w = 0, b = 0, clocks = 0;
        while (true) {
            wait( clk.posedge_event() );
            if (!rst_n) { hdl.awready = 0; hdl.wready = 0; hdl.bvalid = 0; continue; }
            clocks++;
            if (hdl.awvalid && hdl.awready) { awHdl.push_back( ns() ); aw++; }
            if (hdl.wvalid && hdl.wready) { wHdl.push_back( ns() ); w++; }
            if (hdl.bvalid && hdl.bready) { bHdl.push_back( ns() ); b++; }
            hdl.awready = clocks % 2;
            hdl.wready = !(clocks % 2);
            hdl.bvalid = b < aw && b < w;
            hdl.bid = 0; hdl.bresp = 0;
        }
    }
};

constexpr int PACED_BEATS = 40;

// A model writer behind a rdy_vld dst BFM that waits on the clock between
// writes, or (memWoken) writes once each time an HDL memory requester behind
// memory_src_bfm writes, every other clock, so that the memory BFM's
// request() wakes it in the edge's own delta. The HDL sink is always ready.
SC_MODULE( paced )
{
    sc_in<bool> clk, rst_n;
    rdy_vld_channel<wordSt> ch;
    rdy_vld_out<wordSt> out;
    rdy_vld_hdl_if<bv> hdl;
    rdy_vld_dst_bfm<wordSt, bv> bfm;
    memory_channel<wordSt, wordSt> mch;
    memory_in<wordSt, wordSt> min;
    memory_hdl_if<bv, bv> mhdl;
    memory_src_bfm<wordSt, wordSt, bv, bv> mbfm;
    bool memWoken;
    int beats = 0;
    std::vector<std::string> times;
    SC_HAS_PROCESS( paced );
    paced( sc_module_name n, bool m ) : sc_module( n ), ch( "ch", "tb", BACKPRESSURE_ALLOWED ), out( "out" ), bfm( "bfm" ),
        mch( "mch", "tb" ), min( "min" ), mbfm( "mbfm" ), memWoken( m )
    {
        out( ch ); bfm.if_p( ch ); bfm.hdl_if_p( hdl ); bfm.clk( clk ); bfm.rst_n( rst_n );
        min( mch ); mbfm.if_p( mch ); mbfm.hdl_if_p( mhdl ); mbfm.clk( clk ); mbfm.rst_n( rst_n );
        SC_THREAD( model ); SC_THREAD( hdlThread );
    }
    void model()
    {
        do { wait( clk.posedge_event() ); } while (!rst_n);
        for (int k = 0; k < PACED_BEATS; k++) {
            if (memWoken) {
                bool isWrite; wordSt a, d;
                min->reqReceive( isWrite, a, d );
            }
            wordSt v; v.w = k;
            out->write( v );
            if (!memWoken) { wait( clk.posedge_event() ); }
        }
    }
    void hdlThread()
    {
        hdl.rdy = 1;
        int clocks = 0;
        while (true) {
            wait( clk.posedge_event() );
            if (!rst_n) { continue; }
            clocks++;
            if (hdl.vld && hdl.rdy) { beats++; times.push_back( ns() ); }
            mhdl.enable = memWoken && clocks % 2 == 0;
            mhdl.wr_en = 1;
            mhdl.addr = bv( clocks );
            mhdl.write_data = bv( clocks );
        }
    }
};

// A model reader behind a rdy_vld src BFM that waits on the clock after
// each read. The HDL writer holds vld high.
SC_MODULE( pacedReader )
{
    sc_in<bool> clk, rst_n;
    rdy_vld_channel<wordSt> ch;
    rdy_vld_in<wordSt> in;
    rdy_vld_hdl_if<bv> hdl;
    rdy_vld_src_bfm<wordSt, bv> bfm;
    std::vector<std::string> times;
    SC_HAS_PROCESS( pacedReader );
    pacedReader( sc_module_name n ) : sc_module( n ), ch( "ch", "tb", BACKPRESSURE_ALLOWED ), in( "in" ), bfm( "bfm" )
    {
        in( ch ); bfm.if_p( ch ); bfm.hdl_if_p( hdl ); bfm.clk( clk ); bfm.rst_n( rst_n );
        SC_THREAD( model ); SC_THREAD( hdlThread );
    }
    void model()
    {
        while (true) {
            wordSt v;
            in->read( v );
            wait( clk.posedge_event() );
        }
    }
    void hdlThread()
    {
        int sent = 0;
        while (true) {
            wait( clk.posedge_event() );
            if (!rst_n) { continue; }
            if (hdl.vld && hdl.rdy) { times.push_back( ns() ); sent++; }
            hdl.vld = sent < 8;
            hdl.data = bv( sent );
        }
    }
};

const sc_time SKEW( 100, SC_PS );

// A model that reads a beat and writes it on, in one thread, between a src
// BFM and a dst BFM. The HDL source and sink drive at the rising edge plus
// 100 ps, as UVM agents do; the source offers a beat on every clock and the
// sink is ready on every clock or, with half, on odd clocks only. ready() at
// each falling edge is traced for both ports.
template <typename F>
struct relayRate : sc_module {
    sc_in<bool> clk, rst_n;
    typename F::chan inCh, outCh;
    typename F::in in;
    typename F::out out;
    typename F::hdl inHdl, outHdl;
    typename F::src inBfm;
    typename F::dst outBfm;
    bool half;
    int clocks = 0;
    std::vector<std::string> outNs, vals;
    std::string inRdy, outRdy;
    SC_HAS_PROCESS( relayRate );
    relayRate( sc_module_name n, bool half_ ) : sc_module( n ), inCh( "inCh", "tb", BACKPRESSURE_ALLOWED ),
        outCh( "outCh", "tb", BACKPRESSURE_ALLOWED ), in( "in" ), out( "out" ), inBfm( "inBfm" ), outBfm( "outBfm" ), half( half_ )
    {
        in( inCh ); inBfm.if_p( inCh ); inBfm.hdl_if_p( inHdl ); inBfm.clk( clk ); inBfm.rst_n( rst_n );
        out( outCh ); outBfm.if_p( outCh ); outBfm.hdl_if_p( outHdl ); outBfm.clk( clk ); outBfm.rst_n( rst_n );
        SC_THREAD( model ); SC_THREAD( source ); SC_THREAD( sink );
        SC_METHOD( trace ); sensitive << clk.neg(); dont_initialize();
    }
    void model() { while (true) { F::put( out, F::get( in ) ); } }
    void source()
    {
        do { wait( clk.posedge_event() ); } while (!rst_n);
        int k = 0;
        while (true) {
            wait( SKEW );
            F::offer( inHdl, k );
            wait( clk.posedge_event() );
            if (F::vld( inHdl ) && F::rdy( inHdl )) { k++; }
        }
    }
    void sink()
    {
        do { wait( clk.posedge_event() ); } while (!rst_n);
        while (true) {
            wait( SKEW );
            F::ready( outHdl, !half || clocks % 2 );
            wait( clk.posedge_event() );
            if (F::vld( outHdl ) && F::rdy( outHdl ) && outNs.size() < 16) {
                outNs.push_back( ns() );
                vals.push_back( std::to_string( F::data( outHdl ) ) );
            }
            clocks++;
        }
    }
    void trace()
    {
        if (!rst_n || inRdy.size() >= 12) { return; }
        inRdy += F::rdy( inHdl ) ? '1' : '0';
        outRdy += F::rdy( outHdl ) ? '1' : '0';
    }
};

struct rvRelayF {
    using chan = rdy_vld_channel<wordSt>;
    using in = rdy_vld_in<wordSt>;
    using out = rdy_vld_out<wordSt>;
    using hdl = rdy_vld_hdl_if<bv>;
    using src = rdy_vld_src_bfm<wordSt, bv>;
    using dst = rdy_vld_dst_bfm<wordSt, bv>;
    static std::uint64_t get( in &p ) { wordSt v; p->read( v ); return v.w; }
    static void put( out &p, std::uint64_t w ) { wordSt v; v.w = w; p->write( v ); }
    static void offer( hdl &h, int k ) { h.vld = 1; h.data = bv( k ); }
    static void ready( hdl &h, bool r ) { h.rdy = r; }
    static bool vld( hdl &h ) { return h.vld.read(); }
    static bool rdy( hdl &h ) { return h.rdy.read(); }
    static std::uint64_t data( hdl &h ) { return h.data.read().to_uint64(); }
};

using axInfo = axi4StreamInfoSt<wordSt, wordSt, wordSt>;
struct axRelayF {
    using chan = axi4_stream_channel<wordSt, wordSt, wordSt>;
    using in = axi4_stream_in<wordSt, wordSt, wordSt>;
    using out = axi4_stream_out<wordSt, wordSt, wordSt>;
    using hdl = axi4_stream_hdl_if<bv, bv, bv, sc_bv<4>, sc_bv<4>>;
    using src = axi4_stream_src_bfm<wordSt, wordSt, wordSt, bv, bv, bv, sc_bv<4>, sc_bv<4>>;
    using dst = axi4_stream_dst_bfm<wordSt, wordSt, wordSt, bv, bv, bv, sc_bv<4>, sc_bv<4>>;
    static std::uint64_t get( in &p ) { axInfo v; p->receiveInfo( v ); return v.tdata.w; }
    static void put( out &p, std::uint64_t w ) { axInfo v; v.tdata.w = w; p->sendInfo( v ); }
    static void offer( hdl &h, int k ) { h.tvalid = 1; h.tdata = bv( k ); }
    static void ready( hdl &h, bool r ) { h.tready = r; }
    static bool vld( hdl &h ) { return h.tvalid.read(); }
    static bool rdy( hdl &h ) { return h.tready.read(); }
    static std::uint64_t data( hdl &h ) { return h.tdata.read().to_uint64(); }
};

// An axi_read slave model that takes an address and sends its one R beat.
// The HDL master keeps an address on the pins from the rising edge plus
// 100 ps and is always ready for R.
SC_MODULE( rdSlaveRate )
{
    sc_in<bool> clk, rst_n;
    rdChanT ch;
    axi_read_in<wordSt, wordSt> in;
    rdHdlT hdl;
    axi_read_src_bfm<wordSt, wordSt, bv, bv> bfm;
    std::vector<std::string> arNs, rNs;
    SC_HAS_PROCESS( rdSlaveRate );
    rdSlaveRate( sc_module_name n ) : sc_module( n ), ch( "ch", "tb" ), in( "in" ), bfm( "bfm" )
    {
        in( ch ); bfm.if_p( ch ); bfm.hdl_if_p( hdl ); bfm.clk( clk ); bfm.rst_n( rst_n );
        SC_THREAD( model ); SC_THREAD( master );
    }
    void model()
    {
        while (true) {
            axiReadAddressSt<wordSt> a;
            in->receiveAddr( a );
            axiReadRespSt<wordSt> r;
            r.rid = a.arid; r.rdata.w = a.araddr.w; r.rresp = AXIRESP_OKAY; r.rlast = true;
            in->sendDataCycle( r );
        }
    }
    void master()
    {
        do { wait( clk.posedge_event() ); } while (!rst_n);
        int k = 0;
        while (true) {
            wait( SKEW );
            hdl.arvalid = 1; hdl.arid = 0; hdl.araddr = bv( 0x10 * k ); hdl.arlen = 0; hdl.arsize = 2; hdl.arburst = 1;
            hdl.rready = 1;
            wait( clk.posedge_event() );
            if (hdl.arvalid && hdl.arready && arNs.size() < 8) { arNs.push_back( ns() ); k++; }
            if (hdl.rvalid && hdl.rready && rNs.size() < 8) { rNs.push_back( ns() ); }
        }
    }
};

// A model writes six beats back to back into a rdy_vld dst BFM. The HDL sink
// is ready from the rising edge plus 100 ps. At 76 ns, in the low phase after
// the BFM completed the write of the beat on the pins, it lowers rdy until
// the drive point after the 90 ns edge; with reset it also asserts its own
// reset for that time. The BFM's rst_n is that reset.
SC_MODULE( lowered )
{
    sc_in<bool> clk, rst_n;
    sc_signal<bool> rstLocal;
    rdy_vld_channel<wordSt> ch;
    rdy_vld_out<wordSt> out;
    rdy_vld_hdl_if<bv> hdl;
    rdy_vld_dst_bfm<wordSt, bv> bfm;
    bool reset;
    std::vector<std::string> vals;
    SC_HAS_PROCESS( lowered );
    lowered( sc_module_name n, bool r ) : sc_module( n ), ch( "ch", "tb", BACKPRESSURE_ALLOWED ), out( "out" ), bfm( "bfm" ), reset( r )
    {
        out( ch ); bfm.if_p( ch ); bfm.hdl_if_p( hdl ); bfm.clk( clk ); bfm.rst_n( rstLocal );
        SC_THREAD( model ); SC_THREAD( sink );
    }
    void model()
    {
        do { wait( clk.posedge_event() ); } while (!rstLocal);
        for (int k = 0; k < 6; k++) { wordSt v; v.w = k; out->write( v ); }
    }
    void sink()
    {
        rstLocal = 0;
        do { wait( clk.posedge_event() ); } while (!rst_n);
        rstLocal = 1;
        while (true) {
            wait( SKEW );
            const sc_time edge = sc_time_stamp() - SKEW;
            hdl.rdy = edge != sc_time( 80, SC_NS );
            if (edge == sc_time( 90, SC_NS )) { rstLocal = 1; }
            if (edge == sc_time( 70, SC_NS )) {
                wait( sc_time( 6, SC_NS ) - SKEW );
                hdl.rdy = 0;
                if (reset) { rstLocal = 0; }
            }
            wait( clk.posedge_event() );
            if (hdl.vld && hdl.rdy) { vals.push_back( std::to_string( hdl.data.read().to_uint64() ) ); }
        }
    }
};

// A model behind an ack-style dst BFM sends four requests back to back in
// zero time. The HDL destination acks each request combinationally, with
// rdata 0x50 plus the request's number on req_ack and pop_ack, and records
// the edges and values it takes. delayNs puts a timed delay on the channel,
// which ack() waits out after the BFM took the request. With lowerAt the
// destination lowers ack in the low phase before the edge at lowerAt and
// raises it again one step after that edge; with reset it also asserts the
// BFM's reset for that time.
template <typename F>
struct ackDst : sc_module {
    sc_in<bool> clk, rst_n;
    typename F::chan ch;
    typename F::out out;
    typename F::hdl hdl;
    typename F::dst bfm;
    sc_signal<bool> rstLocal;
    sc_time lowerAt;
    bool reset;
    sc_event poke;
    bool low = false;
    int taken = 0;
    std::vector<std::string> returnNs, takeNs, vals, rdata;
    SC_HAS_PROCESS( ackDst );
    ackDst( sc_module_name n, int delayNs, int lowerAtNs, bool reset_ = false ) : sc_module( n ), ch( "ch", "tb" ),
        out( "out" ), bfm( "bfm" ), lowerAt( lowerAtNs, SC_NS ), reset( reset_ )
    {
        out( ch ); bfm.if_p( ch ); bfm.hdl_if_p( hdl ); bfm.clk( clk ); bfm.rst_n( rstLocal );
        if (delayNs) { ch.setTimed( delayNs, TIMED_DELAY_FIXED_INIT ); }
        SC_THREAD( model ); SC_THREAD( dest ); SC_THREAD( lower );
        SC_METHOD( answer ); sensitive << F::req( hdl ) << poke; dont_initialize();
    }
    void model()
    {
        do { wait( clk.posedge_event() ); } while (!rst_n);
        for (int k = 0; k < 4; k++) {
            std::uint64_t r = F::send( out, k );
            returnNs.push_back( ns() );
            if (F::hasRdata) { rdata.push_back( std::to_string( r ) ); }
        }
    }
    void answer()
    {
        F::ack( hdl, F::req( hdl ).read() && !low );
        F::setRdata( hdl, 0x50 + taken );
    }
    void lower()
    {
        rstLocal = 0;
        do { wait( clk.posedge_event() ); } while (!rst_n);
        rstLocal = 1;
        if (lowerAt == SC_ZERO_TIME) { return; }
        wait( lowerAt - sc_time( 4, SC_NS ) - sc_time_stamp() );
        low = true;
        if (reset) { rstLocal = 0; }
        poke.notify();
        wait( sc_time( 4, SC_NS ) + SKEW );
        low = false;
        rstLocal = 1;
        poke.notify();
    }
    void dest()
    {
        while (true) {
            wait( clk.posedge_event() );
            if (rst_n && F::req( hdl ).read() && F::acked( hdl )) {
                takeNs.push_back( ns() );
                vals.push_back( std::to_string( F::data( hdl ) ) );
                taken++;
                wait( SKEW );
                poke.notify();
            }
        }
    }
};

struct pushDstF {
    using chan = push_ack_channel<wordSt>;
    using out = push_ack_out<wordSt>;
    using hdl = push_ack_hdl_if<bv>;
    using dst = push_ack_dst_bfm<wordSt, bv>;
    static constexpr bool hasRdata = false;
    static std::uint64_t send( out &p, int k ) { wordSt v; v.w = k; p->push( v ); return 0; }
    static sc_signal<bool> &req( hdl &h ) { return h.push; }
    static void ack( hdl &h, bool a ) { h.ack = a; }
    static bool acked( hdl &h ) { return h.ack.read(); }
    static void setRdata( hdl &, int ) {}
    static std::uint64_t data( hdl &h ) { return h.data.read().to_uint64(); }
};

struct notifyDstF {
    using chan = notify_ack_channel<bool>;
    using out = notify_ack_out<bool>;
    using hdl = notify_ack_hdl_if<bool>;
    using dst = notify_ack_dst_bfm<bool>;
    static constexpr bool hasRdata = false;
    static std::uint64_t send( out &p, int ) { p->notify(); return 0; }
    static sc_signal<bool> &req( hdl &h ) { return h.notify; }
    static void ack( hdl &h, bool a ) { h.ack = a; }
    static bool acked( hdl &h ) { return h.ack.read(); }
    static void setRdata( hdl &, int ) {}
    static std::uint64_t data( hdl & ) { return 1; }
};

struct reqDstF {
    using chan = req_ack_channel<wordSt, wordSt>;
    using out = req_ack_out<wordSt, wordSt>;
    using hdl = req_ack_hdl_if<bv, bv>;
    using dst = req_ack_dst_bfm<wordSt, wordSt, bv, bv>;
    static constexpr bool hasRdata = true;
    static std::uint64_t send( out &p, int k ) { wordSt v, r; v.w = k; p->req( v, r ); return r.w; }
    static sc_signal<bool> &req( hdl &h ) { return h.req; }
    static void ack( hdl &h, bool a ) { h.ack = a; }
    static bool acked( hdl &h ) { return h.ack.read(); }
    static void setRdata( hdl &h, int r ) { h.rdata = bv( r ); }
    static std::uint64_t data( hdl &h ) { return h.data.read().to_uint64(); }
};

struct popDstF {
    using chan = pop_ack_channel<wordSt>;
    using out = pop_ack_out<wordSt>;
    using hdl = pop_ack_hdl_if<bv>;
    using dst = pop_ack_dst_bfm<wordSt, bv>;
    static constexpr bool hasRdata = true;
    static std::uint64_t send( out &p, int ) { wordSt r; p->pop( r ); return r.w; }
    static sc_signal<bool> &req( hdl &h ) { return h.pop; }
    static void ack( hdl &h, bool a ) { h.ack = a; }
    static bool acked( hdl &h ) { return h.ack.read(); }
    static void setRdata( hdl &h, int r ) { h.rdata = bv( r ); }
    static std::uint64_t data( hdl & ) { return 1; }
};

SC_MODULE( probe )
{
    sc_clock clk;
    sc_signal<bool> rst_n;
    pushSrc push0, push1, push2;
    reqSrc req0, req1, req2;
    popSrc pop0, pop1;
    notifySrc notify0, notify1;
    apbSrc apbSrcGood, apbSrcWithdraw;
    apbSrcZero apbSrcZeroWait;
    pushZero pushSameClock;
    reqZero reqSameClock;
    popZero popSameClock;
    notifyZero notifySameClock;
    apbDst apbDstPosted;
    rdSrc axiRdSrc;
    rdDst axiRdDst;
    wrSrc axiWrSrc;
    wrDst axiWrDst;
    paced pacedClock, pacedMem;
    pacedReader pacedRead;
    relayRate<rvRelayF> rvRelayFull, rvRelayHalf;
    relayRate<axRelayF> axRelayFull, axRelayHalf;
    rdSlaveRate axiRdSlaveRate;
    lowered loweredRdy, loweredReset;
    ackDst<pushDstF> pushDstRate, pushDstDelay, pushDstLowered, pushDstReset;
    ackDst<notifyDstF> notifyDstRate;
    ackDst<reqDstF> reqDstRate, reqDstDelay;
    ackDst<popDstF> popDstRate;

    SC_HAS_PROCESS( probe );
    probe( sc_module_name n ) : sc_module( n ), clk( "clk", 10, SC_NS ),
        push0( "push0", 0 ), push1( "push1", 1 ), push2( "push2", 2 ),
        req0( "req0", 0 ), req1( "req1", 1 ), req2( "req2", 2 ),
        pop0( "pop0", 0 ), pop1( "pop1", 1 ), notify0( "notify0", 0 ), notify1( "notify1", 1 ),
        apbSrcGood( "apbSrcGood", false ), apbSrcWithdraw( "apbSrcWithdraw", true ), apbSrcZeroWait( "apbSrcZeroWait" ),
        pushSameClock( "pushSameClock" ), reqSameClock( "reqSameClock" ), popSameClock( "popSameClock" ),
        notifySameClock( "notifySameClock" ),
        apbDstPosted( "apbDstPosted" ),
        axiRdSrc( "axiRdSrc" ), axiRdDst( "axiRdDst" ), axiWrSrc( "axiWrSrc" ), axiWrDst( "axiWrDst" ),
        pacedClock( "pacedClock", false ), pacedMem( "pacedMem", true ), pacedRead( "pacedRead" ),
        rvRelayFull( "rvRelayFull", false ), rvRelayHalf( "rvRelayHalf", true ),
        axRelayFull( "axRelayFull", false ), axRelayHalf( "axRelayHalf", true ), axiRdSlaveRate( "axiRdSlaveRate" ),
        loweredRdy( "loweredRdy", false ), loweredReset( "loweredReset", true ),
        pushDstRate( "pushDstRate", 0, 0 ), pushDstDelay( "pushDstDelay", 25, 0 ), pushDstLowered( "pushDstLowered", 0, 70 ),
        pushDstReset( "pushDstReset", 0, 70, true ),
        notifyDstRate( "notifyDstRate", 0, 0 ), reqDstRate( "reqDstRate", 0, 0 ), reqDstDelay( "reqDstDelay", 25, 0 ),
        popDstRate( "popDstRate", 0, 0 )
    {
        push0.clk( clk ); push0.rst_n( rst_n ); push1.clk( clk ); push1.rst_n( rst_n ); push2.clk( clk ); push2.rst_n( rst_n );
        req0.clk( clk ); req0.rst_n( rst_n ); req1.clk( clk ); req1.rst_n( rst_n ); req2.clk( clk ); req2.rst_n( rst_n );
        pop0.clk( clk ); pop0.rst_n( rst_n ); pop1.clk( clk ); pop1.rst_n( rst_n );
        notify0.clk( clk ); notify0.rst_n( rst_n ); notify1.clk( clk ); notify1.rst_n( rst_n );
        apbSrcGood.clk( clk ); apbSrcGood.rst_n( rst_n ); apbSrcWithdraw.clk( clk ); apbSrcWithdraw.rst_n( rst_n );
        apbSrcZeroWait.clk( clk ); apbSrcZeroWait.rst_n( rst_n );
        pushSameClock.clk( clk ); pushSameClock.rst_n( rst_n ); reqSameClock.clk( clk ); reqSameClock.rst_n( rst_n );
        popSameClock.clk( clk ); popSameClock.rst_n( rst_n ); notifySameClock.clk( clk ); notifySameClock.rst_n( rst_n );
        apbDstPosted.clk( clk ); apbDstPosted.rst_n( rst_n );
        axiRdSrc.clk( clk ); axiRdSrc.rst_n( rst_n ); axiRdDst.clk( clk ); axiRdDst.rst_n( rst_n );
        axiWrSrc.clk( clk ); axiWrSrc.rst_n( rst_n ); axiWrDst.clk( clk ); axiWrDst.rst_n( rst_n );
        pacedClock.clk( clk ); pacedClock.rst_n( rst_n ); pacedMem.clk( clk ); pacedMem.rst_n( rst_n );
        pacedRead.clk( clk ); pacedRead.rst_n( rst_n );
        rvRelayFull.clk( clk ); rvRelayFull.rst_n( rst_n ); rvRelayHalf.clk( clk ); rvRelayHalf.rst_n( rst_n );
        axRelayFull.clk( clk ); axRelayFull.rst_n( rst_n ); axRelayHalf.clk( clk ); axRelayHalf.rst_n( rst_n );
        axiRdSlaveRate.clk( clk ); axiRdSlaveRate.rst_n( rst_n );
        loweredRdy.clk( clk ); loweredRdy.rst_n( rst_n ); loweredReset.clk( clk ); loweredReset.rst_n( rst_n );
        pushDstRate.clk( clk ); pushDstRate.rst_n( rst_n ); pushDstDelay.clk( clk ); pushDstDelay.rst_n( rst_n );
        pushDstLowered.clk( clk ); pushDstLowered.rst_n( rst_n ); pushDstReset.clk( clk ); pushDstReset.rst_n( rst_n ); notifyDstRate.clk( clk ); notifyDstRate.rst_n( rst_n );
        reqDstRate.clk( clk ); reqDstRate.rst_n( rst_n ); reqDstDelay.clk( clk ); reqDstDelay.rst_n( rst_n );
        popDstRate.clk( clk ); popDstRate.rst_n( rst_n );
        SC_THREAD( run );
    }

    void run()
    {
        rst_n = 0;
        wait( 25, SC_NS );
        rst_n = 1;
        wait( 2, SC_US );
        std::printf( "rec apbSrcGood take=%s done=%s\\n", join( apbSrcGood.takeNs ).c_str(), join( apbSrcGood.doneNs ).c_str() );
        std::printf( "rec apbSrcZeroWait setup=%s done=%s rdata=%s\\n", join( apbSrcZeroWait.setupNs ).c_str(),
                     join( apbSrcZeroWait.doneNs ).c_str(), join( apbSrcZeroWait.rdata ).c_str() );
        std::printf( "rec pushSameClock first=%s done=%s\\n", join( pushSameClock.firstNs ).c_str(), join( pushSameClock.doneNs ).c_str() );
        std::printf( "rec reqSameClock first=%s done=%s rdata=%s\\n", join( reqSameClock.firstNs ).c_str(), join( reqSameClock.doneNs ).c_str(),
                     join( reqSameClock.rdata ).c_str() );
        std::printf( "rec popSameClock first=%s done=%s rdata=%s\\n", join( popSameClock.firstNs ).c_str(), join( popSameClock.doneNs ).c_str(),
                     join( popSameClock.rdata ).c_str() );
        std::printf( "rec notifySameClock first=%s done=%s\\n", join( notifySameClock.firstNs ).c_str(), join( notifySameClock.doneNs ).c_str() );
        std::printf( "rec apbDstPosted returns=%s done=%s\\n", join( apbDstPosted.returnNs ).c_str(), join( apbDstPosted.doneNs ).c_str() );
        std::printf( "rec axiRdSrc arHdl=%s arModel=%s rHdl=%s rModel=%s\\n", join( axiRdSrc.arHdl ).c_str(),
                     join( axiRdSrc.arModel ).c_str(), join( axiRdSrc.rHdl ).c_str(), join( axiRdSrc.rModel ).c_str() );
        std::printf( "rec axiRdDst arHdl=%s arModel=%s rHdl=%s rModel=%s\\n", join( axiRdDst.arHdl ).c_str(),
                     join( axiRdDst.arModel ).c_str(), join( axiRdDst.rHdl ).c_str(), join( axiRdDst.rModel ).c_str() );
        std::printf( "rec axiWrSrc awHdl=%s awModel=%s wHdl=%s wModel=%s bHdl=%s bModel=%s\\n",
                     join( axiWrSrc.awHdl ).c_str(), join( axiWrSrc.awModel ).c_str(), join( axiWrSrc.wHdl ).c_str(),
                     join( axiWrSrc.wModel ).c_str(), join( axiWrSrc.bHdl ).c_str(), join( axiWrSrc.bModel ).c_str() );
        std::printf( "rec axiWrDst awHdl=%s awModel=%s wHdl=%s wModel=%s bHdl=%s bModel=%s\\n",
                     join( axiWrDst.awHdl ).c_str(), join( axiWrDst.awModel ).c_str(), join( axiWrDst.wHdl ).c_str(),
                     join( axiWrDst.wModel ).c_str(), join( axiWrDst.bHdl ).c_str(), join( axiWrDst.bModel ).c_str() );
        std::printf( "rec pacedClock beats=%d times=%s\\n", pacedClock.beats, join( pacedClock.times ).c_str() );
        std::printf( "rec pacedMem beats=%d times=%s\\n", pacedMem.beats, join( pacedMem.times ).c_str() );
        std::printf( "rec pacedRead times=%s\\n", join( pacedRead.times ).c_str() );
        std::printf( "rec pacedClockRate times=%s\\n", join( pacedClock.times ).c_str() );
        for (auto *r : { &rvRelayFull, &rvRelayHalf }) {
            std::printf( "rec %s out=%s vals=%s\\ntrace %s in=%s out=%s\\n", r->basename(), join( r->outNs ).c_str(), join( r->vals ).c_str(),
                         r->basename(), r->inRdy.c_str(), r->outRdy.c_str() );
        }
        for (auto *r : { &axRelayFull, &axRelayHalf }) {
            std::printf( "rec %s out=%s vals=%s\\ntrace %s in=%s out=%s\\n", r->basename(), join( r->outNs ).c_str(), join( r->vals ).c_str(),
                         r->basename(), r->inRdy.c_str(), r->outRdy.c_str() );
        }
        std::printf( "rec axiRdSlaveRate ar=%s r=%s\\n", join( axiRdSlaveRate.arNs ).c_str(), join( axiRdSlaveRate.rNs ).c_str() );
        std::printf( "rec loweredRdy vals=%s\\n", join( loweredRdy.vals ).c_str() );
        std::printf( "rec loweredReset vals=%s\\n", join( loweredReset.vals ).c_str() );
        auto ackRec = [&]( auto &d ) {
            std::printf( "rec %s returns=%s take=%s vals=%s rdata=%s\\n", d.basename(), join( d.returnNs ).c_str(),
                         join( d.takeNs ).c_str(), join( d.vals ).c_str(), join( d.rdata ).c_str() );
        };
        ackRec( pushDstRate ); ackRec( pushDstDelay ); ackRec( pushDstLowered ); ackRec( pushDstReset ); ackRec( notifyDstRate );
        ackRec( reqDstRate ); ackRec( reqDstDelay ); ackRec( popDstRate );
        for (const char *b = a2c_bfm_contract_break(); *b; b = a2c_bfm_contract_break()) {
            std::printf( "uvm break: %s\\n", b );
        }
        sc_stop();
    }
};

int sc_main( int, char *[] )
{
    logging::GetInstance().setDefaultVerbosity( VERBOSITY_MEDIUM );
    bfmContractCheck::toUvm = true;
    probe p( "p" );
    sc_start();
    std::printf( "probe done\\n" );
    return 0;
}
"""

HELD = 'HDL dropped or changed a request between the edge the BFM took it and the edge it completed'
PACED = 'remove the wait from the model'
LOWERED = 'HDL lowered ready between the falling edge and the rising edge after it'
FAILURES = []


def check(condition, message):
    print(f"  {'PASS' if condition else 'FAIL'}: {message}")
    if not condition:
        FAILURES.append(message)


def records(output):
    return {m.group(1): {k: [v for v in vals.split(',') if v] for k, vals in re.findall(r'(\w+)=([\d,]*)', m.group(2))}
            for m in re.finditer(r'^rec (\w+) (.*)$', output, re.M)}


def logged(output, scenario, text):
    return [line for line in output.splitlines()
            if line.startswith(f'p.{scenario}.') and text in line and not line.startswith('uvm break')]


def queued(output, scenario, text):
    return [line for line in output.splitlines() if line.startswith(f'uvm break: p.{scenario}.') and text in line]


def test_bfm_handshake_contract():
    scLibdir = os.environ.get('SYSTEMC_LIBDIR', '')
    tmpdir = tempfile.mkdtemp(prefix='a2c_bfm_handshake_')
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
        rec = records(output)

        for scenario in ['push0', 'req0', 'pop0', 'notify0', 'apbSrcGood', 'apbSrcZeroWait']:
            check(logged(output, scenario, HELD) == [] and queued(output, scenario, HELD) == [],
                  f"{scenario}: an HDL requester that holds its request until the ack breaks nothing")
        for scenario, how in [('push1', 'drops'), ('push2', 'changes'), ('req1', 'drops'), ('req2', 'changes'),
                              ('pop1', 'drops'), ('notify1', 'drops'), ('apbSrcWithdraw', 'drops')]:
            check(len(logged(output, scenario, HELD)) >= 1,
                  f"{scenario}: an HDL requester that {how} its request inside the model's call logs the break")
            check(len(queued(output, scenario, HELD)) == 1,
                  f"{scenario}: the break is queued once for the testbench (got {queued(output, scenario, HELD)})")

        r = rec.get('apbSrcGood', {})
        take, done = [int(v) for v in r.get('take', [])], [int(v) for v in r.get('done', [])]
        check(len(take) == 2 and len(done) == 2 and all(d > t for t, d in zip(take, done)),
              f"apb src: PREADY completes each posted write only after the model took it (take={take} done={done})")

        r = rec.get('apbSrcZeroWait', {})
        setup, done = [int(v) for v in r.get('setup', [])], [int(v) for v in r.get('done', [])]
        check(len(setup) == 4 and len(done) == 4 and all(d - s == 10 for s, d in zip(setup, done)),
              f"apb src: a zero-time model completes each transfer in its first access phase (setup={setup} done={done})")
        check(r.get('rdata') == ['168', '172'], f"apb src: each read returns its word with PREADY (rdata={r.get('rdata')})")

        for scenario, want in [('pushSameClock', None), ('reqSameClock', ['160', '161', '162', '163']),
                               ('popSameClock', ['176', '177', '178', '179']), ('notifySameClock', None)]:
            r = rec.get(scenario, {})
            first, done = [int(v) for v in r.get('first', [])], [int(v) for v in r.get('done', [])]
            check(len(first) == 4 and first == done and all(b - a == 10 for a, b in zip(done, done[1:])),
                  f"{scenario}: a zero-time model acks each request in its first clock, one per clock, as a "
                  f"destination whose ack follows the request does (first={first} done={done})")
            if want:
                check(r.get('rdata') == want, f"{scenario}: each answer comes with its ack (rdata={r.get('rdata')})")
            check(logged(output, scenario, HELD) == [], f"{scenario}: a request held until its ack breaks nothing")

        r = rec.get('apbDstPosted', {})
        returns, done = r.get('returns', []), r.get('done', [])
        returns, done = [int(v) for v in returns], [int(v) for v in done]
        check(len(returns) == 3 and len(done) == 3 and all(d - 10 < r < d for r, d in zip(returns[1:], done)),
              f"apb dst: each posted write holds the next request() until the sample point before the edge the "
              f"HDL completes it (returns={returns} done={done})")

        # The model sends R on axiRdSrc, AR on axiRdDst, B on axiWrSrc and AW
        # and W on axiWrDst; the HDL sends the rest.
        for scenario, pairs in [('axiRdSrc', [('arHdl', 'arModel', False), ('rHdl', 'rModel', True)]),
                                ('axiRdDst', [('arHdl', 'arModel', True), ('rHdl', 'rModel', False)]),
                                ('axiWrSrc', [('awHdl', 'awModel', False), ('wHdl', 'wModel', False), ('bHdl', 'bModel', True)]),
                                ('axiWrDst', [('awHdl', 'awModel', True), ('wHdl', 'wModel', True), ('bHdl', 'bModel', False)])]:
            r = rec.get(scenario, {})
            for hdl, model, modelSends in pairs:
                hdlNs, modelNs = [int(v) for v in r.get(hdl, [])], [int(v) for v in r.get(model, [])]
                if modelSends:
                    check(len(hdlNs) == 4 and len(modelNs) == 4 and all(h - 10 < m < h for h, m in zip(hdlNs, modelNs)),
                          f"{scenario}: every {hdl[:-3].upper()} send returns at the sample point before the edge the "
                          f"HDL takes the beat (hdl={hdlNs} model={modelNs})")
                else:
                    check(len(hdlNs) == 4 and hdlNs == modelNs,
                          f"{scenario}: every {hdl[:-3].upper()} beat reaches the model on the edge the HDL transfers it "
                          f"(hdl={hdlNs} model={modelNs})")

        times = [int(v) for v in rec.get('pacedClockRate', {}).get('times', [])]
        check(len(times) == 40 and sorted({b - a for a, b in zip(times, times[1:])}) == [10]
              and logged(output, 'pacedClock', PACED) == [],
              f"pacedClock: a writer that waits on the clock between writes moves one beat per clock behind a dst "
              f"BFM and is not reported (times={times[:6]}...)")
        times = [int(v) for v in rec.get('pacedRead', {}).get('times', [])]
        check(len(times) == 8 and sorted({b - a for a, b in zip(times, times[1:])}) == [20],
              f"pacedRead: a reader that waits on the clock after each read leaves rdy low one clock in two "
              f"(times={times})")
        for scenario in ['rvRelayFull', 'axRelayFull']:
            r = rec.get(scenario, {})
            out = [int(v) for v in r.get('out', [])]
            check(len(out) == 16 and sorted({b - a for a, b in zip(out, out[1:])}) == [10]
                  and r.get('vals') == [str(k) for k in range(16)],
                  f"{scenario}: a read-then-write model moves one beat per clock into an always-ready sink "
                  f"(out={out[:6]}... vals={r.get('vals', [])[:6]}...)")
        for scenario in ['rvRelayHalf', 'axRelayHalf']:
            trace = re.search(rf'^trace {scenario} in=(\d*) out=(\d*)$', output, re.M)
            # The empty model takes its first beat before the sink is ready,
            # so the traces agree once that beat is in the model.
            check(trace is not None and len(trace.group(1)) == 12 and trace.group(1)[2:] == trace.group(2)[2:],
                  f"{scenario}: into a sink ready on odd clocks, in.rdy follows out.rdy once the model holds a "
                  f"beat, as RTL whose in.rdy is out.rdy does (in={trace.group(1) if trace else None} "
                  f"out={trace.group(2) if trace else None})")
            r = rec.get(scenario, {})
            check(r.get('vals') == [str(k) for k in range(len(r.get('vals', [])))] and len(r.get('vals', [])) >= 8,
                  f"{scenario}: every beat arrives in order (vals={r.get('vals')})")
        r = rec.get('axiRdSlaveRate', {})
        ar, rb = [int(v) for v in r.get('ar', [])], [int(v) for v in r.get('r', [])]
        check(len(ar) == 8 and sorted({b - a for a, b in zip(ar, ar[1:])}) == [10]
              and len(rb) == 8 and sorted({b - a for a, b in zip(rb, rb[1:])}) == [10],
              f"axiRdSlaveRate: a slave model that takes an address and sends its R beat takes an address and "
              f"returns a beat on every clock (ar={ar} r={rb})")
        six = [str(k) for k in range(6)]
        check(rec.get('loweredRdy', {}).get('vals') == six,
              f"loweredRdy: the beat whose rdy fell after its send completed is still delivered, in order "
              f"(vals={rec.get('loweredRdy', {}).get('vals')})")
        check(len(logged(output, 'loweredRdy', LOWERED)) == 2 and len(queued(output, 'loweredRdy', LOWERED)) == 1
              and any('at 80 ns' in line for line in logged(output, 'loweredRdy', LOWERED)),
              f"loweredRdy: rdy lowered in the low phase outside reset logs the break at the 80 ns edge and "
              f"queues it once (got {logged(output, 'loweredRdy', LOWERED)})")
        check(rec.get('loweredReset', {}).get('vals') == six,
              f"loweredReset: under a reset that asserts after the send completed, the beat is delivered after "
              f"reset, in order (vals={rec.get('loweredReset', {}).get('vals')})")
        check(logged(output, 'loweredReset', LOWERED) == [] and queued(output, 'loweredReset', LOWERED) == [],
              "loweredReset: a reset that lowers rdy after the send completed breaks nothing")
        for scenario, gap, rdata in [('pushDstRate', 10, None), ('notifyDstRate', 10, None),
                                     ('reqDstRate', 20, ['80', '81', '82', '83']), ('popDstRate', 20, ['80', '81', '82', '83'])]:
            r = rec.get(scenario, {})
            returns, take = [int(v) for v in r.get('returns', [])], [int(v) for v in r.get('take', [])]
            check(len(returns) == 4 and len(take) == 4 and all(t - 10 < m < t for m, t in zip(returns, take)),
                  f"{scenario}: every model call returns at the sample point before the edge the HDL takes the "
                  f"request (returns={returns} take={take})")
            check(sorted({b - a for a, b in zip(take, take[1:])}) == [gap],
                  f"{scenario}: a zero-time model's requests transfer one per {gap // 10} clock(s) (take={take})")
            if scenario == 'pushDstRate':
                check(r.get('vals') == ['0', '1', '2', '3'], f"{scenario}: each value transfers once, in order (vals={r.get('vals')})")
            if rdata:
                check(r.get('rdata') == rdata, f"{scenario}: each call returns the rdata of its own ack (rdata={r.get('rdata')})")
            check(logged(output, scenario, LOWERED) == [], f"{scenario}: an HDL that holds ack to the edge breaks nothing")
        for scenario in ['pushDstDelay', 'reqDstDelay']:
            r = rec.get(scenario, {})
            returns, take = [int(v) for v in r.get('returns', [])], [int(v) for v in r.get('take', [])]
            check(len(take) == 4 and r.get('vals') == ['0', '1', '2', '3'] and len(returns) == 4
                  and all(m > t for m, t in zip(returns, take)),
                  f"{scenario}: a timed delay on the completion that outlasts the transfer edge still drops the "
                  f"request at that edge, so the HDL takes each request once (returns={returns} take={take} "
                  f"vals={r.get('vals')})")
        r = rec.get('pushDstLowered', {})
        check(r.get('vals') == ['0', '1', '2', '3'],
              f"pushDstLowered: the push whose ack fell after its call completed stays on the pins and transfers "
              f"once, in order (vals={r.get('vals')})")
        check(len(queued(output, 'pushDstLowered', LOWERED)) == 1
              and any('at 70 ns' in line for line in logged(output, 'pushDstLowered', LOWERED)),
              f"pushDstLowered: ack lowered in the low phase logs the break at the 70 ns edge and queues it once "
              f"(got {logged(output, 'pushDstLowered', LOWERED)})")
        r = rec.get('pushDstReset', {})
        check(r.get('vals') == ['0', '1', '2', '3'] and logged(output, 'pushDstReset', LOWERED) == []
              and queued(output, 'pushDstReset', LOWERED) == [],
              f"pushDstReset: under a reset that asserts after the push's call completed, the push transfers once "
              f"after reset, in order, and nothing breaks (vals={r.get('vals')})")
        r = rec.get('pacedMem', {})
        times = [int(v) for v in r.get('times', [])]
        check(len(times) == 40 and sorted({b - a for a, b in zip(times, times[1:])}) == [20],
              f"pacedMem: a model woken by memory_src_bfm on every other edge moves one beat per two clocks "
              f"(times={times[:6]}...)")
        check(logged(output, 'pacedMem', PACED) == [] and queued(output, 'pacedMem', PACED) == [],
              "pacedMem: a model the HDL paces through a memory port is not reported")
        if len(FAILURES) > before:
            print(output)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == '__main__':
    test_bfm_handshake_contract()
    if FAILURES:
        print(f"\n  SOME TESTS FAILED ({len(FAILURES)})")
        sys.exit(1)
    print("\n  ALL TESTS PASSED!")
    sys.exit(0)
