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

#include "systemc.h"
#include "logging.h"
#include "axi_read_bfm.h"
#include "axi_write_bfm.h"
#include "req_ack_bfm.h"
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

int sc_main( int, char *argv[] )
{
    logging::GetInstance().setDefaultVerbosity( VERBOSITY_MEDIUM );
    int delayNs = std::atoi( argv[1] );
    std::string bfm = argv[2], mode = argv[3];
    if (bfm == "req_ack") { runProbe<reqAckDst>( delayNs, mode ); }
    if (bfm == "ar") { runProbe<axiReadSrc>( delayNs, mode ); }
    if (bfm == "r") { runProbe<axiReadDst>( delayNs, mode ); }
    if (bfm == "b") { runProbe<axiWriteDst>( delayNs, mode ); }
    return 0;
}
