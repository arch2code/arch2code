// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE
//
// One probe per BFM that makes a model call after a handshake. A SystemC thread
// stands in for the RTL and honours only the handshake rule, on a 2.5 ns clock.
// A channel subclass records each call the BFM makes. argv is
// <delay ns> <bfm> <mode>, and the probe prints what the HDL transferred, what
// the BFM passed on and what the far end got:
//   req_ack fast|slow  req_ack_dst_bfm; the RTL acks on the 1st or 3rd edge after req
//   ar seq|pipe        axi_read_src_bfm; the master issues the 2nd AR after the 1st
//                      burst's last R beat, or straight away
//   r seq|pipe         axi_read_dst_bfm; the model sends the 2nd AR after the 1st
//                      burst's last R beat, or straight away
//   b each|batch       axi_write_dst_bfm; the slave returns each B when its burst is
//                      in, or both back to back once both bursts are in
//
// The handover probes further down serve test_bfm_handover.py, with their own
// argv. They share the payload types above.

#include "systemc.h"
#include "logging.h"
#include "apb_bfm.h"
#include "axi4_stream_bfm.h"
#include "axi_read_bfm.h"
#include "axi_write_bfm.h"
#include "memory_bfm.h"
#include "notify_ack_bfm.h"
#include "pop_ack_bfm.h"
#include "push_ack_bfm.h"
#include "rdy_vld_bfm.h"
#include "req_ack_bfm.h"
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <deque>
#include <format>
#include <functional>
#include <map>
#include <memory>
#include <random>
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
using arT = axiReadAddressSt<wordSt>;
using rT = axiReadRespSt<wordSt>;
using awT = axiWriteAddressSt<wordSt>;
using wT = axiWriteDataSt<wordSt, strbSt>;
using bT = axiWriteRespSt<>;

constexpr int REQUESTS = 3;
constexpr int BURSTS = 2;
constexpr int LEN = 3;                     // four beats per burst

// req_ack_dst_bfm calls the channel through its port and the AXI BFMs find
// theirs with dynamic_cast, so a subclass sees every call either makes.
struct reqAckChan : req_ack_channel<wordSt, wordSt> {
    std::vector<std::uint64_t> bfmCalls;
    reqAckChan( const char *n ) : req_ack_channel( n, "tb" ) {}
    void ack( const wordSt &a ) override
    {
        bfmCalls.push_back( a.w );
        req_ack_channel::ack( a );
    }
};

struct arChan : axi_read_channel<wordSt, wordSt> {
    std::vector<std::uint64_t> bfmCalls;
    arChan( const char *n ) : axi_read_channel( n, "tb" ) {}
    void sendAddr( const arT &a, std::optional<std::string> s ) override
    {
        bfmCalls.push_back( a.araddr.w );
        axi_read_channel::sendAddr( a, s );
    }
};

struct rChan : axi_read_channel<wordSt, wordSt> {
    std::vector<std::uint64_t> bfmCalls;
    rChan( const char *n ) : axi_read_channel( n, "tb" ) {}
    void sendDataCycle( const rT &r ) override
    {
        bfmCalls.push_back( r.rdata.w );
        axi_read_channel::sendDataCycle( r );
    }
};

struct bChan : axi_write_channel<wordSt, wordSt, strbSt> {
    std::vector<std::uint64_t> bfmCalls;
    bChan( const char *n ) : axi_write_channel( n, "tb" ) {}
    void sendRespCycle( const bT &b ) override
    {
        bfmCalls.push_back( b.bid );
        axi_write_channel::sendRespCycle( b );
    }
};

// In every RTL thread below, values read right after an edge are the ones that
// edge sampled.

// The model makes three requests, request i carrying 0xa0 + i. The RTL starts
// an operation on an edge where it is idle and req is high, raises ack with
// rdata = data + 0x1000, holds it for one cycle, and is idle again from the
// edge that samples it.
SC_MODULE( reqAckDst )
{
    sc_in<bool> clk, rst_n;
    reqAckChan ch;
    req_ack_out<wordSt, wordSt> out;
    req_ack_hdl_if<sc_bv<32>, sc_bv<32>> hdl;
    req_ack_dst_bfm<wordSt, wordSt, sc_bv<32>, sc_bv<32>> bfm;
    int latency;
    std::vector<std::uint64_t> hdlSeen, received;

    SC_HAS_PROCESS( reqAckDst );
    reqAckDst( sc_module_name n, const std::string &mode ) :
        sc_module( n ), ch( "ch" ), out( "out" ), bfm( "bfm" ), latency( mode == "slow" ? 3 : 1 )
    {
        out( ch ); bfm.if_p( ch ); bfm.hdl_if_p( hdl ); bfm.clk( clk ); bfm.rst_n( rst_n );
        SC_THREAD( rtl ); SC_THREAD( model );
    }

    void model()
    {
        for (int i = 0; i < REQUESTS; i++) {
            wordSt d, r;
            d.w = 0xa0 + i;
            out->req( d, r );
            received.push_back( r.w );
        }
    }

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
                hdlSeen.push_back( data );
                left = latency;
            }
            if (left == 0) {
                hdl.ack = 1;
                hdl.rdata = sc_bv<32>( data + 0x1000 );
                left = -2;
            } else if (left > 0) {
                left--;
            }
        }
    }
};

// The RTL master issues two ARs. The model answers each with four R beats,
// beat i of the burst at address a carrying a / 0x10 + i.
SC_MODULE( axiReadSrc )
{
    sc_in<bool> clk, rst_n;
    arChan ch;
    axi_read_in<wordSt, wordSt> in;
    axi_read_hdl_if<sc_bv<32>, sc_bv<32>> hdl;
    axi_read_src_bfm<wordSt, wordSt, sc_bv<32>, sc_bv<32>> bfm;
    bool pipe;
    std::vector<std::uint64_t> hdlSeen, received;
    std::deque<arT> addrs;
    sc_event addrArrived;

    SC_HAS_PROCESS( axiReadSrc );
    axiReadSrc( sc_module_name n, const std::string &mode ) :
        sc_module( n ), ch( "ch" ), in( "in" ), bfm( "bfm" ), pipe( mode == "pipe" )
    {
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

    void master()
    {
        int arNext = 0, rDone = 0;
        bool arUp = false;
        hdl.rready = 1;
        while (true) {
            wait( clk.posedge_event() );
            if (!rst_n) { hdl.arvalid = 0; continue; }
            if (hdl.arvalid && hdl.arready) {
                hdlSeen.push_back( hdl.araddr.read().to_uint64() );
                arUp = false;
            }
            if (hdl.rvalid && hdl.rready) {
                received.push_back( hdl.rdata.read().to_uint64() );
                if (hdl.rlast) { rDone++; }
            }
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

// The model sends two ARs. The RTL slave accepts every AR and returns each
// burst's four R beats back to back, beat i of the burst at address a carrying
// a / 0x10 + i.
SC_MODULE( axiReadDst )
{
    sc_in<bool> clk, rst_n;
    rChan ch;
    axi_read_out<wordSt, wordSt> out;
    axi_read_hdl_if<sc_bv<32>, sc_bv<32>> hdl;
    axi_read_dst_bfm<wordSt, wordSt, sc_bv<32>, sc_bv<32>> bfm;
    bool pipe;
    int bursts = 0;
    std::vector<std::uint64_t> hdlSeen, received;
    sc_event burstDone;

    SC_HAS_PROCESS( axiReadDst );
    axiReadDst( sc_module_name n, const std::string &mode ) :
        sc_module( n ), ch( "ch" ), out( "out" ), bfm( "bfm" ), pipe( mode == "pipe" )
    {
        out( ch ); bfm.if_p( ch ); bfm.hdl_if_p( hdl ); bfm.clk( clk ); bfm.rst_n( rst_n );
        SC_THREAD( slave ); SC_THREAD( addrThread ); SC_THREAD( dataThread );
    }

    void addrThread()
    {
        for (int n = 0; n < BURSTS; n++) {
            while (!pipe && bursts < n) { wait( burstDone ); }
            arT ar;
            ar.arid = n + 1;
            ar.araddr.w = 0x1000 * (n + 1);
            ar.arlen = LEN;
            ar.arsize = 2;
            ar.arburst = AXIBURST_INCR;
            out->sendAddr( ar );
        }
    }

    void dataThread()
    {
        while (true) {
            rT r;
            out->receiveDataCycle( r );
            received.push_back( r.rdata.w );
            if (r.rlast) { bursts++; burstDone.notify(); }
        }
    }

    void slave()
    {
        std::deque<std::pair<std::uint64_t, int>> pending;
        int beat = 0;
        bool rUp = false;
        while (true) {
            wait( clk.posedge_event() );
            if (!rst_n) { hdl.arready = 0; hdl.rvalid = 0; continue; }
            hdl.arready = 1;
            if (hdl.arvalid && hdl.arready) {
                pending.emplace_back( hdl.araddr.read().to_uint64(), (int)hdl.arid.read().to_uint() );
            }
            if (hdl.rvalid && hdl.rready) {
                hdlSeen.push_back( hdl.rdata.read().to_uint64() );
                if (++beat > LEN) { beat = 0; pending.pop_front(); }
                rUp = false;
            }
            if (!rUp && !pending.empty()) {
                hdl.rvalid = 1;
                hdl.rid = pending.front().second;
                hdl.rdata = sc_bv<32>( pending.front().first / 0x10 + beat );
                hdl.rresp = 0;
                hdl.rlast = beat == LEN;
                rUp = true;
            } else if (!rUp) {
                hdl.rvalid = 0;
                hdl.rlast = 0;
            }
        }
    }
};

// The model sends two four-beat bursts without waiting for B. Burst n is at
// 0x1000 * (n + 1) with ID n + 1, and beat i carries 0x100 * (n + 1) + i. The
// RTL slave accepts every AW and W beat.
SC_MODULE( axiWriteDst )
{
    sc_in<bool> clk, rst_n;
    bChan ch;
    axi_write_out<wordSt, wordSt, strbSt> out;
    axi_write_hdl_if<sc_bv<32>, sc_bv<32>, sc_bv<4>> hdl;
    axi_write_dst_bfm<wordSt, wordSt, strbSt, sc_bv<32>, sc_bv<32>, sc_bv<4>> bfm;
    bool batch;
    std::vector<std::uint64_t> hdlSeen, received;

    SC_HAS_PROCESS( axiWriteDst );
    axiWriteDst( sc_module_name n, const std::string &mode ) :
        sc_module( n ), ch( "ch" ), out( "out" ), bfm( "bfm" ), batch( mode == "batch" )
    {
        out( ch ); bfm.if_p( ch ); bfm.hdl_if_p( hdl ); bfm.clk( clk ); bfm.rst_n( rst_n );
        SC_THREAD( slave ); SC_THREAD( addrThread ); SC_THREAD( dataThread ); SC_THREAD( respThread );
    }

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
        }
    }

    void slave()
    {
        std::deque<int> resps;
        int written = 0;
        bool bUp = false;
        while (true) {
            wait( clk.posedge_event() );
            if (!rst_n) { hdl.awready = 0; hdl.wready = 0; hdl.bvalid = 0; continue; }
            hdl.awready = 1;
            hdl.wready = 1;
            if (hdl.wvalid && hdl.wready && hdl.wlast) {
                resps.push_back( (int)hdl.wid.read().to_uint() );
                written++;
            }
            if (hdl.bvalid && hdl.bready) {
                hdlSeen.push_back( hdl.bid.read().to_uint() );
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

template <class DUT>
struct probe : sc_module
{
    sc_clock clk;
    sc_signal<bool> rst_n;
    DUT dut;
    int delayNs;

    SC_HAS_PROCESS( probe );
    probe( sc_module_name n, int delayNs_, const std::string &mode ) :
        sc_module( n ), clk( "clk", 2500, SC_PS ), dut( "dut", mode ), delayNs( delayNs_ )
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
        std::printf( "delayed hdl=%s bfm=%s recv=%s\n", list( dut.hdlSeen ).c_str(),
                     list( dut.ch.bfmCalls ).c_str(), list( dut.received ).c_str() );
        sc_stop();
    }
};

template <class DUT>
void runProbe( int delayNs, const std::string &mode )
{
    probe<DUT> p( "p", delayNs, mode );
    sc_start();
    std::printf( "probe done\n" );
}

// ---------------------------------------------------------------------------
// Handover probes. Each run puts one BFM, in one direction, against one
// stand-in RTL behaviour, on a 10 ns clock with reset released at 25 ns. argv
// is <delay ns> <family> <dir> <rtl> <busy ns> <bp>:
//   family  rv, rvmulti (rdy_vld with 4-beat ping-pong bursts), axis, and the
//           AXI channels ar, r, aw, w, b; wfirst (w src with the W beats on
//           the wire 30 ns before the AW); then popack, pushack, notifyack,
//           reqack, apb and mem
//   dir     dst: the model starts the transfer and the RTL receives it;
//           src: the RTL starts it
//   rtl     how the stand-in drives rdy (dst) or vld (src): always, hold (low
//           for 70 ns from the lane's start), every3 (on every third edge;
//           a src offer comes three or more edges after the last
//           handshake), random (seeded), comb (rdy follows vld, or vld
//           follows rdy), reset (high, with reset asserted again from 45 to
//           65 ns after the lane's start). Against always the src model
//           first reads half a clock after vld rises; src only:
//           waiting (vld rises only after the model is in read()) and
//           parked (the model first reads 15 ns after vld rises, so beat 0
//           sits on the wire across an edge)
//   busy    ns the src model spends after each read
//   bp      allowed or none
// A lane starts on the edge at or before the model's first send (dst), or on
// the first edge the RTL may offer a beat (src), so the B lane meets the hold
// and the reset too.
// The probe prints one line per event, "ev <kind> <value> <ps>":
//   call, ret  a model call starts and returns; ret carries the value read
//   vld        the wire shows vld with this beat
//   hs         the RTL takes or hands over a beat on this edge
//   rst        an edge the mid-run reset covers
//   rsths      a src RTL sees vld and ready high on a reset edge, with this beat
//   req, ack   non-handshake RTL: it starts an operation, or the operation
//              completes on this edge
// After the run it prints "probe done", then "probe assert <message>" if a
// Q_ASSERT stopped the run.

constexpr int BEATS = 8;
constexpr int OPS = 4;

struct runCfg {
    int delayNs = 0;
    std::string family, dir, rtl;
    int busyNs = 0;
    bool noBp = false;
};

void logEv( const char *kind, std::uint64_t value )
{
    std::printf( "ev %s %llu %llu\n", kind, (unsigned long long)value, (unsigned long long)sc_time_stamp().value() );
}

bool pastNs( int ns ) { return sc_time_stamp() >= sc_time( ns, SC_NS ); }

// One handshake lane on the wire: its vld and rdy, the beat it carries, and
// how an RTL sender puts beat n on it.
struct lane {
    sc_signal<bool> &vld, &rdy;
    std::function<std::uint64_t()> beat;
    std::function<void( int )> drive;
    const sc_event &dataEv;
};

struct handoverBase : sc_module
{
    sc_in<bool> clk, rst_n;
    runCfg cfg;
    portBase *timed = nullptr;
    sc_time laneStart;
    sc_event started;
    bool modelReading = false;

    handoverBase( sc_module_name n, const runCfg &c ) : sc_module( n ), cfg( c ) {}

    // --delay N --delayMode fixedInit reaches the channel this way.
    void start_of_simulation() override
    {
        if (cfg.delayNs > 0) { timed->setTimed( cfg.delayNs, TIMED_DELAY_FIXED_INIT ); }
    }

    void waitEdge() { wait( clk.posedge_event() ); }

    // The hold and the mid-run reset count from the edge at or before the
    // lane's first send or offer.
    void startLane()
    {
        if (laneStart != SC_ZERO_TIME) { return; }
        laneStart = sc_time( double( sc_time_stamp().value() / 10000 * 10000 ), SC_PS );
        started.notify();
    }

    bool holdOver() { return laneStart != SC_ZERO_TIME && sc_time_stamp() >= laneStart + sc_time( 70, SC_NS ); }

    // The model runs setup, then writes beats 0..BEATS-1 back to back.
    void measureDst( lane l, std::function<void()> setup, std::function<void( int )> send )
    {
        sc_spawn( [this, setup, send] {
            wait( 33, SC_NS );
            if (setup) { setup(); }
            startLane();
            for (int k = 0; k < BEATS; k++) {
                logEv( "call", k );
                send( k );
                logEv( "ret", k );
            }
        } );
        sc_spawn( [this, l] { receiver( l ); } );
        if (cfg.rtl == "comb") {
            sc_spawn( [l] { while (true) { l.rdy = l.vld.read(); sc_core::wait( l.vld.value_changed_event() ); } } );
        }
        sc_spawn( [l] { monitor( l ); } );
    }

    // The model runs setup, then reads BEATS beats, busy for busyNs after each.
    void measureSrc( lane l, std::function<void()> setup, std::function<std::uint64_t()> recv,
                     std::function<bool()> go )
    {
        sc_spawn( [this, l, setup, recv] {
            wait( 33, SC_NS );
            if (setup) { setup(); }
            if (cfg.rtl == "always" || cfg.rtl == "parked") {
                if (!l.vld) { wait( l.vld.posedge_event() ); }
                wait( cfg.rtl == "always" ? 5 : 15, SC_NS );
            }
            modelReading = true;
            for (int k = 0; k < BEATS; k++) {
                logEv( "call", k );
                logEv( "ret", recv() );
                if (cfg.busyNs) { wait( cfg.busyNs, SC_NS ); }
            }
        } );
        if (cfg.rtl == "comb") {
            sc_spawn( [this, l, go] { combSender( l, go ); } );
        } else {
            sc_spawn( [this, l, go] { sender( l, go ); } );
        }
        sc_spawn( [l] { monitor( l ); } );
    }

    static void monitor( lane l )
    {
        while (true) {
            sc_core::wait( l.vld.value_changed_event() | l.dataEv );
            if (l.vld) { logEv( "vld", l.beat() ); }
        }
    }

    // The RTL receiver counts a handshake on an edge out of reset with vld and
    // rdy high. In reset it keeps rdy, as a FIFO whose rdy is !full does.
    void receiver( lane l )
    {
        std::mt19937 rng( 1 );
        if (cfg.rtl != "comb") { l.rdy = cfg.rtl == "always" || cfg.rtl == "reset"; }
        for (int edge = 1;; edge++) {
            waitEdge();
            if (rst_n && l.vld && l.rdy) { logEv( "hs", l.beat() ); }
            if (cfg.rtl == "hold") { l.rdy = holdOver(); }
            if (cfg.rtl == "every3") { l.rdy = edge % 3 == 0; }
            if (cfg.rtl == "random") { l.rdy = rng() & 1; }
        }
    }

    // The RTL sender offers beats 0..BEATS-1 once go() allows, and holds an
    // offered beat until it is taken. Reset drops vld and keeps the count.
    void sender( lane l, std::function<bool()> go )
    {
        std::mt19937 rng( 1 );
        int n = 0, lastHs = -3;
        for (int edge = 1;; edge++) {
            waitEdge();
            if (!rst_n) {
                if (l.vld && l.rdy) { logEv( "rsths", l.beat() ); }
                l.vld = false;
                continue;
            }
            if (l.vld && l.rdy) {
                logEv( "hs", l.beat() );
                n++;
                lastHs = edge;
            } else if (l.vld) {
                continue;
            }
            if (go()) { startLane(); }
            bool offer = cfg.rtl == "hold" ? holdOver() : cfg.rtl == "every3" ? edge % 3 == 0 && edge - lastHs >= 3
                       : cfg.rtl == "random" ? bool( rng() & 1 ) : cfg.rtl == "waiting" ? modelReading : true;
            l.vld = offer && n < BEATS && go();
            l.drive( n );
        }
    }

    // vld = rdy && a beat is left, re-evaluated whenever rdy or reset changes.
    void combSender( lane l, std::function<bool()> go )
    {
        int n = 0;
        while (true) {
            wait( clk.posedge_event() | l.rdy.value_changed_event() | rst_n.value_changed_event() );
            if (clk.posedge() && rst_n && l.vld && l.rdy) {
                logEv( "hs", l.beat() );
                n++;
            }
            if (rst_n && go()) { startLane(); }
            l.vld = rst_n && l.rdy && n < BEATS && go();
            l.drive( n );
        }
    }

    // Offers count items, unmeasured, with three idle edges after each
    // handshake, more than a 15 ns delay. sent, if given, counts the
    // handshakes, and a reader on the same edge sees the count from the edge
    // before.
    void issue( sc_signal<bool> &vld, sc_signal<bool> &rdy, int count, std::function<void( int )> drive,
                sc_signal<int> *sent = nullptr )
    {
        int n = 0, idle = 0;
        while (true) {
            waitEdge();
            if (!rst_n) { vld = false; continue; }
            if (vld && rdy) {
                n++;
                idle = 3;
                if (sent) { *sent = n; }
            }
            vld = n < count && idle-- <= 0;
            drive( n );
        }
    }

    // Always ready, unmeasured; taken, if given, counts the handshakes, as
    // issue() does.
    void accept( sc_signal<bool> &vld, sc_signal<bool> &rdy, sc_signal<int> *taken = nullptr )
    {
        rdy = true;
        int n = 0;
        while (true) {
            waitEdge();
            if (rst_n && vld && rdy) {
                n++;
                if (taken) { *taken = n; }
            }
        }
    }

    // A model that makes OPS requests from 33 ns; op returns the value it got.
    void modelRequests( std::function<std::uint64_t( int )> op )
    {
        sc_spawn( [op] {
            sc_core::wait( 33, SC_NS );
            for (int k = 0; k < OPS; k++) {
                logEv( "call", k );
                logEv( "ret", op( k ) );
            }
        } );
    }

    // A model that serves OPS requests: receive takes the request, complete
    // answers request k.
    void modelServes( std::function<void()> receive, std::function<void( int )> complete )
    {
        sc_spawn( [receive, complete] {
            for (int k = 0; k < OPS; k++) {
                receive();
                logEv( "call", k );
                complete( k );
                logEv( "ret", k );
            }
        } );
    }

    // The RTL responder starts an operation on an edge where it is idle and
    // sees req, raises ack on the next edge and drops it on the edge after.
    void responder( sc_signal<bool> &req, sc_signal<bool> &ack, std::function<std::uint64_t( int )> reqValue,
                    std::function<void( int )> driveRdata )
    {
        int n = 0, state = 0;
        while (true) {
            waitEdge();
            if (!rst_n) { ack = false; state = 0; continue; }
            if (state == 2) {
                logEv( "ack", n++ );
                ack = false;
                state = 0;
            } else if (state == 1) {
                ack = true;
                if (driveRdata) { driveRdata( n ); }
                state = 2;
            } else if (req) {
                logEv( "req", reqValue( n ) );
                state = 1;
            }
        }
    }

    // The RTL requester raises req for item n, holds it until it samples ack,
    // and drops it for at least one edge.
    void requester( sc_signal<bool> &req, sc_signal<bool> &ack, std::function<void( int )> drive,
                    std::function<std::uint64_t( int )> ackValue )
    {
        int n = 0;
        while (true) {
            waitEdge();
            if (!rst_n) { req = false; continue; }
            if (req && ack) {
                logEv( "ack", ackValue( n++ ) );
                req = false;
            } else if (!req && n < OPS) {
                logEv( "req", n );
                req = true;
                if (drive) { drive( n ); }
            }
        }
    }
};

// rdy_vld and axi4_stream

using rvHdl = rdy_vld_hdl_if<sc_bv<32>>;
using axisT = axi4StreamInfoSt<wordSt, wordSt, wordSt>;
using axisChan = axi4_stream_channel<wordSt, wordSt, wordSt>;
using axisHdl = axi4_stream_hdl_if<sc_bv<32>, sc_bv<32>, sc_bv<32>, sc_bv<4>, sc_bv<4>>;

lane rvLane( rvHdl &h )
{
    return { h.vld, h.rdy, [&h] { return h.data.read().to_uint64(); },
             [&h]( int n ) { h.data = sc_bv<32>( n ); }, h.data.value_changed_event() };
}

lane axisLane( axisHdl &h )
{
    return { h.tvalid, h.tready, [&h] { return h.tdata.read().to_uint64(); },
             [&h]( int n ) { h.tdata = sc_bv<32>( n ); }, h.tdata.value_changed_event() };
}

channelBackpressure backpressure( const runCfg &c ) { return c.noBp ? BACKPRESSURE_NONE : BACKPRESSURE_ALLOWED; }

// rvmulti carries four-beat transactions. The ping-pong buffer adds a beat
// less one byte to the size it is given, so 25 bytes become 32.
std::unique_ptr<rdy_vld_channel<wordSt>> rvChannel( const runCfg &c )
{
    if (c.family == "rvmulti") {
        return std::make_unique<rdy_vld_channel<wordSt>>( "ch", "tb", backpressure( c ), "fixed_size",
                                                          3 * sizeof( wordSt ) + 1, "" );
    }
    return std::make_unique<rdy_vld_channel<wordSt>>( "ch", "tb", backpressure( c ) );
}

struct rvDst : handoverBase
{
    std::unique_ptr<rdy_vld_channel<wordSt>> ch;
    rdy_vld_out<wordSt> out;
    rvHdl hdl;
    rdy_vld_dst_bfm<wordSt, sc_bv<32>> bfm;

    rvDst( sc_module_name n, const runCfg &c ) : handoverBase( n, c ), ch( rvChannel( c ) ), out( "out" ), bfm( "bfm" )
    {
        timed = ch.get();
        out( *ch ); bfm.if_p( *ch ); bfm.hdl_if_p( hdl ); bfm.clk( clk ); bfm.rst_n( rst_n );
        measureDst( rvLane( hdl ), {}, [this]( int k ) {
            wordSt v;
            v.w = k;
            if (cfg.family == "rvmulti") { out->writeClocked( v ); } else { out->write( v ); }
        } );
    }
};

struct rvSrc : handoverBase
{
    std::unique_ptr<rdy_vld_channel<wordSt>> ch;
    rdy_vld_in<wordSt> in;
    rvHdl hdl;
    rdy_vld_src_bfm<wordSt, sc_bv<32>> bfm;

    rvSrc( sc_module_name n, const runCfg &c ) : handoverBase( n, c ), ch( rvChannel( c ) ), in( "in" ), bfm( "bfm" )
    {
        timed = ch.get();
        in( *ch ); bfm.if_p( *ch ); bfm.hdl_if_p( hdl ); bfm.clk( clk ); bfm.rst_n( rst_n );
        measureSrc( rvLane( hdl ), {}, [this] {
            wordSt v;
            if (cfg.family == "rvmulti") { in->readClocked( v ); } else { in->read( v ); }
            return v.w;
        }, [] { return true; } );
    }
};

struct axisDst : handoverBase
{
    axisChan ch;
    axi4_stream_out<wordSt, wordSt, wordSt> out;
    axisHdl hdl;
    axi4_stream_dst_bfm<wordSt, wordSt, wordSt, sc_bv<32>, sc_bv<32>, sc_bv<32>, sc_bv<4>, sc_bv<4>> bfm;

    axisDst( sc_module_name n, const runCfg &c ) :
        handoverBase( n, c ), ch( "ch", "tb", backpressure( c ) ), out( "out" ), bfm( "bfm" )
    {
        timed = &ch;
        out( ch ); bfm.if_p( ch ); bfm.hdl_if_p( hdl ); bfm.clk( clk ); bfm.rst_n( rst_n );
        measureDst( axisLane( hdl ), {}, [this]( int k ) {
            axisT s;
            s.tdata.w = k;
            s.tlast = false;
            out->sendInfo( s );
        } );
    }
};

struct axisSrc : handoverBase
{
    axisChan ch;
    axi4_stream_in<wordSt, wordSt, wordSt> in;
    axisHdl hdl;
    axi4_stream_src_bfm<wordSt, wordSt, wordSt, sc_bv<32>, sc_bv<32>, sc_bv<32>, sc_bv<4>, sc_bv<4>> bfm;

    axisSrc( sc_module_name n, const runCfg &c ) :
        handoverBase( n, c ), ch( "ch", "tb", backpressure( c ) ), in( "in" ), bfm( "bfm" )
    {
        timed = &ch;
        in( ch ); bfm.if_p( ch ); bfm.hdl_if_p( hdl ); bfm.clk( clk ); bfm.rst_n( rst_n );
        measureSrc( axisLane( hdl ), {}, [this] {
            axisT s;
            in->receiveInfo( s );
            return s.tdata.w;
        }, [] { return true; } );
    }
};

// AXI read: AR and R. One AR of BEATS beats opens the R runs.

using rdChan = axi_read_channel<wordSt, wordSt>;
using rdHdl = axi_read_hdl_if<sc_bv<32>, sc_bv<32>>;
using rdSrcBfm = axi_read_src_bfm<wordSt, wordSt, sc_bv<32>, sc_bv<32>>;
using rdDstBfm = axi_read_dst_bfm<wordSt, wordSt, sc_bv<32>, sc_bv<32>>;

arT makeAr( int addr, int len )
{
    arT a;
    a.arid = 1;
    a.araddr.w = addr;
    a.arlen = len;
    a.arsize = 2;
    a.arburst = AXIBURST_INCR;
    return a;
}

void driveAr( rdHdl &h, int addr, int len )
{
    h.arid = 1;
    h.araddr = sc_bv<32>( addr );
    h.arlen = len;
    h.arsize = 2;
    h.arburst = 1;
}

lane arLane( rdHdl &h )
{
    return { h.arvalid, h.arready, [&h] { return h.araddr.read().to_uint64(); },
             [&h]( int n ) { driveAr( h, n, 0 ); }, h.araddr.value_changed_event() };
}

lane rLane( rdHdl &h )
{
    return { h.rvalid, h.rready, [&h] { return h.rdata.read().to_uint64(); },
             [&h]( int n ) { h.rid = 1; h.rdata = sc_bv<32>( n ); h.rresp = 0; h.rlast = n == BEATS - 1; },
             h.rdata.value_changed_event() };
}

struct arDst : handoverBase
{
    rdChan ch;
    axi_read_out<wordSt, wordSt> out;
    rdHdl hdl;
    rdDstBfm bfm;

    arDst( sc_module_name n, const runCfg &c ) : handoverBase( n, c ), ch( "ch", "tb" ), out( "out" ), bfm( "bfm" )
    {
        timed = &ch;
        out( ch ); bfm.if_p( ch ); bfm.hdl_if_p( hdl ); bfm.clk( clk ); bfm.rst_n( rst_n );
        measureDst( arLane( hdl ), {}, [this]( int k ) { out->sendAddr( makeAr( k, 0 ) ); } );
    }
};

struct arSrc : handoverBase
{
    rdChan ch;
    axi_read_in<wordSt, wordSt> in;
    rdHdl hdl;
    rdSrcBfm bfm;

    arSrc( sc_module_name n, const runCfg &c ) : handoverBase( n, c ), ch( "ch", "tb" ), in( "in" ), bfm( "bfm" )
    {
        timed = &ch;
        in( ch ); bfm.if_p( ch ); bfm.hdl_if_p( hdl ); bfm.clk( clk ); bfm.rst_n( rst_n );
        measureSrc( arLane( hdl ), {}, [this] {
            arT a;
            in->receiveAddr( a );
            return a.araddr.w;
        }, [] { return true; } );
    }
};

struct rDst : handoverBase
{
    rdChan ch;
    axi_read_in<wordSt, wordSt> in;
    rdHdl hdl;
    rdSrcBfm bfm;

    rDst( sc_module_name n, const runCfg &c ) : handoverBase( n, c ), ch( "ch", "tb" ), in( "in" ), bfm( "bfm" )
    {
        timed = &ch;
        in( ch ); bfm.if_p( ch ); bfm.hdl_if_p( hdl ); bfm.clk( clk ); bfm.rst_n( rst_n );
        sc_spawn( [this] { issue( hdl.arvalid, hdl.arready, 1, [this]( int ) { driveAr( hdl, 0x1000, BEATS - 1 ); } ); } );
        measureDst( rLane( hdl ), [this] { arT a; in->receiveAddr( a ); }, [this]( int k ) {
            rT r;
            r.rid = 1;
            r.rdata.w = k;
            r.rresp = AXIRESP_OKAY;
            r.rlast = k == BEATS - 1;
            in->sendDataCycle( r );
        } );
    }
};

struct rSrc : handoverBase
{
    rdChan ch;
    axi_read_out<wordSt, wordSt> out;
    rdHdl hdl;
    rdDstBfm bfm;
    sc_signal<int> arTaken;

    rSrc( sc_module_name n, const runCfg &c ) : handoverBase( n, c ), ch( "ch", "tb" ), out( "out" ), bfm( "bfm" )
    {
        timed = &ch;
        out( ch ); bfm.if_p( ch ); bfm.hdl_if_p( hdl ); bfm.clk( clk ); bfm.rst_n( rst_n );
        sc_spawn( [this] { accept( hdl.arvalid, hdl.arready, &arTaken ); } );
        measureSrc( rLane( hdl ), [this] { out->sendAddr( makeAr( 0x1000, BEATS - 1 ) ); }, [this] {
            rT r;
            out->receiveDataCycle( r );
            return r.rdata.w;
        }, [this] { return arTaken > 0; } );
    }
};

// AXI write: AW, W and B. B carries the burst number as its ID.

using wrChan = axi_write_channel<wordSt, wordSt, strbSt>;
using wrHdl = axi_write_hdl_if<sc_bv<32>, sc_bv<32>, sc_bv<4>>;
using wrSrcBfm = axi_write_src_bfm<wordSt, wordSt, strbSt, sc_bv<32>, sc_bv<32>, sc_bv<4>>;
using wrDstBfm = axi_write_dst_bfm<wordSt, wordSt, strbSt, sc_bv<32>, sc_bv<32>, sc_bv<4>>;

awT makeAw( int id, int addr, int len )
{
    awT a;
    a.awid = id;
    a.awaddr.w = addr;
    a.awlen = len;
    a.awsize = 2;
    a.awburst = AXIBURST_INCR;
    return a;
}

wT makeW( int id, int data, bool last )
{
    wT w;
    w.wid = id;
    w.wdata.w = data;
    w.wstrb.w = 0xf;
    w.wlast = last;
    return w;
}

void driveAw( wrHdl &h, int id, int addr, int len )
{
    h.awid = id;
    h.awaddr = sc_bv<32>( addr );
    h.awlen = len;
    h.awsize = 2;
    h.awburst = 1;
}

void driveW( wrHdl &h, int id, int data, bool last )
{
    h.wid = id;
    h.wdata = sc_bv<32>( data );
    h.wstrb = sc_bv<4>( 0xf );
    h.wlast = last;
}

lane awLane( wrHdl &h )
{
    return { h.awvalid, h.awready, [&h] { return h.awaddr.read().to_uint64(); },
             [&h]( int n ) { driveAw( h, 1, n, 0 ); }, h.awaddr.value_changed_event() };
}

lane wLane( wrHdl &h )
{
    return { h.wvalid, h.wready, [&h] { return h.wdata.read().to_uint64(); },
             [&h]( int n ) { driveW( h, 1, n, n == BEATS - 1 ); }, h.wdata.value_changed_event() };
}

lane bLane( wrHdl &h )
{
    return { h.bvalid, h.bready, [&h] { return h.bid.read().to_uint64(); },
             [&h]( int n ) { h.bid = n; h.bresp = 0; }, h.bid.value_changed_event() };
}

struct awDst : handoverBase
{
    wrChan ch;
    axi_write_out<wordSt, wordSt, strbSt> out;
    wrHdl hdl;
    wrDstBfm bfm;

    awDst( sc_module_name n, const runCfg &c ) : handoverBase( n, c ), ch( "ch", "tb" ), out( "out" ), bfm( "bfm" )
    {
        timed = &ch;
        out( ch ); bfm.if_p( ch ); bfm.hdl_if_p( hdl ); bfm.clk( clk ); bfm.rst_n( rst_n );
        measureDst( awLane( hdl ), {}, [this]( int k ) { out->sendAddr( makeAw( 1, k, 0 ) ); } );
    }
};

// A cycle-based model on the subordinate side, as the generated code makes it.
struct wrSrcBase : handoverBase
{
    wrChan ch;
    axi_write_in<wordSt, wordSt, strbSt> in;
    wrHdl hdl;
    wrSrcBfm bfm;

    wrSrcBase( sc_module_name n, const runCfg &c ) : handoverBase( n, c ), ch( "ch", "tb" ), in( "in" ), bfm( "bfm" )
    {
        timed = &ch;
        in( ch ); bfm.if_p( ch ); bfm.hdl_if_p( hdl ); bfm.clk( clk ); bfm.rst_n( rst_n );
    }

    void end_of_elaboration() override { in->setCycleTransaction( PORTTYPE_IN ); }
};

struct awSrc : wrSrcBase
{
    awSrc( sc_module_name n, const runCfg &c ) : wrSrcBase( n, c )
    {
        measureSrc( awLane( hdl ), {}, [this] {
            awT a;
            in->receiveAddr( a );
            return a.awaddr.w;
        }, [] { return true; } );
    }
};

struct wDst : handoverBase
{
    wrChan ch;
    axi_write_out<wordSt, wordSt, strbSt> out;
    wrHdl hdl;
    wrDstBfm bfm;

    wDst( sc_module_name n, const runCfg &c ) : handoverBase( n, c ), ch( "ch", "tb" ), out( "out" ), bfm( "bfm" )
    {
        timed = &ch;
        out( ch ); bfm.if_p( ch ); bfm.hdl_if_p( hdl ); bfm.clk( clk ); bfm.rst_n( rst_n );
        sc_spawn( [this] { accept( hdl.awvalid, hdl.awready ); } );
        measureDst( wLane( hdl ), [this] { out->sendAddr( makeAw( 1, 0x1000, BEATS - 1 ) ); },
                    [this]( int k ) { out->sendDataCycle( makeW( 1, k, k == BEATS - 1 ) ); } );
    }
};

struct wSrc : wrSrcBase
{
    sc_signal<int> awSent;

    wSrc( sc_module_name n, const runCfg &c ) : wrSrcBase( n, c )
    {
        sc_spawn( [this] {
            if (cfg.family == "wfirst") { wait( 60, SC_NS ); }
            issue( hdl.awvalid, hdl.awready, 1, [this]( int ) { driveAw( hdl, 1, 0x1000, BEATS - 1 ); }, &awSent );
        } );
        measureSrc( wLane( hdl ), [this] { awT a; in->receiveAddr( a ); }, [this] {
            wT w;
            in->receiveDataCycle( w );
            return w.wdata.w;
        }, [this] { return cfg.family == "wfirst" || awSent > 0; } );
    }
};

// The RTL manager writes BEATS one-beat bursts. The model takes them all, then
// returns the BEATS responses back to back.
struct bDst : wrSrcBase
{

    bDst( sc_module_name n, const runCfg &c ) : wrSrcBase( n, c )
    {
        sc_spawn( [this] { issue( hdl.awvalid, hdl.awready, BEATS, [this]( int i ) { driveAw( hdl, i, i, 0 ); } ); } );
        sc_spawn( [this] { issue( hdl.wvalid, hdl.wready, BEATS, [this]( int i ) { driveW( hdl, i, i, true ); } ); } );
        measureDst( bLane( hdl ), [this] {
            for (int i = 0; i < BEATS; i++) {
                awT a;
                wT w;
                in->receiveAddr( a );
                in->receiveDataCycle( w );
            }
        }, [this]( int k ) {
            bT b;
            b.bid = k;
            b.bresp = AXIRESP_OKAY;
            in->sendRespCycle( b );
        } );
    }
};

// The model writes BEATS one-beat bursts. The RTL subordinate returns their
// responses once every burst is in.
struct bSrc : handoverBase
{
    wrChan ch;
    axi_write_out<wordSt, wordSt, strbSt> out;
    wrHdl hdl;
    wrDstBfm bfm;
    sc_signal<int> wTaken;

    bSrc( sc_module_name n, const runCfg &c ) : handoverBase( n, c ), ch( "ch", "tb" ), out( "out" ), bfm( "bfm" )
    {
        timed = &ch;
        out( ch ); bfm.if_p( ch ); bfm.hdl_if_p( hdl ); bfm.clk( clk ); bfm.rst_n( rst_n );
        sc_spawn( [this] { wait( 33, SC_NS ); for (int i = 0; i < BEATS; i++) { out->sendAddr( makeAw( i, i, 0 ) ); } } );
        sc_spawn( [this] { wait( 33, SC_NS ); for (int i = 0; i < BEATS; i++) { out->sendDataCycle( makeW( i, i, true ) ); } } );
        sc_spawn( [this] { accept( hdl.awvalid, hdl.awready ); } );
        sc_spawn( [this] { accept( hdl.wvalid, hdl.wready, &wTaken ); } );
        measureSrc( bLane( hdl ), {}, [this] {
            bT b;
            out->receiveResp( b );
            return std::uint64_t( b.bid );
        }, [this] { return wTaken == BEATS; } );
    }
};

// pop_ack, push_ack, notify_ack and req_ack. The RTL returns n as the data of
// operation n.

using popHdl = pop_ack_hdl_if<sc_bv<32>>;
using pushHdl = push_ack_hdl_if<sc_bv<32>>;
using reqHdl = req_ack_hdl_if<sc_bv<32>, sc_bv<32>>;

struct popAckDst : handoverBase
{
    pop_ack_channel<wordSt> ch;
    pop_ack_out<wordSt> out;
    popHdl hdl;
    pop_ack_dst_bfm<wordSt, sc_bv<32>> bfm;

    popAckDst( sc_module_name n, const runCfg &c ) : handoverBase( n, c ), ch( "ch", "tb" ), out( "out" ), bfm( "bfm" )
    {
        timed = &ch;
        out( ch ); bfm.if_p( ch ); bfm.hdl_if_p( hdl ); bfm.clk( clk ); bfm.rst_n( rst_n );
        modelRequests( [this]( int ) { wordSt r; out->pop( r ); return r.w; } );
        sc_spawn( [this] { responder( hdl.pop, hdl.ack, []( int i ) { return i; },
                                      [this]( int i ) { hdl.rdata = sc_bv<32>( i ); } ); } );
    }
};

struct popAckSrc : handoverBase
{
    pop_ack_channel<wordSt> ch;
    pop_ack_in<wordSt> in;
    popHdl hdl;
    pop_ack_src_bfm<wordSt, sc_bv<32>> bfm;

    popAckSrc( sc_module_name n, const runCfg &c ) : handoverBase( n, c ), ch( "ch", "tb" ), in( "in" ), bfm( "bfm" )
    {
        timed = &ch;
        in( ch ); bfm.if_p( ch ); bfm.hdl_if_p( hdl ); bfm.clk( clk ); bfm.rst_n( rst_n );
        modelServes( [this] { in->popReceive(); }, [this]( int k ) { wordSt v; v.w = k; in->ack( v ); } );
        sc_spawn( [this] { requester( hdl.pop, hdl.ack, {}, [this]( int ) { return hdl.rdata.read().to_uint64(); } ); } );
    }
};

struct pushAckDst : handoverBase
{
    push_ack_channel<wordSt> ch;
    push_ack_out<wordSt> out;
    pushHdl hdl;
    push_ack_dst_bfm<wordSt, sc_bv<32>> bfm;

    pushAckDst( sc_module_name n, const runCfg &c ) : handoverBase( n, c ), ch( "ch", "tb" ), out( "out" ), bfm( "bfm" )
    {
        timed = &ch;
        out( ch ); bfm.if_p( ch ); bfm.hdl_if_p( hdl ); bfm.clk( clk ); bfm.rst_n( rst_n );
        modelRequests( [this]( int k ) { wordSt v; v.w = k; out->push( v ); return std::uint64_t( k ); } );
        sc_spawn( [this] { responder( hdl.push, hdl.ack, [this]( int ) { return hdl.data.read().to_uint64(); }, {} ); } );
    }
};

struct pushAckSrc : handoverBase
{
    push_ack_channel<wordSt> ch;
    push_ack_in<wordSt> in;
    pushHdl hdl;
    push_ack_src_bfm<wordSt, sc_bv<32>> bfm;

    pushAckSrc( sc_module_name n, const runCfg &c ) : handoverBase( n, c ), ch( "ch", "tb" ), in( "in" ), bfm( "bfm" )
    {
        timed = &ch;
        in( ch ); bfm.if_p( ch ); bfm.hdl_if_p( hdl ); bfm.clk( clk ); bfm.rst_n( rst_n );
        modelServes( [this] { wordSt v; in->pushReceive( v ); }, [this]( int ) { in->ack(); } );
        sc_spawn( [this] { requester( hdl.push, hdl.ack, [this]( int i ) { hdl.data = sc_bv<32>( i ); },
                                      []( int i ) { return i; } ); } );
    }
};

struct notifyAckDst : handoverBase
{
    notify_ack_channel<> ch;
    notify_ack_out<> out;
    notify_ack_hdl_if<> hdl;
    notify_ack_dst_bfm<> bfm;

    notifyAckDst( sc_module_name n, const runCfg &c ) : handoverBase( n, c ), ch( "ch", "tb" ), out( "out" ), bfm( "bfm" )
    {
        timed = &ch;
        out( ch ); bfm.if_p( ch ); bfm.hdl_if_p( hdl ); bfm.clk( clk ); bfm.rst_n( rst_n );
        modelRequests( [this]( int k ) { out->notify(); return std::uint64_t( k ); } );
        sc_spawn( [this] { responder( hdl.notify, hdl.ack, []( int i ) { return i; }, {} ); } );
    }
};

struct notifyAckSrc : handoverBase
{
    notify_ack_channel<> ch;
    notify_ack_in<> in;
    notify_ack_hdl_if<> hdl;
    notify_ack_src_bfm<> bfm;

    notifyAckSrc( sc_module_name n, const runCfg &c ) : handoverBase( n, c ), ch( "ch", "tb" ), in( "in" ), bfm( "bfm" )
    {
        timed = &ch;
        in( ch ); bfm.if_p( ch ); bfm.hdl_if_p( hdl ); bfm.clk( clk ); bfm.rst_n( rst_n );
        modelServes( [this] { in->waitNotify(); }, [this]( int ) { in->ack(); } );
        sc_spawn( [this] { requester( hdl.notify, hdl.ack, {}, []( int i ) { return i; } ); } );
    }
};

struct reqAckSrc : handoverBase
{
    req_ack_channel<wordSt, wordSt> ch;
    req_ack_in<wordSt, wordSt> in;
    reqHdl hdl;
    req_ack_src_bfm<wordSt, wordSt, sc_bv<32>, sc_bv<32>> bfm;

    reqAckSrc( sc_module_name n, const runCfg &c ) : handoverBase( n, c ), ch( "ch", "tb" ), in( "in" ), bfm( "bfm" )
    {
        timed = &ch;
        in( ch ); bfm.if_p( ch ); bfm.hdl_if_p( hdl ); bfm.clk( clk ); bfm.rst_n( rst_n );
        modelServes( [this] { wordSt d; in->reqReceive( d ); },
                     [this]( int k ) { wordSt a; a.w = k; in->ack( a ); } );
        sc_spawn( [this] { requester( hdl.req, hdl.ack, [this]( int i ) { hdl.data = sc_bv<32>( i ); },
                                      [this]( int ) { return hdl.rdata.read().to_uint64(); } ); } );
    }
};

// apb and memory. Operation k writes or reads address k / 2 + 1: writes on
// even k with data 0x11 * (k / 2 + 1), reads on odd k.

// apb_dst_bfm reads its payloads through _getAddress() and _getData().
struct apbWordSt : wordSt {
    std::uint64_t _getAddress() const { return w; }
    std::uint64_t _getData() const { return w; }
};

using apbHdl = apb_hdl_if<sc_bv<32>, sc_bv<32>>;
using memHdl = memory_hdl_if<sc_bv<32>, sc_bv<32>>;

bool opWrites( int k ) { return k % 2 == 0; }
int opAddr( int k ) { return k / 2 + 1; }
int opData( int k ) { return 0x11 * (k / 2 + 1); }

struct apbDst : handoverBase
{
    apb_channel<apbWordSt, apbWordSt> ch;
    apb_out<apbWordSt, apbWordSt> out;
    apbHdl hdl;
    apb_dst_bfm<apbWordSt, apbWordSt, sc_bv<32>, sc_bv<32>> bfm;

    apbDst( sc_module_name n, const runCfg &c ) : handoverBase( n, c ), ch( "ch", "tb" ), out( "out" ), bfm( "bfm" )
    {
        timed = &ch;
        out( ch ); bfm.if_p( ch ); bfm.hdl_if_p( hdl ); bfm.clk( clk ); bfm.rst_n( rst_n );
        modelRequests( [this]( int k ) {
            apbWordSt a, d;
            a.w = opAddr( k );
            d.w = opWrites( k ) ? opData( k ) : 0;
            out->request( opWrites( k ), a, d );
            return d.w;
        } );
        SC_THREAD( completer );
    }

    // Answers an access phase with pready on the next edge.
    SC_HAS_PROCESS( apbDst );
    void completer()
    {
        std::map<std::uint64_t, std::uint64_t> mem;
        while (true) {
            waitEdge();
            if (!rst_n) { hdl.pready = false; continue; }
            if (hdl.pready) {
                logEv( "ack", hdl.pwrite ? 0 : hdl.prdata.read().to_uint64() );
                hdl.pready = false;
            } else if (hdl.psel && hdl.penable) {
                std::uint64_t addr = hdl.paddr.read().to_uint64();
                logEv( "req", addr );
                if (hdl.pwrite) { mem[addr] = hdl.pwdata.read().to_uint64(); } else { hdl.prdata = sc_bv<32>( mem[addr] ); }
                hdl.pready = true;
            }
        }
    }
};

struct apbSrc : handoverBase
{
    apb_channel<apbWordSt, apbWordSt> ch;
    apb_in<apbWordSt, apbWordSt> in;
    apbHdl hdl;
    apb_src_bfm<apbWordSt, apbWordSt, sc_bv<32>, sc_bv<32>> bfm;
    std::map<std::uint64_t, std::uint64_t> mem;

    apbSrc( sc_module_name n, const runCfg &c ) : handoverBase( n, c ), ch( "ch", "tb" ), in( "in" ), bfm( "bfm" )
    {
        timed = &ch;
        in( ch ); bfm.if_p( ch ); bfm.hdl_if_p( hdl ); bfm.clk( clk ); bfm.rst_n( rst_n );
        SC_THREAD( model );
        SC_THREAD( manager );
    }

    SC_HAS_PROCESS( apbSrc );

    // apb_src_bfm sends every request with requestWithResponse(), so a write
    // waits for its complete() too.
    void model()
    {
        for (int k = 0; k < OPS; k++) {
            bool isWrite;
            apbWordSt a, d;
            in->reqReceive( isWrite, a, d );
            logEv( "call", k );
            if (isWrite) {
                mem[a.w] = d.w;
            } else {
                d.w = mem[a.w];
            }
            in->complete( d );
            logEv( "ret", d.w );
        }
    }

    // Setup phase, access phase, then waits for pready.
    void manager()
    {
        int k = 0, phase = 0;
        while (true) {
            waitEdge();
            if (!rst_n) { hdl.psel = false; hdl.penable = false; continue; }
            if (phase == 2 && hdl.pready) {
                logEv( "ack", opWrites( k ) ? 0 : hdl.prdata.read().to_uint64() );
                hdl.psel = false;
                hdl.penable = false;
                k++;
                phase = 0;
            } else if (phase == 1) {
                hdl.penable = true;
                phase = 2;
            } else if (phase == 0 && k < OPS) {
                logEv( "req", k );
                hdl.psel = true;
                hdl.pwrite = opWrites( k );
                hdl.paddr = sc_bv<32>( opAddr( k ) );
                hdl.pwdata = sc_bv<32>( opWrites( k ) ? opData( k ) : 0 );
                phase = 1;
            }
        }
    }
};

struct memDst : handoverBase
{
    memory_channel<wordSt, wordSt> ch;
    memory_out<wordSt, wordSt> out;
    memHdl hdl;
    memory_dst_bfm<wordSt, wordSt, sc_bv<32>, sc_bv<32>> bfm;

    memDst( sc_module_name n, const runCfg &c ) : handoverBase( n, c ), ch( "ch", "tb" ), out( "out" ), bfm( "bfm" )
    {
        timed = &ch;
        out( ch ); bfm.if_p( ch ); bfm.hdl_if_p( hdl ); bfm.clk( clk ); bfm.rst_n( rst_n );
        modelRequests( [this]( int k ) {
            wordSt a, d;
            a.w = opAddr( k );
            d.w = opWrites( k ) ? opData( k ) : 0;
            out->request( opWrites( k ), a, d );
            return d.w;
        } );
        SC_THREAD( ram );
    }

    // One access per edge with enable high; read data is registered.
    SC_HAS_PROCESS( memDst );
    void ram()
    {
        std::map<std::uint64_t, std::uint64_t> mem;
        while (true) {
            waitEdge();
            if (!rst_n || !hdl.enable) { continue; }
            std::uint64_t addr = hdl.addr.read().to_uint64();
            logEv( "req", addr );
            if (hdl.wr_en) {
                mem[addr] = hdl.write_data.read().to_uint64();
                logEv( "ack", 0 );
            } else {
                hdl.read_data = sc_bv<32>( mem[addr] );
                logEv( "ack", mem[addr] );
            }
        }
    }
};

struct memSrc : handoverBase
{
    memory_channel<wordSt, wordSt> ch;
    memory_in<wordSt, wordSt> in;
    memHdl hdl;
    memory_src_bfm<wordSt, wordSt, sc_bv<32>, sc_bv<32>> bfm;
    std::map<std::uint64_t, std::uint64_t> mem;

    memSrc( sc_module_name n, const runCfg &c ) : handoverBase( n, c ), ch( "ch", "tb" ), in( "in" ), bfm( "bfm" )
    {
        timed = &ch;
        in( ch ); bfm.if_p( ch ); bfm.hdl_if_p( hdl ); bfm.clk( clk ); bfm.rst_n( rst_n );
        modelServes( [this] {
            bool isWrite;
            wordSt a, d;
            in->reqReceive( isWrite, a, d );
            pending = { isWrite, a.w, d.w };
        }, [this]( int ) {
            if (pending.write) {
                mem[pending.addr] = pending.data;
            } else {
                wordSt d;
                d.w = mem[pending.addr];
                in->complete( d );
            }
        } );
        SC_THREAD( manager );
    }

    struct { bool write; std::uint64_t addr, data; } pending{};

    // Drives one access per edge, and reads the data of a read access on the
    // edge after the one that sampled it.
    SC_HAS_PROCESS( memSrc );
    void manager()
    {
        int k = 0, sampled = -1;
        while (true) {
            waitEdge();
            if (!rst_n) { hdl.enable = false; continue; }
            if (sampled >= 0) {
                logEv( "ack", opWrites( sampled ) ? 0 : hdl.read_data.read().to_uint64() );
                sampled = -1;
            }
            if (hdl.enable) {
                logEv( "req", k );
                sampled = k++;
            }
            hdl.enable = k < OPS;
            hdl.wr_en = opWrites( k );
            hdl.addr = sc_bv<32>( opAddr( k ) );
            hdl.write_data = sc_bv<32>( opWrites( k ) ? opData( k ) : 0 );
        }
    }
};

// The mid-run reset starts 45 ns after the lane's start. In the delayed src
// runs of rv, axis and ar a beat moves only every other edge, so there the
// reset starts an edge later, on an edge where vld and ready are high.
int resetAfterNs( const runCfg &c )
{
    bool everyOther = c.dir == "src" && c.delayNs > 0 && (c.family == "rv" || c.family == "axis" || c.family == "ar");
    return everyOther ? 55 : 45;
}

template <class DUT>
struct handoverTop : sc_module
{
    sc_clock clk;
    sc_signal<bool> rst_n;
    DUT dut;
    bool midReset;

    SC_HAS_PROCESS( handoverTop );
    handoverTop( sc_module_name n, const runCfg &c ) :
        sc_module( n ), clk( "clk", 10, SC_NS ), dut( "dut", c ), midReset( c.rtl == "reset" )
    {
        dut.clk( clk ); dut.rst_n( rst_n );
        SC_THREAD( run );
        SC_THREAD( resetEdges );
    }

    void run()
    {
        rst_n = 0;
        wait( 25, SC_NS );
        rst_n = 1;
        if (midReset) { wait( sc_time( 2, SC_US ), dut.started ); }
        if (midReset && dut.laneStart != SC_ZERO_TIME) {
            wait( dut.laneStart + sc_time( resetAfterNs( dut.cfg ), SC_NS ) - sc_time_stamp() );
            rst_n = 0;
            wait( 20, SC_NS );
            rst_n = 1;
        }
        wait( 3, SC_US );
        sc_stop();
    }

    void resetEdges()
    {
        while (true) {
            wait( clk.posedge_event() );
            if (!rst_n && pastNs( 30 )) { logEv( "rst", 0 ); }
        }
    }
};

template <class DUT>
void runHandover( const runCfg &c )
{
    handoverTop<DUT> top( "p", c );
    sc_start();
    std::printf( "probe done\n" );
    if (errorCode::getExitCode() > 0) { std::printf( "probe assert %s\n", errorCode::getErrorString().c_str() ); }
}

void runHandover( const runCfg &c )
{
    const std::string key = c.family + " " + c.dir;
    if (key == "rv dst" || key == "rvmulti dst") { runHandover<rvDst>( c ); }
    if (key == "rv src" || key == "rvmulti src") { runHandover<rvSrc>( c ); }
    if (key == "axis dst") { runHandover<axisDst>( c ); }
    if (key == "axis src") { runHandover<axisSrc>( c ); }
    if (key == "ar dst") { runHandover<arDst>( c ); }
    if (key == "ar src") { runHandover<arSrc>( c ); }
    if (key == "r dst") { runHandover<rDst>( c ); }
    if (key == "r src") { runHandover<rSrc>( c ); }
    if (key == "aw dst") { runHandover<awDst>( c ); }
    if (key == "aw src") { runHandover<awSrc>( c ); }
    if (key == "w dst") { runHandover<wDst>( c ); }
    if (key == "w src" || key == "wfirst src") { runHandover<wSrc>( c ); }
    if (key == "b dst") { runHandover<bDst>( c ); }
    if (key == "b src") { runHandover<bSrc>( c ); }
    if (key == "popack dst") { runHandover<popAckDst>( c ); }
    if (key == "popack src") { runHandover<popAckSrc>( c ); }
    if (key == "pushack dst") { runHandover<pushAckDst>( c ); }
    if (key == "pushack src") { runHandover<pushAckSrc>( c ); }
    if (key == "notifyack dst") { runHandover<notifyAckDst>( c ); }
    if (key == "notifyack src") { runHandover<notifyAckSrc>( c ); }
    if (key == "reqack src") { runHandover<reqAckSrc>( c ); }
    if (key == "apb dst") { runHandover<apbDst>( c ); }
    if (key == "apb src") { runHandover<apbSrc>( c ); }
    if (key == "mem dst") { runHandover<memDst>( c ); }
    if (key == "mem src") { runHandover<memSrc>( c ); }
}

int sc_main( int argc, char *argv[] )
{
    logging::GetInstance().setDefaultVerbosity( VERBOSITY_MEDIUM );
    int delayNs = std::atoi( argv[1] );
    std::string bfm = argv[2], mode = argv[3];
    if (argc == 7) {
        // A run that hangs is killed, so each line goes out as it is printed.
        std::setvbuf( stdout, nullptr, _IOLBF, 0 );
        runHandover( { delayNs, bfm, mode, argv[4], std::atoi( argv[5] ), std::string( argv[6] ) == "none" } );
        return errorCode::getExitCode() > 0;
    }
    if (bfm == "req_ack") { runProbe<reqAckDst>( delayNs, mode ); }
    if (bfm == "ar") { runProbe<axiReadSrc>( delayNs, mode ); }
    if (bfm == "r") { runProbe<axiReadDst>( delayNs, mode ); }
    if (bfm == "b") { runProbe<axiWriteDst>( delayNs, mode ); }
    return errorCode::getExitCode() > 0;
}
