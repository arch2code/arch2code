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
#include "ahb_bfm.h"
#include "apb_bfm.h"
#include "axi4_stream_bfm.h"
#include "axi_read_bfm.h"
#include "axi_write_bfm.h"
#include "external_reg_bfm.h"
#include "memory_bfm.h"
#include "notify_ack_bfm.h"
#include "pop_ack_bfm.h"
#include "push_ack_bfm.h"
#include "raw_bfm.h"
#include "rdy_vld_bfm.h"
#include "req_ack_bfm.h"
#include "status_bfm.h"
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
//           the wire 30 ns before the AW); the _ack lanes popack, pushack,
//           notifyack and reqack; the buses mem, apb and ahb; the levels
//           status, raw and extreg (external_reg)
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
//           A bus runs four operations, write, read, write, read: always,
//           reset, slow (the RTL completer adds two wait states, or the
//           RTL master two idle edges), error (apb and ahb: operations 1
//           and 2 end in an error response; the dst model posts write 2
//           and waits for the response to the others), and for src parked
//           (the model asks 15 ns after the first request). A level runs
//           values 1 to 8: always, reset, and for src every3 (the RTL
//           steps the level every third edge)
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
//   rstvld     a src RTL has vld high on a reset edge, with this beat
//   req, ack   non-handshake RTL: it starts an operation, or the operation
//              completes on this edge
//   rerr       a bus RTL sees the completion's error response
//   err        a dst bus model gets this error response
//   errfirst   an ahb RTL sees the first cycle of an error response
//   rcall, rcv a src bus model asks for a request, and gets it
//   drv, smp   a level RTL drives this value, or samples a new one
//   pin        a level dst BFM puts this value on the wire
//   mir, pub   external_reg: the model's mirror changes (dst), or the
//              model publishes this value (src)
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

// One handshake lane on the wire: its vld and rdy, the beat it carries, how
// an RTL sender puts beat n on it, and how an RTL receiver drives the data
// it returns with the nth handshake. A lane with no beat (notify) counts its
// handshakes instead.
struct lane {
    sc_signal<bool> &vld, &rdy;
    std::function<std::uint64_t()> beat;
    std::function<void( int )> drive;
    const sc_event &dataEv;
    std::function<void( int )> respond = {};
};

struct handoverBase : sc_module
{
    sc_in<bool> clk, rst_n;
    runCfg cfg;
    portBase *timed = nullptr;
    sc_time laneStart;
    sc_event started;
    bool modelReading = false;
    sc_event firstRequest;

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

    // The model runs setup, then sends beats 0..BEATS-1 back to back. send
    // returns the value the model gets back: the beat, or the response.
    void measureDst( lane l, std::function<void()> setup, std::function<std::uint64_t( int )> send )
    {
        sc_spawn( [this, setup, send] {
            wait( 33, SC_NS );
            if (setup) { setup(); }
            startLane();
            for (int k = 0; k < BEATS; k++) {
                logEv( "call", k );
                logEv( "ret", send( k ) );
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
            if (l.vld) { logEv( "vld", l.beat ? l.beat() : 0 ); }
        }
    }

    // The RTL receiver counts a handshake on an edge out of reset with vld and
    // rdy high. In reset it keeps rdy, as a FIFO whose rdy is !full does.
    void receiver( lane l )
    {
        std::mt19937 rng( 1 );
        int n = 0;
        if (cfg.rtl != "comb") { l.rdy = cfg.rtl == "always" || cfg.rtl == "reset"; }
        if (l.respond) { l.respond( n ); }
        for (int edge = 1;; edge++) {
            waitEdge();
            if (rst_n && l.vld && l.rdy) {
                logEv( "hs", l.beat ? l.beat() : n );
                n++;
                if (l.respond) { l.respond( n ); }
            }
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
                if (l.vld && l.rdy) { logEv( "rsths", l.beat ? l.beat() : n ); }
                if (l.vld) { logEv( "rstvld", l.beat ? l.beat() : n ); }
                l.vld = false;
                continue;
            }
            if (l.vld && l.rdy) {
                logEv( "hs", l.beat ? l.beat() : n );
                n++;
                lastHs = edge;
            } else if (l.vld) {
                continue;
            }
            if (go()) { startLane(); }
            bool offer = cfg.rtl == "hold" ? holdOver() : cfg.rtl == "every3" ? edge % 3 == 0 && edge - lastHs >= 3
                       : cfg.rtl == "random" ? bool( rng() & 1 ) : cfg.rtl == "waiting" ? modelReading : true;
            l.vld = offer && n < BEATS && go();
            if (l.drive) { l.drive( n ); }
        }
    }

    // vld = rdy && a beat is left, re-evaluated whenever rdy or reset changes.
    void combSender( lane l, std::function<bool()> go )
    {
        int n = 0;
        while (true) {
            wait( clk.posedge_event() | l.rdy.value_changed_event() | rst_n.value_changed_event() );
            if (clk.posedge() && rst_n && l.vld && l.rdy) {
                logEv( "hs", l.beat ? l.beat() : n );
                n++;
            }
            if (rst_n && go()) { startLane(); }
            l.vld = rst_n && l.rdy && n < BEATS && go();
            if (l.drive) { l.drive( n ); }
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
        sc_spawn( [this, op] {
            wait( 33, SC_NS );
            startLane();
            for (int k = 0; k < OPS; k++) {
                logEv( "call", k );
                logEv( "ret", op( k ) );
            }
        } );
    }

    // A model that serves OPS requests: receive takes request k, complete
    // answers it. A parked model first calls receive 15 ns after the RTL's
    // first request.
    void modelServes( std::function<void()> receive, std::function<void( int )> complete )
    {
        sc_spawn( [this, receive, complete] {
            if (cfg.rtl == "parked") {
                wait( firstRequest );
                wait( 15, SC_NS );
            }
            for (int k = 0; k < OPS; k++) {
                logEv( "rcall", k );
                receive();
                logEv( "rcv", k );
                logEv( "call", k );
                complete( k );
                logEv( "ret", k );
            }
        } );
    }

    // The RTL bus master logs request n on the edge it drives it.
    void masterRequests( int n )
    {
        logEv( "req", n );
        if (n == 0) {
            startLane();
            firstRequest.notify();
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
            return k;
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
            return k;
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
        measureDst( arLane( hdl ), {}, [this]( int k ) { out->sendAddr( makeAr( k, 0 ) ); return k; } );
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
            return k;
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
        measureDst( awLane( hdl ), {}, [this]( int k ) { out->sendAddr( makeAw( 1, k, 0 ) ); return k; } );
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
                    [this]( int k ) { out->sendDataCycle( makeW( 1, k, k == BEATS - 1 ) ); return k; } );
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
            return k;
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

// push_ack, pop_ack, notify_ack and req_ack are handshake lanes too: the
// request (push, pop, notify, req) is vld and ack is rdy. A src model takes
// each request in two calls, receive then ack(). pop and req return data
// with the ack: the RTL returns n with its nth ack, and a src model returns
// beat k.

using popHdl = pop_ack_hdl_if<sc_bv<32>>;
using pushHdl = push_ack_hdl_if<sc_bv<32>>;
using reqHdl = req_ack_hdl_if<sc_bv<32>, sc_bv<32>>;

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
        measureDst( { hdl.push, hdl.ack, [this] { return hdl.data.read().to_uint64(); }, {}, hdl.data.value_changed_event() },
                    {}, [this]( int k ) { wordSt v; v.w = k; out->push( v ); return k; } );
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
        measureSrc( { hdl.push, hdl.ack, [this] { return hdl.data.read().to_uint64(); },
                      [this]( int i ) { hdl.data = sc_bv<32>( i ); }, hdl.data.value_changed_event() },
                    {}, [this] { wordSt v; in->pushReceive( v ); in->ack(); return v.w; }, [] { return true; } );
    }
};

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
        measureDst( { hdl.pop, hdl.ack, {}, {}, hdl.pop.value_changed_event(),
                      [this]( int i ) { hdl.rdata = sc_bv<32>( i ); } },
                    {}, [this]( int ) { wordSt r; out->pop( r ); return r.w; } );
    }
};

struct popAckSrc : handoverBase
{
    pop_ack_channel<wordSt> ch;
    pop_ack_in<wordSt> in;
    popHdl hdl;
    pop_ack_src_bfm<wordSt, sc_bv<32>> bfm;
    std::uint64_t served = 0;

    popAckSrc( sc_module_name n, const runCfg &c ) : handoverBase( n, c ), ch( "ch", "tb" ), in( "in" ), bfm( "bfm" )
    {
        timed = &ch;
        in( ch ); bfm.if_p( ch ); bfm.hdl_if_p( hdl ); bfm.clk( clk ); bfm.rst_n( rst_n );
        measureSrc( { hdl.pop, hdl.ack, [this] { return hdl.rdata.read().to_uint64(); }, {}, hdl.rdata.value_changed_event() },
                    {}, [this] { in->popReceive(); wordSt v; v.w = served++; in->ack( v ); return v.w; },
                    [] { return true; } );
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
        measureDst( { hdl.notify, hdl.ack, {}, {}, hdl.notify.value_changed_event() },
                    {}, [this]( int k ) { out->notify(); return k; } );
    }
};

struct notifyAckSrc : handoverBase
{
    notify_ack_channel<> ch;
    notify_ack_in<> in;
    notify_ack_hdl_if<> hdl;
    notify_ack_src_bfm<> bfm;
    std::uint64_t served = 0;

    notifyAckSrc( sc_module_name n, const runCfg &c ) : handoverBase( n, c ), ch( "ch", "tb" ), in( "in" ), bfm( "bfm" )
    {
        timed = &ch;
        in( ch ); bfm.if_p( ch ); bfm.hdl_if_p( hdl ); bfm.clk( clk ); bfm.rst_n( rst_n );
        measureSrc( { hdl.notify, hdl.ack, {}, {}, hdl.notify.value_changed_event() },
                    {}, [this] { in->waitNotify(); in->ack(); return served++; }, [] { return true; } );
    }
};

struct reqAckDstHandover : handoverBase
{
    req_ack_channel<wordSt, wordSt> ch;
    req_ack_out<wordSt, wordSt> out;
    reqHdl hdl;
    req_ack_dst_bfm<wordSt, wordSt, sc_bv<32>, sc_bv<32>> bfm;

    reqAckDstHandover( sc_module_name n, const runCfg &c ) : handoverBase( n, c ), ch( "ch", "tb" ), out( "out" ), bfm( "bfm" )
    {
        timed = &ch;
        out( ch ); bfm.if_p( ch ); bfm.hdl_if_p( hdl ); bfm.clk( clk ); bfm.rst_n( rst_n );
        measureDst( { hdl.req, hdl.ack, [this] { return hdl.data.read().to_uint64(); }, {}, hdl.data.value_changed_event(),
                      [this]( int i ) { hdl.rdata = sc_bv<32>( i ); } },
                    {}, [this]( int k ) { wordSt d, a; d.w = k; out->req( d, a ); return a.w; } );
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
        measureSrc( { hdl.req, hdl.ack, [this] { return hdl.data.read().to_uint64(); },
                      [this]( int i ) { hdl.data = sc_bv<32>( i ); }, hdl.data.value_changed_event() },
                    {}, [this] { wordSt d; in->reqReceive( d ); in->ack( d ); return d.w; }, [] { return true; } );
    }
};

// apb, ahb and memory. Operation k writes or reads address k / 2 + 1: writes
// on even k with data 0x11 * (k / 2 + 1), reads on odd k. Besides the run
// modes above, an RTL completer can add two wait states (slow), an RTL
// master can idle two edges between operations (slow), and in error runs
// operations 1 and 2 end with an error: the dst model sends 0, 1 and 3
// with requestWithResponse() and 2 as a posted write, and the src model
// completes 1 and 2 with the error bit. The RTL logs "req" on the edge it
// first sees (completer) or drives (master) a request, and "ack" and "rerr"
// on the edge the operation completes; a dst model logs "err" for each
// response-aware call.

bool opWrites( int k ) { return k % 2 == 0; }
int opAddr( int k ) { return k / 2 + 1; }
int opData( int k ) { return 0x11 * (k / 2 + 1); }
bool errorOp( const runCfg &c, int n ) { return c.rtl == "error" && (n == 1 || n == 2); }

// apb_dst_bfm reads its payloads through _getAddress() and _getData().
struct apbWordSt : wordSt {
    std::uint64_t _getAddress() const { return w; }
    std::uint64_t _getData() const { return w; }
};

using apbHdl = apb_hdl_if<sc_bv<32>, sc_bv<32>>;
using ahbHdl = ahb_hdl_if<sc_bv<32>, sc_bv<32>>;
using memHdl = memory_hdl_if<sc_bv<32>, sc_bv<32>>;

// The model side of a dst register bus: op k as above.
template <class OUT>
std::uint64_t busRequest( OUT &out, const runCfg &c, int k )
{
    apbWordSt a, d;
    a.w = opAddr( k );
    d.w = opWrites( k ) ? opData( k ) : 0;
    if (c.rtl == "error" && k != 2) {
        logEv( "err", out->requestWithResponse( opWrites( k ), a, d ) );
    } else {
        out->request( opWrites( k ), a, d );
    }
    return d.w;
}

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
        modelRequests( [this]( int k ) { return busRequest( out, cfg, k ); } );
        SC_THREAD( completer );
    }

    // Sees the setup phase and raises pready for the access phase that
    // follows, after any wait states.
    SC_HAS_PROCESS( apbDst );
    void completer()
    {
        std::map<std::uint64_t, std::uint64_t> mem;
        int n = 0, waits = 0;
        bool busy = false;
        auto respond = [&] {
            std::uint64_t addr = hdl.paddr.read().to_uint64();
            if (hdl.pwrite) { mem[addr] = hdl.pwdata.read().to_uint64(); } else { hdl.prdata = sc_bv<32>( mem[addr] ); }
            hdl.pready = true;
            hdl.pslverr = errorOp( cfg, n );
        };
        while (true) {
            waitEdge();
            if (!rst_n) { hdl.pready = false; hdl.pslverr = false; busy = false; continue; }
            if (busy && hdl.psel && hdl.penable && hdl.pready) {
                logEv( "ack", hdl.pwrite ? 0 : hdl.prdata.read().to_uint64() );
                logEv( "rerr", hdl.pslverr );
                hdl.pready = false;
                hdl.pslverr = false;
                busy = false;
                n++;
            } else if (busy && waits > 0 && --waits == 0) {
                respond();
            } else if (!busy && hdl.psel && !hdl.penable) {
                logEv( "req", n );
                busy = true;
                waits = cfg.rtl == "slow" ? 2 : 0;
                if (waits == 0) { respond(); }
            }
        }
    }
};

// The model side of a src register bus: it serves op k as above.
template <class IN>
struct busServer {
    std::map<std::uint64_t, std::uint64_t> mem;
    bool isWrite = false;
    apbWordSt a, d;
    void receive( IN &in ) { in->reqReceive( isWrite, a, d ); }
    void complete( IN &in, const runCfg &c, int k )
    {
        if (isWrite) { mem[a.w] = d.w; } else { d.w = mem[a.w]; }
        in->complete( d, errorOp( c, k ) );
    }
};

struct apbSrc : handoverBase
{
    apb_channel<apbWordSt, apbWordSt> ch;
    apb_in<apbWordSt, apbWordSt> in;
    apbHdl hdl;
    apb_src_bfm<apbWordSt, apbWordSt, sc_bv<32>, sc_bv<32>> bfm;
    busServer<apb_in<apbWordSt, apbWordSt>> server;

    apbSrc( sc_module_name n, const runCfg &c ) : handoverBase( n, c ), ch( "ch", "tb" ), in( "in" ), bfm( "bfm" )
    {
        timed = &ch;
        in( ch ); bfm.if_p( ch ); bfm.hdl_if_p( hdl ); bfm.clk( clk ); bfm.rst_n( rst_n );
        modelServes( [this] { server.receive( in ); }, [this]( int k ) { server.complete( in, cfg, k ); } );
        SC_THREAD( manager );
    }

    // Setup phase, access phase, then waits for pready; a new setup phase
    // may start on the edge an access completes.
    SC_HAS_PROCESS( apbSrc );
    void manager()
    {
        int k = 0, phase = 0, idle = 0;
        while (true) {
            waitEdge();
            if (!rst_n) { hdl.psel = false; hdl.penable = false; phase = 0; continue; }
            if (phase == 2 && hdl.pready) {
                logEv( "ack", opWrites( k ) ? 0 : hdl.prdata.read().to_uint64() );
                logEv( "rerr", hdl.pslverr );
                hdl.psel = false;
                hdl.penable = false;
                k++;
                phase = 0;
                idle = cfg.rtl == "slow" ? 2 : 0;
            } else if (phase == 1) {
                hdl.penable = true;
                phase = 2;
            }
            if (phase == 0 && k < OPS && idle-- <= 0) {
                masterRequests( k );
                hdl.psel = true;
                hdl.pwrite = opWrites( k );
                hdl.paddr = sc_bv<32>( opAddr( k ) );
                hdl.pwdata = sc_bv<32>( opWrites( k ) ? opData( k ) : 0 );
                phase = 1;
            }
        }
    }
};

struct ahbDst : handoverBase
{
    ahb_channel<apbWordSt, apbWordSt> ch;
    ahb_out<apbWordSt, apbWordSt> out;
    ahbHdl hdl;
    ahb_dst_bfm<apbWordSt, apbWordSt, sc_bv<32>, sc_bv<32>> bfm;

    ahbDst( sc_module_name n, const runCfg &c ) : handoverBase( n, c ), ch( "ch", "tb" ), out( "out" ), bfm( "bfm" )
    {
        timed = &ch;
        out( ch ); bfm.if_p( ch ); bfm.hdl_if_p( hdl ); bfm.clk( clk ); bfm.rst_n( rst_n );
        modelRequests( [this]( int k ) { return busRequest( out, cfg, k ); } );
        SC_THREAD( slave );
    }

    // Samples an address phase on an edge with hready, then holds the data
    // phase for any wait states. An error takes two cycles, HRESP high with
    // HREADYOUT low and then with HREADYOUT high.
    SC_HAS_PROCESS( ahbDst );
    void slave()
    {
        std::map<std::uint64_t, std::uint64_t> mem;
        int n = 0, waits = 0;
        bool data = false, isWrite = false, err = false, errShown = false;
        std::uint64_t addr = 0;
        hdl.hreadyout = true;
        while (true) {
            waitEdge();
            if (!rst_n) { hdl.hreadyout = true; hdl.hresp = false; data = false; continue; }
            bool ready = hdl.hreadyout;
            if (data && ready) {
                if (isWrite) { mem[addr] = hdl.hwdata.read().to_uint64(); }
                logEv( "ack", isWrite ? 0 : hdl.hrdata.read().to_uint64() );
                logEv( "rerr", hdl.hresp );
                data = false;
                n++;
            }
            if (ready && hdl.hsel && hdl.htrans.read()[1].to_bool()) {
                addr = hdl.haddr.read().to_uint64();
                isWrite = hdl.hwrite;
                logEv( "req", n );
                data = true;
                waits = cfg.rtl == "slow" ? 2 : 0;
                err = errorOp( cfg, n );
                errShown = false;
            }
            if (!data) {
                hdl.hreadyout = true;
                hdl.hresp = false;
            } else if (waits > 0) {
                waits--;
                hdl.hreadyout = false;
                hdl.hresp = false;
            } else if (err && !errShown) {
                errShown = true;
                hdl.hreadyout = false;
                hdl.hresp = true;
            } else {
                hdl.hreadyout = true;
                hdl.hresp = err;
                if (!isWrite) { hdl.hrdata = sc_bv<32>( mem[addr] ); }
            }
        }
    }
};

struct ahbSrc : handoverBase
{
    ahb_channel<apbWordSt, apbWordSt> ch;
    ahb_in<apbWordSt, apbWordSt> in;
    ahbHdl hdl;
    ahb_src_bfm<apbWordSt, apbWordSt, sc_bv<32>, sc_bv<32>> bfm;
    busServer<ahb_in<apbWordSt, apbWordSt>> server;

    ahbSrc( sc_module_name n, const runCfg &c ) : handoverBase( n, c ), ch( "ch", "tb" ), in( "in" ), bfm( "bfm" )
    {
        timed = &ch;
        in( ch ); bfm.if_p( ch ); bfm.hdl_if_p( hdl ); bfm.clk( clk ); bfm.rst_n( rst_n );
        modelServes( [this] { server.receive( in ); }, [this]( int k ) { server.complete( in, cfg, k ); } );
        SC_THREAD( master );
        SC_METHOD( tieHready );
        sensitive << hdl.hreadyout;
    }

    SC_HAS_PROCESS( ahbSrc );
    void tieHready() { hdl.hready = hdl.hreadyout.read(); }

    // A pipelined master: the next address phase goes out with the data
    // phase of the one before. It logs "errfirst" on the edge it sees the
    // first cycle of an error response.
    void master()
    {
        int next = 0, addrOp = -1, dataOp = -1, idle = 0;
        while (true) {
            waitEdge();
            if (!rst_n) { hdl.hsel = false; hdl.htrans = sc_bv<2>( 0 ); addrOp = dataOp = -1; continue; }
            if (hdl.hreadyout) {
                if (dataOp >= 0) {
                    logEv( "ack", opWrites( dataOp ) ? 0 : hdl.hrdata.read().to_uint64() );
                    logEv( "rerr", hdl.hresp );
                    dataOp = -1;
                    idle = cfg.rtl == "slow" ? 2 : 0;
                }
                if (addrOp >= 0) {
                    dataOp = addrOp;
                    addrOp = -1;
                    hdl.hwdata = sc_bv<32>( opWrites( dataOp ) ? opData( dataOp ) : 0 );
                }
            } else if (dataOp >= 0 && hdl.hresp) {
                logEv( "errfirst", dataOp );
            }
            if (addrOp < 0 && next < OPS && (cfg.rtl != "slow" || (dataOp < 0 && idle-- <= 0))) {
                addrOp = next++;
                masterRequests( addrOp );
                hdl.hsel = true;
                hdl.htrans = sc_bv<2>( AHB_HTRANS_NONSEQ );
                hdl.hwrite = opWrites( addrOp );
                hdl.hsize = sc_bv<3>( AHB_HSIZE_WORD );
                hdl.haddr = sc_bv<32>( opAddr( addrOp ) );
            } else if (addrOp < 0) {
                hdl.hsel = false;
                hdl.htrans = sc_bv<2>( 0 );
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
        int n = 0;
        while (true) {
            waitEdge();
            if (!rst_n || !hdl.enable) { continue; }
            std::uint64_t addr = hdl.addr.read().to_uint64();
            logEv( "req", n++ );
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

    // Drives an access, and reads the data of a read access on the edge
    // after the one that sampled it. A slow master idles two edges between
    // accesses.
    SC_HAS_PROCESS( memSrc );
    void manager()
    {
        int k = 0, sampled = -1, idle = 0, logged = -1;
        while (true) {
            waitEdge();
            if (!rst_n) { hdl.enable = false; continue; }
            if (sampled >= 0) {
                logEv( "ack", opWrites( sampled ) ? 0 : hdl.read_data.read().to_uint64() );
                sampled = -1;
            }
            if (hdl.enable) {
                sampled = k++;
                idle = cfg.rtl == "slow" ? 2 : 0;
            }
            bool drive = k < OPS && idle-- <= 0;
            if (drive && k != logged) { masterRequests( logged = k ); }
            hdl.enable = drive;
            hdl.wr_en = opWrites( k );
            hdl.addr = sc_bv<32>( opAddr( k ) );
            hdl.write_data = sc_bv<32>( opWrites( k ) ? opData( k ) : 0 );
        }
    }
};

// status, raw and external_reg carry levels, with no handshake. The RTL
// logs "drv v" on the edge it drives value v, and "smp v" on the edge it
// samples a new value; the model logs "call v" when it writes and "ret v"
// when a read returns. Values run 1..BEATS. A src RTL changes its value on
// every edge (always) or every third edge (every3), and drives 0 in reset.

using statusHdl = status_hdl_if<sc_bv<32>>;
using rawHdl = raw_hdl_if<sc_bv<32>>;
using extHdl = external_reg_hdl_if<sc_bv<32>>;

// The model writes 1..BEATS from 33 ns, one every clock.
void modelWritesLevels( std::function<void( int )> write )
{
    sc_spawn( [write] {
        sc_core::wait( 33, SC_NS );
        for (int v = 1; v <= BEATS; v++) {
            logEv( "call", v );
            write( v );
            logEv( "ret", v );
            sc_core::wait( 10, SC_NS );
        }
    } );
}

struct levelBase : handoverBase
{
    levelBase( sc_module_name n, const runCfg &c ) : handoverBase( n, c ) {}

    // An RTL source register: 0 from the start, then 1..BEATS, then holds
    // BEATS.
    void driveLevels( std::function<void( int )> drive )
    {
        int v = 0;
        logEv( "drv", 0 );
        for (int edge = 1;; edge++) {
            waitEdge();
            if (!rst_n) {
                if (v != 0 && pastNs( 30 )) { v = 0; drive( 0 ); logEv( "drv", 0 ); }
                continue;
            }
            startLane();
            bool step = cfg.rtl == "every3" ? edge % 3 == 0 : true;
            if (step && next < BEATS) {
                v = ++next;
                drive( v );
                logEv( "drv", v );
            }
        }
    }

    // An RTL sink register: logs each new value it samples out of reset.
    void sampleLevels( std::function<std::uint64_t()> read )
    {
        std::uint64_t last = 0;
        while (true) {
            waitEdge();
            if (!rst_n) { continue; }
            std::uint64_t v = read();
            if (v != last) { logEv( "smp", v ); last = v; }
        }
    }

    int next = 0;
};

struct statusDst : levelBase
{
    status_channel<wordSt> ch;
    status_out<wordSt> out;
    statusHdl hdl;
    status_dst_bfm<wordSt, sc_bv<32>> bfm;

    statusDst( sc_module_name n, const runCfg &c ) : levelBase( n, c ), ch( "ch", "tb" ), out( "out" ), bfm( "bfm" )
    {
        timed = &ch;
        out( ch ); bfm.if_p( ch ); bfm.hdl_if_p( hdl ); bfm.clk( clk ); bfm.rst_n( rst_n );
        modelWritesLevels( [this]( int v ) { startLane(); wordSt d; d.w = v; out->write( d ); } );
        sc_spawn( [this] { sampleLevels( [this] { return hdl.data.read().to_uint64(); } ); } );
        sc_spawn( [this] { while (true) { wait( hdl.data.value_changed_event() ); logEv( "pin", hdl.data.read().to_uint64() ); } } );
    }
};

struct statusSrc : levelBase
{
    status_channel<wordSt> ch;
    status_in<wordSt> in;
    statusHdl hdl;
    status_src_bfm<wordSt, sc_bv<32>> bfm;

    statusSrc( sc_module_name n, const runCfg &c ) : levelBase( n, c ), ch( "ch", "tb" ), in( "in" ), bfm( "bfm" )
    {
        timed = &ch;
        in( ch ); bfm.if_p( ch ); bfm.hdl_if_p( hdl ); bfm.clk( clk ); bfm.rst_n( rst_n );
        sc_spawn( [this] { driveLevels( [this]( int v ) { hdl.data = sc_bv<32>( v ); } ); } );
        sc_spawn( [this] { while (true) { wordSt d; in->read( d ); logEv( "ret", d.w ); } } );
    }
};

struct rawDst : levelBase
{
    raw_channel<wordSt> ch;
    raw_out<wordSt> out;
    rawHdl hdl;
    raw_dst_bfm<wordSt, sc_bv<32>> bfm;

    rawDst( sc_module_name n, const runCfg &c ) : levelBase( n, c ), ch( "ch", "tb" ), out( "out" ), bfm( "bfm" )
    {
        timed = &ch;
        out( ch ); bfm.if_p( ch ); bfm.hdl_if_p( hdl ); bfm.clk( clk ); bfm.rst_n( rst_n );
        sc_spawn( [this] {
            wait( 33, SC_NS );
            startLane();
            for (int v = 1; v <= BEATS; v++) {
                logEv( "call", v );
                wordSt d;
                d.w = v;
                out->write( d );
                logEv( "ret", v );
            }
        } );
        sc_spawn( [this] { sampleLevels( [this] { return hdl.data.read().to_uint64(); } ); } );
        sc_spawn( [this] { while (true) { wait( hdl.data.value_changed_event() ); logEv( "pin", hdl.data.read().to_uint64() ); } } );
    }
};

struct rawSrc : levelBase
{
    raw_channel<wordSt> ch;
    raw_in<wordSt> in;
    rawHdl hdl;
    raw_src_bfm<wordSt, sc_bv<32>> bfm;

    rawSrc( sc_module_name n, const runCfg &c ) : levelBase( n, c ), ch( "ch", "tb" ), in( "in" ), bfm( "bfm" )
    {
        timed = &ch;
        in( ch ); bfm.if_p( ch ); bfm.hdl_if_p( hdl ); bfm.clk( clk ); bfm.rst_n( rst_n );
        sc_spawn( [this] { driveLevels( [this]( int v ) { hdl.data = sc_bv<32>( v ); } ); } );
        sc_spawn( [this] { while (true) { wordSt d; in->read( d ); logEv( "ret", d.w ); } } );
    }
};

// The model is the register handler: it issues reg_write_cmd(v) and watches
// the mirror. The RTL owner takes each strobe and drives rdata = wdata + 0x100.
struct extregDst : levelBase
{
    external_reg_channel<wordSt> ch;
    external_reg_out<wordSt> out;
    extHdl hdl;
    external_reg_dst_bfm<wordSt, sc_bv<32>> bfm;

    extregDst( sc_module_name n, const runCfg &c ) : levelBase( n, c ), ch( "ch", "tb" ), out( "out" ), bfm( "bfm" )
    {
        timed = &ch;
        out( ch ); bfm.if_p( ch ); bfm.hdl_if_p( hdl ); bfm.clk( clk ); bfm.rst_n( rst_n );
        modelWritesLevels( [this]( int v ) { startLane(); wordSt d; d.w = v; out->reg_write_cmd( d ); } );
        sc_spawn( [this] { while (true) { out->wait_mirror(); logEv( "mir", out->readNonBlocking().w ); } } );
        SC_THREAD( owner );
    }

    SC_HAS_PROCESS( extregDst );
    void owner()
    {
        while (true) {
            waitEdge();
            if (!rst_n) { continue; }
            if (hdl.write.read().or_reduce()) {
                std::uint64_t v = hdl.wdata.read().to_uint64();
                logEv( "smp", v );
                hdl.rdata = sc_bv<32>( v + 0x100 );
                logEv( "drv", v + 0x100 );
            }
        }
    }
};

// The model owns the register: it reads each command and publishes
// value + 0x100. The RTL handler strobes 1..BEATS and samples rdata.
struct extregSrc : levelBase
{
    external_reg_channel<wordSt> ch;
    external_reg_in<wordSt> in;
    extHdl hdl;
    external_reg_src_bfm<wordSt, sc_bv<32>> bfm;

    extregSrc( sc_module_name n, const runCfg &c ) : levelBase( n, c ), ch( "ch", "tb" ), in( "in" ), bfm( "bfm" )
    {
        timed = &ch;
        in( ch ); bfm.if_p( ch ); bfm.hdl_if_p( hdl ); bfm.clk( clk ); bfm.rst_n( rst_n );
        sc_spawn( [this] {
            while (true) {
                wordSt d;
                in->read( d );
                logEv( "ret", d.w );
                d.w += 0x100;
                in->update_mirror( d );
                logEv( "pub", d.w );
            }
        } );
        sc_spawn( [this] { sampleLevels( [this] { return hdl.rdata.read().to_uint64(); } ); } );
        SC_THREAD( handler );
    }

    // Strobes write for one cycle per value.
    SC_HAS_PROCESS( extregSrc );
    void handler()
    {
        for (int edge = 1;; edge++) {
            waitEdge();
            hdl.write = 0;
            if (!rst_n) { continue; }
            startLane();
            bool step = cfg.rtl == "every3" ? edge % 3 == 0 : true;
            if (step && next < BEATS) {
                hdl.write = 1;
                hdl.wdata = sc_bv<32>( ++next );
                logEv( "drv", next );
            }
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
    if (key == "reqack dst") { runHandover<reqAckDstHandover>( c ); }
    if (key == "notifyack dst") { runHandover<notifyAckDst>( c ); }
    if (key == "notifyack src") { runHandover<notifyAckSrc>( c ); }
    if (key == "reqack src") { runHandover<reqAckSrc>( c ); }
    if (key == "apb dst") { runHandover<apbDst>( c ); }
    if (key == "apb src") { runHandover<apbSrc>( c ); }
    if (key == "ahb dst") { runHandover<ahbDst>( c ); }
    if (key == "ahb src") { runHandover<ahbSrc>( c ); }
    if (key == "mem dst") { runHandover<memDst>( c ); }
    if (key == "mem src") { runHandover<memSrc>( c ); }
    if (key == "status dst") { runHandover<statusDst>( c ); }
    if (key == "status src") { runHandover<statusSrc>( c ); }
    if (key == "raw dst") { runHandover<rawDst>( c ); }
    if (key == "raw src") { runHandover<rawSrc>( c ); }
    if (key == "extreg dst") { runHandover<extregDst>( c ); }
    if (key == "extreg src") { runHandover<extregSrc>( c ); }
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
