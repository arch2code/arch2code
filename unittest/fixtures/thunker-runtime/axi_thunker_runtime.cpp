// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE
//
// Runtime acceptance harness for the axi_read and axi_write port thunkers.
// Driven by unittest/test_thunker_runtime.py.
//
// Each case drives real AXI traffic between a parent-side endpoint on the
// channel and a child endpoint behind the thunker, and runs the same traffic
// over a direct connection as a control. The thunked run must deliver the same
// beats as the control and finish at the same simulation time.
//
// The payload pairs make each check say which copy ran:
//  - narrowSt and wideSt declare 16 bits in 32-bit and 64-bit storage. The
//    envelopes around them differ in storage, so only the packed arm can
//    bridge them, and it drops every bit above bit 15 (the accepted thunker
//    limitation noted at copyPayload; not behaviour a model may rely on).
//  - maskASt and maskBSt are distinct declarations over identical storage, the
//    pair a direct verdict describes. Under a direct verdict the burst buffer
//    is shared and every bit arrives.
// Every sent value has bits above bit 15 set, so a check that expects them
// kept fails if the packed arm ran, and one that expects them dropped fails if
// the storage was reinterpreted.
//
// A user sideband bound on the receiving side only must keep the receiving
// envelope's default (USER_SENTINEL). No 16-bit unpack can produce it.
//
// Pass a case name to run that case alone, or --list to print the names.

#include "axi_read_port_thunker.h"
#include "axi_write_port_thunker.h"

#include <cstdint>
#include <cstdio>
#include <functional>
#include <memory>
#include <string>
#include <vector>
#include <systemc.h>

static constexpr std::uint32_t MASK16 = 0xFFFFu;
static constexpr std::uint32_t USER_SENTINEL = 0x5A5A5A5Au;

#define A2C_AXI_PAYLOAD( NAME, STORAGE, INIT )                                  \
    struct NAME                                                                 \
    {                                                                           \
        using _packedSt = STORAGE;                                              \
        static constexpr unsigned _bitWidth = 16;                               \
        static constexpr unsigned _byteWidth = sizeof( _packedSt );             \
        void pack( _packedSt& v ) const { v = value & MASK16; }                 \
        void unpack( const _packedSt& v ) { value = v & MASK16; }               \
        /* "" selects the channels' no-tracker path. */                         \
        static const char* getValueType() { return ""; }                        \
        std::uint64_t getStructValue() const { return value; }                  \
        std::string prt( bool = false ) const { return #NAME; }                 \
        bool operator==( const NAME& o ) const { return value == o.value; }     \
        STORAGE value = INIT;                                                   \
    }

A2C_AXI_PAYLOAD( narrowSt, std::uint32_t, 0 );
A2C_AXI_PAYLOAD( wideSt, std::uint64_t, 0 );
A2C_AXI_PAYLOAD( maskASt, std::uint32_t, 0 );
A2C_AXI_PAYLOAD( maskBSt, std::uint32_t, 0 );
A2C_AXI_PAYLOAD( userNarrowSt, std::uint32_t, USER_SENTINEL );
A2C_AXI_PAYLOAD( userWideSt, std::uint64_t, USER_SENTINEL );

static_assert( sizeof( maskASt ) == sizeof( maskBSt ) );
static_assert( sizeof( narrowSt ) != sizeof( wideSt ) );

// A parameterizable id_t spells as a 64-bit alias; the Up bundles use it so the
// id crosses between two C++ types of the same 4-bit width.
using wideIdT = std::uint64_t;

static int g_checks = 0;
static int g_failures = 0;

// Per-run observations. `direct` says whether the required payloads cross
// whole; `userCrosses` whether both ends bind the user sidebands.
struct axiRun
{
    std::string label;
    bool direct = true;
    bool userDirect = true;
    bool userCrosses = true;
    int beats = 0;
    int bursts = 0;
    int resps = 0;
    bool senderDone = false;
    bool receiverDone = false;
    sc_core::sc_time done = sc_core::SC_ZERO_TIME;
    int printed = 0;
};

static void expectEqual( axiRun& run, const char* what, std::uint64_t got, std::uint64_t want )
{
    ++g_checks;
    if (got != want) {
        ++g_failures;
        // A broken bridge fails every beat; the first few say how.
        if (run.printed++ < 8) {
            std::printf( "FAIL %s %s: got 0x%llx want 0x%llx\n", run.label.c_str(), what,
                         (unsigned long long)got, (unsigned long long)want );
        }
    }
}

enum : std::uint32_t { TAG_ADDR = 0x11, TAG_DATA = 0x22, TAG_STRB = 0x33, TAG_AUSER = 0x44,
                       TAG_DUSER = 0x55, TAG_BUSER = 0x66 };

static std::uint32_t val( std::uint32_t tag, int burst, int beat )
{
    return ( tag << 24 ) | 0x00A50000u | ( (std::uint32_t)burst << 8 ) | (std::uint32_t)beat;
}

static std::uint32_t bridged( std::uint32_t v, bool direct ) { return direct ? v : ( v & MASK16 ); }

static _axiResponseT respFor( int burst, int beat ) { return (_axiResponseT)( ( burst + beat ) % 4 ); }

template <class U>
static void putUser( U& u, std::uint32_t v )
{
    if constexpr (hasOptionalPayload<U>) u.value = v;
}

template <class U>
static void checkUser( axiRun& run, const char* what, const U& u, std::uint32_t v )
{
    if constexpr (hasOptionalPayload<U>) {
        expectEqual( run, what, u.value, run.userCrosses ? bridged( v, run.userDirect ) : USER_SENTINEL );
    }
}

struct axiBurst
{
    int id;
    int len;
};

// Construction shapes: the child is the consumer (responder/receiver) or the
// producer (requester/sender), and the parent side is the channel itself or an
// unbound parent port.
enum class shape { connections, connectionMap, producer, producerPort };

static bool childConsumes( shape s ) { return s == shape::connections || s == shape::connectionMap; }

static void pace( int ns ) { sc_core::wait( ns, sc_core::SC_NS ); }

// ===========================================================================
// axi_read
// ===========================================================================
template <class A_, class D_, class ARU_ = std::monostate, class RU_ = std::monostate, class ID_ = _axiIdT>
struct rdT
{
    using A = A_;
    using D = D_;
    using ARU = ARU_;
    using RU = RU_;
    using ID = ID_;
    using addr = axiReadAddressSt<A, ARU, ID, 4>;
    using resp = axiReadRespSt<D, RU, ID, 4>;
    using chan = axi_read_channel<A, D, ARU, RU, ID, 4>;
    using in = axi_read_in<A, D, ARU, RU, ID, 4>;
    using out = axi_read_out<A, D, ARU, RU, ID, 4>;
    using in_if = axi_read_in_if<A, D, ARU, RU, ID, 4>;
    using out_if = axi_read_out_if<A, D, ARU, RU, ID, 4>;
};

// cycle: receiveDataCycle/sendDataCycle. burst: push_burst + getReadPtr against
// getWritePtr + sendData(x, N). beat: one transactional sendData/receiveData per
// single-beat burst, on a channel without a burst buffer.
enum class rdMode { cycle, burst, beat };

struct rdScenario
{
    rdMode mode;
    bool multicycle;
    // serial: each AR waits for its R. Otherwise every AR is issued before any
    // R is read, and R returns in returnOrder.
    bool serial;
    std::vector<axiBurst> bursts;
    std::vector<int> returnOrder;
    bool fixedSize = false;
    unsigned bufferBeats = 256;
};

template <class T>
static std::unique_ptr<typename T::chan> makeChan( bool multicycle, bool fixedSize = false, unsigned bufferBeats = 256 )
{
    if (multicycle) return std::make_unique<typename T::chan>( "chan", "tb", fixedSize ? "fixed_size" : "api_list_size", bufferBeats, "" );
    return std::make_unique<typename T::chan>( "chan", "tb" );
}

template <class T>
static void rdCheckBeat( axiRun& run, const typename T::resp& r, const rdScenario& sc, int b, int i )
{
    const axiBurst& bu = sc.bursts[b];
    ++run.beats;
    expectEqual( run, "rid", r.rid, bu.id );
    expectEqual( run, "rdata", r.rdata.value, bridged( val( TAG_DATA, b, i ), run.direct ) );
    expectEqual( run, "rresp", r.rresp, respFor( b, i ) );
    expectEqual( run, "rlast", r.rlast, i == bu.len );
    checkUser( run, "ruser", r.user, val( TAG_DUSER, b, i ) );
}

template <class T>
static void rdSendAddr( typename T::out& p, const rdScenario& sc, int b )
{
    pace( 1 );
    const axiBurst& bu = sc.bursts[b];
    typename T::addr a;
    a.arid = bu.id;
    a.araddr.value = val( TAG_ADDR, b, 0 );
    a.arlen = bu.len;
    a.arsize = 2;
    a.arburst = AXIBURST_INCR;
    putUser( a.user, val( TAG_AUSER, b, 0 ) );
    if (sc.mode == rdMode::burst && !sc.fixedSize) p->push_burst( bu.len + 1 );
    p->sendAddr( a );
}

template <class T>
static void rdReceiveBurst( typename T::out& p, const rdScenario& sc, axiRun& run, int b )
{
    const int len = sc.bursts[b].len;
    if (sc.mode == rdMode::burst) {
        typename T::resp r;
        p->receiveData( r );
        const typename T::resp* buf = reinterpret_cast<const typename T::resp*>( p->getReadPtr() );
        for (int i = 0; i <= len; ++i) rdCheckBeat<T>( run, buf[i], sc, b, i );
    } else {
        for (int i = 0; i <= len; ++i) {
            typename T::resp r;
            if (sc.mode == rdMode::cycle) p->receiveDataCycle( r ); else p->receiveData( r );
            rdCheckBeat<T>( run, r, sc, b, i );
        }
    }
    ++run.bursts;
}

template <class T>
static void rdRequester( typename T::out& p, const rdScenario& sc, axiRun& run )
{
    if (sc.mode == rdMode::cycle) p->setCycleTransaction( PORTTYPE_OUT );
    const int n = (int)sc.bursts.size();
    if (sc.serial) {
        for (int b = 0; b < n; ++b) {
            rdSendAddr<T>( p, sc, b );
            rdReceiveBurst<T>( p, sc, run, b );
        }
    } else {
        for (int b = 0; b < n; ++b) rdSendAddr<T>( p, sc, b );
        for (int b : sc.returnOrder) rdReceiveBurst<T>( p, sc, run, b );
    }
    run.done = sc_core::sc_time_stamp();
    run.senderDone = true;
}

template <class T>
static void rdReceiveAddr( typename T::in& p, const rdScenario& sc, axiRun& run, int b )
{
    const axiBurst& bu = sc.bursts[b];
    typename T::addr a;
    p->receiveAddr( a );
    expectEqual( run, "arid", a.arid, bu.id );
    expectEqual( run, "araddr", a.araddr.value, bridged( val( TAG_ADDR, b, 0 ), run.direct ) );
    expectEqual( run, "arlen", a.arlen, bu.len );
    expectEqual( run, "arsize", a.arsize, 2 );
    expectEqual( run, "arburst", a.arburst, AXIBURST_INCR );
    checkUser( run, "aruser", a.user, val( TAG_AUSER, b, 0 ) );
}

template <class T>
static void rdFillBeat( typename T::resp& r, const rdScenario& sc, int b, int i )
{
    r.rid = sc.bursts[b].id;
    r.rdata.value = val( TAG_DATA, b, i );
    r.rresp = respFor( b, i );
    r.rlast = ( i == sc.bursts[b].len );
    putUser( r.user, val( TAG_DUSER, b, i ) );
}

template <class T>
static void rdSendBurst( typename T::in& p, const rdScenario& sc, int b )
{
    pace( 2 );
    const int len = sc.bursts[b].len;
    if (sc.mode == rdMode::burst) {
        typename T::resp* buf = reinterpret_cast<typename T::resp*>( p->getWritePtr() );
        for (int i = 0; i <= len; ++i) rdFillBeat<T>( buf[i], sc, b, i );
        if (sc.fixedSize) p->sendData( *buf ); else p->sendData( *buf, len + 1 );
    } else {
        for (int i = 0; i <= len; ++i) {
            typename T::resp r;
            rdFillBeat<T>( r, sc, b, i );
            if (sc.mode == rdMode::cycle) p->sendDataCycle( r ); else p->sendData( r );
        }
    }
}

template <class T>
static void rdResponder( typename T::in& p, const rdScenario& sc, axiRun& run )
{
    if (sc.mode == rdMode::cycle) p->setCycleTransaction( PORTTYPE_IN );
    const int n = (int)sc.bursts.size();
    if (sc.serial) {
        for (int b = 0; b < n; ++b) {
            rdReceiveAddr<T>( p, sc, run, b );
            rdSendBurst<T>( p, sc, b );
        }
    } else {
        for (int b = 0; b < n; ++b) rdReceiveAddr<T>( p, sc, run, b );
        for (int b : sc.returnOrder) rdSendBurst<T>( p, sc, b );
    }
    run.receiverDone = true;
}

template <class Up, class Down, bool DA, bool DD>
struct rdThunkHarness : sc_core::sc_module
{
    using thunker_t = axi_read_port_thunker<typename Up::A, typename Up::D, typename Down::A, typename Down::D, DA, DD,
                                            typename Up::ARU, typename Up::RU, typename Up::ID, 4,
                                            typename Down::ARU, typename Down::RU, typename Down::ID, 4>;
    std::unique_ptr<typename Up::chan> upChan;
    std::unique_ptr<typename Up::out> peerOut;
    std::unique_ptr<typename Up::in> peerIn;
    std::unique_ptr<typename Up::in> upInPort;
    std::unique_ptr<typename Up::out> upOutPort;
    std::unique_ptr<typename Down::in> childIn;
    std::unique_ptr<typename Down::out> childOut;
    std::unique_ptr<thunker_t> thunker;

    rdThunkHarness( sc_core::sc_module_name n, shape s, const rdScenario& sc, axiRun& run )
      : sc_core::sc_module( n ), upChan( makeChan<Up>( sc.multicycle, sc.fixedSize, sc.bufferBeats ) )
    {
        if (childConsumes( s )) {
            peerOut = std::make_unique<typename Up::out>( "peerOut" );
            ( *peerOut )( *upChan );
            childIn = std::make_unique<typename Down::in>( "childIn" );
            if (s == shape::connectionMap) {
                upInPort = std::make_unique<typename Up::in>( "upInPort" );
                thunker = std::make_unique<thunker_t>( "thunker", *upInPort, *childIn, "tb" );
                // Bound after the thunker captured it, as the generated container does.
                ( *upInPort )( *upChan );
            } else {
                thunker = std::make_unique<thunker_t>( "thunker", static_cast<typename Up::in_if&>( *upChan ), *childIn, "tb" );
            }
            sc_core::sc_spawn( [this, &sc, &run]() { rdRequester<Up>( *peerOut, sc, run ); } );
            sc_core::sc_spawn( [this, &sc, &run]() { rdResponder<Down>( *childIn, sc, run ); } );
        } else {
            peerIn = std::make_unique<typename Up::in>( "peerIn" );
            ( *peerIn )( *upChan );
            childOut = std::make_unique<typename Down::out>( "childOut" );
            if (s == shape::producerPort) {
                upOutPort = std::make_unique<typename Up::out>( "upOutPort" );
                thunker = std::make_unique<thunker_t>( "thunker", *upOutPort, *childOut, "tb" );
                ( *upOutPort )( *upChan );
            } else {
                thunker = std::make_unique<thunker_t>( "thunker", static_cast<typename Up::out_if&>( *upChan ), *childOut, "tb" );
            }
            sc_core::sc_spawn( [this, &sc, &run]() { rdRequester<Down>( *childOut, sc, run ); } );
            sc_core::sc_spawn( [this, &sc, &run]() { rdResponder<Up>( *peerIn, sc, run ); } );
        }
    }
};

template <class T>
struct rdDirectHarness : sc_core::sc_module
{
    std::unique_ptr<typename T::chan> chan;
    typename T::out req;
    typename T::in rsp;

    rdDirectHarness( sc_core::sc_module_name n, const rdScenario& sc, axiRun& run )
      : sc_core::sc_module( n ), chan( makeChan<T>( sc.multicycle, sc.fixedSize, sc.bufferBeats ) ), req( "req" ), rsp( "rsp" )
    {
        req( *chan );
        rsp( *chan );
        sc_core::sc_spawn( [this, &sc, &run]() { rdRequester<T>( req, sc, run ); } );
        sc_core::sc_spawn( [this, &sc, &run]() { rdResponder<T>( rsp, sc, run ); } );
    }
};

// ===========================================================================
// axi_write
// ===========================================================================
template <class A_, class D_, class S_, class AWU_ = std::monostate, class WU_ = std::monostate,
          class BU_ = std::monostate, class ID_ = _axiIdT>
struct wrT
{
    using A = A_;
    using D = D_;
    using S = S_;
    using AWU = AWU_;
    using WU = WU_;
    using BU = BU_;
    using ID = ID_;
    using addr = axiWriteAddressSt<A, AWU, ID, 4>;
    using data = axiWriteDataSt<D, S, WU, ID, 4>;
    using resp = axiWriteRespSt<BU, ID, 4>;
    using chan = axi_write_channel<A, D, S, AWU, WU, BU, ID, 4>;
    using in = axi_write_in<A, D, S, AWU, WU, BU, ID, 4>;
    using out = axi_write_out<A, D, S, AWU, WU, BU, ID, 4>;
    using in_if = axi_write_in_if<A, D, S, AWU, WU, BU, ID, 4>;
    using out_if = axi_write_out_if<A, D, S, AWU, WU, BU, ID, 4>;
};

// burst: getSendDataPtr + sendData(x, N) / receiveData + getReceiveDataPtr.
// beat: one transactional sendData/receiveData per beat. cycle: the Cycle APIs.
enum class wrMode { burst, beat, cycle };

struct wrScenario
{
    wrMode send;
    wrMode recv;
    bool multicycle;
    // serial: AW, W and B of one burst complete before the next burst starts.
    // Otherwise all AWs and all Ws run in groups, then B in respOrder.
    bool serial;
    // W is sent and received before AW, individually or as a group.
    bool dataFirst;
    std::vector<axiBurst> bursts;
    std::vector<int> respOrder;
    bool fixedSize = false;
    unsigned bufferBeats = 256;
};

template <class T>
static void wrFillBeat( typename T::data& d, const wrScenario& sc, int b, int i )
{
    d.wid = sc.bursts[b].id;
    d.wdata.value = val( TAG_DATA, b, i );
    d.wstrb.value = val( TAG_STRB, b, i );
    d.wlast = ( i == sc.bursts[b].len );
    putUser( d.user, val( TAG_DUSER, b, i ) );
}

template <class T>
static void wrCheckBeat( axiRun& run, const typename T::data& d, const wrScenario& sc, int b, int i )
{
    const axiBurst& bu = sc.bursts[b];
    ++run.beats;
    expectEqual( run, "wid", d.wid, bu.id );
    expectEqual( run, "wdata", d.wdata.value, bridged( val( TAG_DATA, b, i ), run.direct ) );
    expectEqual( run, "wstrb", d.wstrb.value, bridged( val( TAG_STRB, b, i ), run.direct ) );
    expectEqual( run, "wlast", d.wlast, i == bu.len );
    checkUser( run, "wuser", d.user, val( TAG_DUSER, b, i ) );
}

template <class T>
static void wrSendAddr( typename T::out& p, const wrScenario& sc, int b )
{
    pace( 1 );
    const axiBurst& bu = sc.bursts[b];
    typename T::addr a;
    a.awid = bu.id;
    a.awaddr.value = val( TAG_ADDR, b, 0 );
    a.awlen = bu.len;
    a.awsize = 2;
    a.awburst = AXIBURST_INCR;
    putUser( a.user, val( TAG_AUSER, b, 0 ) );
    p->sendAddr( a );
}

template <class T>
static void wrSendBurst( typename T::out& p, const wrScenario& sc, int b )
{
    pace( 1 );
    const int len = sc.bursts[b].len;
    if (sc.send == wrMode::burst) {
        typename T::data* buf = reinterpret_cast<typename T::data*>( p->getSendDataPtr() );
        for (int i = 0; i <= len; ++i) wrFillBeat<T>( buf[i], sc, b, i );
        if (sc.fixedSize) p->sendData( *buf ); else p->sendData( *buf, len + 1 );
    } else {
        for (int i = 0; i <= len; ++i) {
            typename T::data d;
            wrFillBeat<T>( d, sc, b, i );
            if (sc.send == wrMode::cycle) p->sendDataCycle( d ); else p->sendData( d );
        }
    }
}

template <class T>
static void wrReceiveResp( typename T::out& p, const wrScenario& sc, axiRun& run, int b )
{
    typename T::resp r;
    if (sc.send == wrMode::cycle) p->receiveRespCycle( r ); else p->receiveResp( r );
    ++run.resps;
    expectEqual( run, "bid", r.bid, sc.bursts[b].id );
    expectEqual( run, "bresp", r.bresp, respFor( b, 0 ) );
    checkUser( run, "buser", r.user, val( TAG_BUSER, b, 0 ) );
}

template <class T>
static void wrSender( typename T::out& p, const wrScenario& sc, axiRun& run )
{
    if (sc.send == wrMode::cycle) p->setCycleTransaction( PORTTYPE_OUT );
    const int n = (int)sc.bursts.size();
    if (sc.serial) {
        for (int b = 0; b < n; ++b) {
            if (sc.dataFirst) {
                wrSendBurst<T>( p, sc, b );
                wrSendAddr<T>( p, sc, b );
            } else {
                wrSendAddr<T>( p, sc, b );
                wrSendBurst<T>( p, sc, b );
            }
            wrReceiveResp<T>( p, sc, run, b );
        }
    } else {
        if (sc.dataFirst) {
            for (int b = 0; b < n; ++b) wrSendBurst<T>( p, sc, b );
            for (int b = 0; b < n; ++b) wrSendAddr<T>( p, sc, b );
        } else {
            for (int b = 0; b < n; ++b) wrSendAddr<T>( p, sc, b );
            for (int b = 0; b < n; ++b) wrSendBurst<T>( p, sc, b );
        }
        for (int b : sc.respOrder) wrReceiveResp<T>( p, sc, run, b );
    }
    run.done = sc_core::sc_time_stamp();
    run.senderDone = true;
}

template <class T>
static void wrReceiveAddr( typename T::in& p, const wrScenario& sc, axiRun& run, int b )
{
    const axiBurst& bu = sc.bursts[b];
    typename T::addr a;
    p->receiveAddr( a );
    expectEqual( run, "awid", a.awid, bu.id );
    expectEqual( run, "awaddr", a.awaddr.value, bridged( val( TAG_ADDR, b, 0 ), run.direct ) );
    expectEqual( run, "awlen", a.awlen, bu.len );
    expectEqual( run, "awsize", a.awsize, 2 );
    expectEqual( run, "awburst", a.awburst, AXIBURST_INCR );
    checkUser( run, "awuser", a.user, val( TAG_AUSER, b, 0 ) );
}

template <class T>
static void wrReceiveBurst( typename T::in& p, const wrScenario& sc, axiRun& run, int b )
{
    const int len = sc.bursts[b].len;
    if (sc.recv == wrMode::burst) {
        typename T::data d;
        p->receiveData( d );
        expectEqual( run, "received beat count", p->getReceiveBeatCount(), len + 1 );
        const typename T::data* buf = reinterpret_cast<const typename T::data*>( p->getReceiveDataPtr() );
        for (int i = 0; i <= len; ++i) wrCheckBeat<T>( run, buf[i], sc, b, i );
    } else {
        for (int i = 0; i <= len; ++i) {
            typename T::data d;
            if (sc.recv == wrMode::cycle) p->receiveDataCycle( d ); else p->receiveData( d );
            wrCheckBeat<T>( run, d, sc, b, i );
        }
    }
    ++run.bursts;
}

template <class T>
static void wrSendResp( typename T::in& p, const wrScenario& sc, int b )
{
    pace( 2 );
    typename T::resp r;
    r.bid = sc.bursts[b].id;
    r.bresp = respFor( b, 0 );
    putUser( r.user, val( TAG_BUSER, b, 0 ) );
    if (sc.recv == wrMode::cycle) p->sendRespCycle( r ); else p->sendResp( r );
}

template <class T>
static void wrReceiver( typename T::in& p, const wrScenario& sc, axiRun& run )
{
    if (sc.recv == wrMode::cycle) p->setCycleTransaction( PORTTYPE_IN );
    const int n = (int)sc.bursts.size();
    if (sc.serial) {
        for (int b = 0; b < n; ++b) {
            if (sc.dataFirst) {
                wrReceiveBurst<T>( p, sc, run, b );
                wrReceiveAddr<T>( p, sc, run, b );
            } else {
                wrReceiveAddr<T>( p, sc, run, b );
                wrReceiveBurst<T>( p, sc, run, b );
            }
            wrSendResp<T>( p, sc, b );
        }
    } else {
        if (sc.dataFirst) {
            for (int b = 0; b < n; ++b) wrReceiveBurst<T>( p, sc, run, b );
            for (int b = 0; b < n; ++b) wrReceiveAddr<T>( p, sc, run, b );
        } else {
            for (int b = 0; b < n; ++b) wrReceiveAddr<T>( p, sc, run, b );
            for (int b = 0; b < n; ++b) wrReceiveBurst<T>( p, sc, run, b );
        }
        for (int b : sc.respOrder) wrSendResp<T>( p, sc, b );
    }
    run.receiverDone = true;
}

template <class Up, class Down, bool DA, bool DD, bool DS>
struct wrThunkHarness : sc_core::sc_module
{
    using thunker_t = axi_write_port_thunker<typename Up::A, typename Up::D, typename Up::S,
                                             typename Down::A, typename Down::D, typename Down::S, DA, DD, DS,
                                             typename Up::AWU, typename Up::WU, typename Up::BU, typename Up::ID, 4,
                                             typename Down::AWU, typename Down::WU, typename Down::BU, typename Down::ID, 4>;
    std::unique_ptr<typename Up::chan> upChan;
    std::unique_ptr<typename Up::out> peerOut;
    std::unique_ptr<typename Up::in> peerIn;
    std::unique_ptr<typename Up::in> upInPort;
    std::unique_ptr<typename Up::out> upOutPort;
    std::unique_ptr<typename Down::in> childIn;
    std::unique_ptr<typename Down::out> childOut;
    std::unique_ptr<thunker_t> thunker;

    wrThunkHarness( sc_core::sc_module_name n, shape s, const wrScenario& sc, axiRun& run )
      : sc_core::sc_module( n ), upChan( makeChan<Up>( sc.multicycle, sc.fixedSize, sc.bufferBeats ) )
    {
        if (childConsumes( s )) {
            peerOut = std::make_unique<typename Up::out>( "peerOut" );
            ( *peerOut )( *upChan );
            childIn = std::make_unique<typename Down::in>( "childIn" );
            if (s == shape::connectionMap) {
                upInPort = std::make_unique<typename Up::in>( "upInPort" );
                thunker = std::make_unique<thunker_t>( "thunker", *upInPort, *childIn, "tb" );
                ( *upInPort )( *upChan );
            } else {
                thunker = std::make_unique<thunker_t>( "thunker", static_cast<typename Up::in_if&>( *upChan ), *childIn, "tb" );
            }
            sc_core::sc_spawn( [this, &sc, &run]() { wrSender<Up>( *peerOut, sc, run ); } );
            sc_core::sc_spawn( [this, &sc, &run]() { wrReceiver<Down>( *childIn, sc, run ); } );
        } else {
            peerIn = std::make_unique<typename Up::in>( "peerIn" );
            ( *peerIn )( *upChan );
            childOut = std::make_unique<typename Down::out>( "childOut" );
            if (s == shape::producerPort) {
                upOutPort = std::make_unique<typename Up::out>( "upOutPort" );
                thunker = std::make_unique<thunker_t>( "thunker", *upOutPort, *childOut, "tb" );
                ( *upOutPort )( *upChan );
            } else {
                thunker = std::make_unique<thunker_t>( "thunker", static_cast<typename Up::out_if&>( *upChan ), *childOut, "tb" );
            }
            sc_core::sc_spawn( [this, &sc, &run]() { wrSender<Down>( *childOut, sc, run ); } );
            sc_core::sc_spawn( [this, &sc, &run]() { wrReceiver<Up>( *peerIn, sc, run ); } );
        }
    }
};

template <class T>
struct wrDirectHarness : sc_core::sc_module
{
    std::unique_ptr<typename T::chan> chan;
    typename T::out snd;
    typename T::in rcv;

    wrDirectHarness( sc_core::sc_module_name n, const wrScenario& sc, axiRun& run )
      : sc_core::sc_module( n ), chan( makeChan<T>( sc.multicycle, sc.fixedSize, sc.bufferBeats ) ), snd( "snd" ), rcv( "rcv" )
    {
        snd( *chan );
        rcv( *chan );
        sc_core::sc_spawn( [this, &sc, &run]() { wrSender<T>( snd, sc, run ); } );
        sc_core::sc_spawn( [this, &sc, &run]() { wrReceiver<T>( rcv, sc, run ); } );
    }
};

// ===========================================================================
// Cases
// ===========================================================================
// Storage-differing bundles, user sidebands bound on both sides.
using rdUp = rdT<narrowSt, narrowSt, userNarrowSt, userNarrowSt, wideIdT>;
using rdDown = rdT<wideSt, wideSt, userWideSt, userWideSt>;
// The receiving side of each leg binds the user sideband, the sending side does
// not: aruser is received by a consumer child, ruser by the parent requester.
using rdUpRxR = rdT<narrowSt, narrowSt, std::monostate, userNarrowSt, wideIdT>;
using rdDownRxAR = rdT<wideSt, wideSt, userWideSt, std::monostate>;
// The same for a producer child: aruser is received by the parent responder.
using rdUpRxAR = rdT<narrowSt, narrowSt, userNarrowSt, std::monostate, wideIdT>;
using rdDownRxR = rdT<wideSt, wideSt, std::monostate, userWideSt>;
// Identical storage under a direct verdict.
using rdMaskA = rdT<maskASt, maskASt>;
using rdMaskB = rdT<maskBSt, maskBSt>;

using wrUp = wrT<narrowSt, narrowSt, narrowSt, userNarrowSt, userNarrowSt, userNarrowSt, wideIdT>;
using wrDown = wrT<wideSt, wideSt, wideSt, userWideSt, userWideSt, userWideSt>;
// A consumer child receives AW and W, the parent sender receives B.
using wrUpRxB = wrT<narrowSt, narrowSt, narrowSt, std::monostate, std::monostate, userNarrowSt, wideIdT>;
using wrDownRxAW = wrT<wideSt, wideSt, wideSt, userWideSt, userWideSt, std::monostate>;
// A producer child sends AW and W to the parent receiver and receives B.
using wrUpRxAW = wrT<narrowSt, narrowSt, narrowSt, userNarrowSt, userNarrowSt, std::monostate, wideIdT>;
using wrDownRxB = wrT<wideSt, wideSt, wideSt, std::monostate, std::monostate, userWideSt>;
using wrMaskA = wrT<maskASt, maskASt, maskASt>;
using wrMaskB = wrT<maskBSt, maskBSt, maskBSt>;

// Two 256-beat bursts on distinct ids.
static const rdScenario RD_CYCLE = { rdMode::cycle, true, false, { { 1, 255 }, { 2, 255 } }, { 0, 1 } };
static const rdScenario RD_BURST = { rdMode::burst, true, false, { { 1, 255 }, { 2, 7 } }, { 0, 1 } };
// Four ARs outstanding from one thread, two on the same id with different
// lengths, returned out of order across ids.
static const rdScenario RD_OUTSTANDING_BURST = { rdMode::burst, true, false,
                                                 { { 1, 3 }, { 2, 0 }, { 1, 1 }, { 3, 15 } }, { 3, 0, 1, 2 } };
static const rdScenario RD_OUTSTANDING_CYCLE = { rdMode::cycle, true, false,
                                                 { { 1, 3 }, { 2, 0 }, { 1, 1 }, { 3, 15 } }, { 3, 0, 1, 2 } };
static const rdScenario RD_BEAT = { rdMode::beat, false, true, { { 1, 0 }, { 2, 0 }, { 3, 0 } }, {} };
static const rdScenario RD_DIRECT = { rdMode::burst, true, false, { { 1, 15 }, { 2, 3 } }, { 0, 1 } };

static const std::vector<axiBurst> WR_LONG = { { 1, 255 }, { 1, 15 } };
static const std::vector<axiBurst> WR_SINGLE = { { 1, 0 }, { 2, 0 }, { 3, 0 } };
static const wrScenario WR_BURST_BURST = { wrMode::burst, wrMode::burst, true, true, false, WR_LONG, {} };
static const wrScenario WR_BURST_CYCLE = { wrMode::burst, wrMode::cycle, true, true, false, WR_LONG, {} };
static const wrScenario WR_CYCLE_BURST = { wrMode::cycle, wrMode::burst, true, true, false, WR_LONG, {} };
static const wrScenario WR_CYCLE_CYCLE = { wrMode::cycle, wrMode::cycle, true, true, false, WR_LONG, {} };
// Without a burst buffer a transactional sender carries one beat per burst, and
// a cycle sender needs a cycle receiver.
static const wrScenario WR_BEAT_BEAT_NMC = { wrMode::beat, wrMode::beat, false, true, false, WR_SINGLE, {} };
static const wrScenario WR_BEAT_CYCLE_NMC = { wrMode::beat, wrMode::cycle, false, true, false, WR_SINGLE, {} };
static const wrScenario WR_CYCLE_CYCLE_NMC = { wrMode::cycle, wrMode::cycle, false, true, false, { { 1, 15 }, { 2, 3 } }, {} };
// Three AWs outstanding from one thread, two on the same id, B out of order.
static const wrScenario WR_OUTSTANDING = { wrMode::burst, wrMode::burst, true, false, false,
                                           { { 1, 3 }, { 2, 0 }, { 1, 1 } }, { 1, 0, 2 } };
static const wrScenario WR_DATA_FIRST_CYCLE = { wrMode::cycle, wrMode::cycle, false, true, true, { { 1, 7 }, { 2, 3 } }, {} };
static const wrScenario WR_DATA_FIRST_BEAT = { wrMode::beat, wrMode::beat, false, true, true, WR_SINGLE, {} };
static const wrScenario WR_DATA_FIRST_BURST = { wrMode::burst, wrMode::burst, true, true, true,
                                               { { 1, 0 }, { 2, 255 }, { 1, 7 }, { 3, 0 } }, {} };
static const wrScenario WR_DATA_FIRST_OUTSTANDING = { wrMode::burst, wrMode::burst, true, false, true,
                                                     { { 1, 7 }, { 2, 0 }, { 1, 3 } }, { 1, 0, 2 } };
// No explicit send count: the fixed-size buffer includes allocation padding.
static const wrScenario WR_DATA_FIRST_FIXED = { wrMode::burst, wrMode::burst, true, true, true,
                                               { { 1, 3 }, { 2, 3 }, { 1, 3 } }, {}, true, 4 };
static const wrScenario WR_FIXED = { wrMode::burst, wrMode::burst, true, true, false,
                                    { { 1, 3 }, { 2, 3 }, { 1, 3 } }, {}, true, 4 };
static const rdScenario RD_FIXED = { rdMode::burst, true, true,
                                    { { 1, 3 }, { 2, 3 }, { 1, 3 } }, {}, true, 4 };
static const rdScenario RD_FIXED_MAX = { rdMode::burst, true, true,
                                        { { 1, 255 }, { 2, 255 } }, {}, true, 256 };
static const wrScenario WR_DIRECT = { wrMode::burst, wrMode::burst, true, true, false, { { 1, 15 }, { 2, 3 } }, {} };

struct caseEntry
{
    std::string name;
    // Builds the harnesses and returns the post-simulation checks.
    std::function<std::function<void()>( std::vector<std::unique_ptr<sc_core::sc_module>>& )> build;
};

static const char* shapeName( shape s )
{
    switch (s) {
        case shape::connections: return "connections";
        case shape::connectionMap: return "connectionMap";
        case shape::producer: return "producer";
        case shape::producerPort: return "producerPort";
    }
    return "";
}

static std::function<void()> finishChecks( std::shared_ptr<axiRun> thunked, std::shared_ptr<axiRun> control,
                                           int bursts, int beats, bool write )
{
    return [thunked, control, bursts, beats, write]() {
        for (axiRun* run : { thunked.get(), control.get() }) {
            expectEqual( *run, "sender finished", run->senderDone, true );
            expectEqual( *run, "receiver finished", run->receiverDone, true );
            expectEqual( *run, "bursts", run->bursts, bursts );
            expectEqual( *run, "beats", run->beats, beats );
            if (write) expectEqual( *run, "one B per burst", run->resps, bursts );
        }
        expectEqual( *thunked, "finish time (ps) matches direct connection",
                     thunked->done.value(), control->done.value() );
    };
}

static int totalBeats( const std::vector<axiBurst>& bursts )
{
    int n = 0;
    for (const axiBurst& b : bursts) n += b.len + 1;
    return n;
}

template <class Up, class Down, bool DA, bool DD>
static caseEntry rdCase( const std::string& stem, shape s, const rdScenario& sc, bool direct, bool userDirect,
                         bool userCrosses )
{
    std::string name = std::string( "rd_" ) + stem + "_" + shapeName( s );
    return { name, [name, s, &sc, direct, userDirect, userCrosses]( std::vector<std::unique_ptr<sc_core::sc_module>>& keep ) {
        auto thunked = std::make_shared<axiRun>();
        thunked->label = name;
        thunked->direct = direct;
        thunked->userDirect = userDirect;
        thunked->userCrosses = userCrosses;
        auto control = std::make_shared<axiRun>();
        control->label = name + "_control";
        keep.push_back( std::make_unique<rdThunkHarness<Up, Down, DA, DD>>( name.c_str(), s, sc, *thunked ) );
        keep.push_back( std::make_unique<rdDirectHarness<Up>>( control->label.c_str(), sc, *control ) );
        return finishChecks( thunked, control, (int)sc.bursts.size(), totalBeats( sc.bursts ), false );
    } };
}

template <class Up, class Down, bool DA, bool DD, bool DS>
static caseEntry wrCase( const std::string& stem, shape s, const wrScenario& sc, bool direct, bool userDirect,
                         bool userCrosses )
{
    std::string name = std::string( "wr_" ) + stem + "_" + shapeName( s );
    return { name, [name, s, &sc, direct, userDirect, userCrosses]( std::vector<std::unique_ptr<sc_core::sc_module>>& keep ) {
        auto thunked = std::make_shared<axiRun>();
        thunked->label = name;
        thunked->direct = direct;
        thunked->userDirect = userDirect;
        thunked->userCrosses = userCrosses;
        auto control = std::make_shared<axiRun>();
        control->label = name + "_control";
        keep.push_back( std::make_unique<wrThunkHarness<Up, Down, DA, DD, DS>>( name.c_str(), s, sc, *thunked ) );
        keep.push_back( std::make_unique<wrDirectHarness<Up>>( control->label.c_str(), sc, *control ) );
        return finishChecks( thunked, control, (int)sc.bursts.size(), totalBeats( sc.bursts ), true );
    } };
}

static std::vector<caseEntry> allCases()
{
    const shape ALL[] = { shape::connections, shape::connectionMap, shape::producer, shape::producerPort };
    const shape CHANNEL[] = { shape::connections, shape::producer };
    std::vector<caseEntry> cases;

    for (shape s : ALL) {
        cases.push_back( rdCase<rdUp, rdDown, false, false>( "cycle256", s, RD_CYCLE, false, false, true ) );
        cases.push_back( rdCase<rdUp, rdDown, false, false>( "burst", s, RD_BURST, false, false, true ) );
        cases.push_back( rdCase<rdUp, rdDown, false, false>( "fixed", s, RD_FIXED, false, false, true ) );
        cases.push_back( rdCase<rdUp, rdDown, false, false>( "fixedMax", s, RD_FIXED_MAX, false, false, true ) );
        cases.push_back( rdCase<rdMaskA, rdMaskB, true, true>( "fixedDirect", s, RD_FIXED, true, true, true ) );
    }
    for (shape s : CHANNEL) {
        cases.push_back( rdCase<rdUp, rdDown, false, false>( "outstandingBurst", s, RD_OUTSTANDING_BURST, false, false, true ) );
        cases.push_back( rdCase<rdUp, rdDown, false, false>( "outstandingCycle", s, RD_OUTSTANDING_CYCLE, false, false, true ) );
        cases.push_back( rdCase<rdMaskA, rdMaskB, true, true>( "directBurst", s, RD_DIRECT, true, true, true ) );
    }
    cases.push_back( rdCase<rdUpRxR, rdDownRxAR, false, false>( "userOneSide", shape::connections, RD_BEAT, false, false, false ) );
    cases.push_back( rdCase<rdUpRxAR, rdDownRxR, false, false>( "userOneSide", shape::producer, RD_BEAT, false, false, false ) );

    for (shape s : ALL) {
        cases.push_back( wrCase<wrUp, wrDown, false, false, false>( "burstBurst", s, WR_BURST_BURST, false, false, true ) );
        cases.push_back( wrCase<wrUp, wrDown, false, false, false>( "cycleCycle", s, WR_CYCLE_CYCLE, false, false, true ) );
        cases.push_back( wrCase<wrUp, wrDown, false, false, false>( "dataFirstBurst", s, WR_DATA_FIRST_BURST, false, false, true ) );
        cases.push_back( wrCase<wrUp, wrDown, false, false, false>( "dataFirstOutstanding", s, WR_DATA_FIRST_OUTSTANDING, false, false, true ) );
        cases.push_back( wrCase<wrUp, wrDown, false, false, false>( "dataFirstFixed", s, WR_DATA_FIRST_FIXED, false, false, true ) );
        cases.push_back( wrCase<wrUp, wrDown, false, false, false>( "fixed", s, WR_FIXED, false, false, true ) );
        cases.push_back( wrCase<wrMaskA, wrMaskB, true, true, true>( "fixedDirect", s, WR_FIXED, true, true, true ) );
    }
    for (shape s : CHANNEL) {
        cases.push_back( wrCase<wrUp, wrDown, false, false, false>( "burstCycle", s, WR_BURST_CYCLE, false, false, true ) );
        cases.push_back( wrCase<wrUp, wrDown, false, false, false>( "cycleBurst", s, WR_CYCLE_BURST, false, false, true ) );
        cases.push_back( wrCase<wrUp, wrDown, false, false, false>( "beatBeatNmc", s, WR_BEAT_BEAT_NMC, false, false, true ) );
        cases.push_back( wrCase<wrUp, wrDown, false, false, false>( "beatCycleNmc", s, WR_BEAT_CYCLE_NMC, false, false, true ) );
        cases.push_back( wrCase<wrUp, wrDown, false, false, false>( "cycleCycleNmc", s, WR_CYCLE_CYCLE_NMC, false, false, true ) );
        cases.push_back( wrCase<wrUp, wrDown, false, false, false>( "outstanding", s, WR_OUTSTANDING, false, false, true ) );
        cases.push_back( wrCase<wrUp, wrDown, false, false, false>( "dataFirstCycle", s, WR_DATA_FIRST_CYCLE, false, false, true ) );
        cases.push_back( wrCase<wrUp, wrDown, false, false, false>( "dataFirstBeat", s, WR_DATA_FIRST_BEAT, false, false, true ) );
        cases.push_back( wrCase<wrMaskA, wrMaskB, true, true, true>( "dataFirstDirect", s, WR_DATA_FIRST_BURST, true, true, true ) );
        cases.push_back( wrCase<wrMaskA, wrMaskB, true, true, true>( "directBurst", s, WR_DIRECT, true, true, true ) );
    }
    cases.push_back( wrCase<wrUpRxB, wrDownRxAW, false, false, false>( "userOneSide", shape::connections, WR_BEAT_BEAT_NMC, false, false, false ) );
    cases.push_back( wrCase<wrUpRxAW, wrDownRxB, false, false, false>( "userOneSide", shape::producer, WR_BEAT_BEAT_NMC, false, false, false ) );
    return cases;
}

int sc_main( int argc, char* argv[] )
{
    std::vector<caseEntry> cases = allCases();
    const std::string only = argc > 1 ? argv[1] : "";
    if (only == "--list") {
        for (const caseEntry& c : cases) std::printf( "%s\n", c.name.c_str() );
        return 0;
    }

    std::vector<std::unique_ptr<sc_core::sc_module>> keep;
    std::vector<std::function<void()>> checks;
    for (const caseEntry& c : cases) {
        if (only.empty() || c.name == only) checks.push_back( c.build( keep ) );
    }
    if (checks.empty()) {
        std::printf( "FAIL no case named %s\n", only.c_str() );
        return 1;
    }

    sc_core::sc_start();

    for (auto& check : checks) check();
    std::printf( "cases:%zu\n", checks.size() );
    std::printf( "checks:%d failures:%d\n", g_checks, g_failures );
    return g_failures == 0 ? 0 : 1;
}
