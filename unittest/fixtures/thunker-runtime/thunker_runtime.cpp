// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE
//
// Runtime acceptance harness for the payload-carrying protocol port thunkers:
// apb, axi_read, axi_write, axi4_stream, external_reg, memory, pop_ack, raw and
// status. Driven by unittest/test_thunker_runtime.py.
//
// Every template here is explicitly instantiated AND run under the SystemC
// kernel, with the value observed on the far side asserted
// against the value sent. A compile-only check would not distinguish a bridge
// that forwards from one that deadlocks, drops or duplicates.
//
// The harness declares its own payload structures, so it exercises the headers
// without a project database or any generated code.
//
// FOUR THINGS THE RUN ESTABLISHES THAT A SMOKE TEST WOULD NOT.
//
//  1. WHICH ARM OF copyPayload RAN. maskASt and maskBSt are two DIFFERENT
//     declarations over IDENTICAL storage - the pair a verdict of true
//     describes - but their _bitWidth is narrower than that storage. The
//     packed arm packs, copies _bitWidth bits and unpacks, dropping the bits
//     above _bitWidth; the direct arm bit_casts the whole object and keeps
//     them. Sending a value with both halves set therefore says which arm ran.
//     A real payload's arms agree; this pair is built so they do not.
//  2. WHICH SLOT EACH FLAG DRIVES. The two multi-payload protocols are
//     instantiated at complementary verdict subsets - axi4_stream at
//     (tdata, tdest) and then (tid, tuser), memory at (addr) and then (data) -
//     so a flag wired to the wrong payload slot fails.
//  3. BOTH FORWARDING DIRECTIONS. Each protocol is run in the consumer-child
//     shape, which runs thunkIn(), and in the producer-child shape, which runs
//     thunkOut() - separate code in every header, with the channel and
//     interface roles exchanged.
//  4. THE LAZY UP-PORT RESOLUTION. The two port shapes resolve their up-side
//     interface through m_up_port->operator->() on the spawned thread's first
//     iteration rather than capturing it at construction. raw is run in both
//     of them, so that line executes in both directions.
//
// Duplication is caught as well as loss: every sink loop runs forever and
// counts what it received, and sc_main asserts the totals after the kernel has
// drained. A bridge that forwarded each beat twice would satisfy every value
// check and fail the count.
//
// A further set of harnesses pins the protocols' notification semantics:
// status commands, the separate external_reg command, read-back and mirror
// legs, the external_reg owner as sole mirror publisher in all four shapes,
// and memory/apb read data that reqReceive() never fills.

#include "apb_port_thunker.h"
#include "axi4_stream_port_thunker.h"
#include "axi_read_port_thunker.h"
#include "axi_write_port_thunker.h"
#include "external_reg_port_thunker.h"
#include "memory_port_thunker.h"
#include "pop_ack_port_thunker.h"
#include "raw_port_thunker.h"
#include "status_port_thunker.h"

#include <cstdint>
#include <cstdio>
#include <memory>
#include <string>
#include <systemc.h>

static constexpr std::uint32_t PAYLOAD_MASK = 0xFFFFu;

#define A2C_TEST_PAYLOAD( NAME, PACKED )                                        \
    struct NAME                                                                 \
    {                                                                           \
        using _packedSt = PACKED;                                               \
        static constexpr unsigned _bitWidth = 16;                               \
        static constexpr unsigned _byteWidth = sizeof( _packedSt );             \
        /* Masking pack/unpack, as generated structures emit. */                \
        void pack( _packedSt& v ) const { v = value & PAYLOAD_MASK; }           \
        void unpack( const _packedSt& v ) { value = v & PAYLOAD_MASK; }         \
        /* "" selects the channels' no-tracker path, so the harness needs no    \
           generated tracker registration. */                                   \
        static const char* getValueType() { return ""; }                        \
        std::uint64_t getStructValue() const { return value; }                  \
        std::string prt( bool = false ) const { return #NAME; }                 \
        bool operator==( const NAME& o ) const { return value == o.value; }     \
        std::uint32_t value = 0;                                                \
    }

A2C_TEST_PAYLOAD( maskASt, std::uint32_t );
A2C_TEST_PAYLOAD( maskBSt, std::uint32_t );

static_assert( sizeof( maskASt ) == sizeof( maskBSt ) );
static_assert( std::is_trivially_copyable_v<maskASt> && std::is_trivially_copyable_v<maskBSt> );

// A data payload that counts every pack() of a value nobody assigned. A
// completer's reqReceive() leaves the data argument untouched on a read, so an
// adapter that converts it anyway packs the constructor's sentinel.
static constexpr std::uint32_t UNFILLED = 0xDEADBEEFu;
static int g_unfilledPacks = 0;

#define A2C_UNFILLED_PAYLOAD( NAME )                                            \
    struct NAME                                                                 \
    {                                                                           \
        using _packedSt = std::uint32_t;                                        \
        static constexpr unsigned _bitWidth = 16;                               \
        static constexpr unsigned _byteWidth = sizeof( _packedSt );             \
        void pack( _packedSt& v ) const                                         \
        {                                                                       \
            if (value == UNFILLED) ++g_unfilledPacks;                           \
            v = value & PAYLOAD_MASK;                                           \
        }                                                                       \
        void unpack( const _packedSt& v ) { value = v & PAYLOAD_MASK; }         \
        static const char* getValueType() { return ""; }                        \
        std::uint64_t getStructValue() const { return value; }                  \
        std::string prt( bool = false ) const { return #NAME; }                 \
        bool operator==( const NAME& o ) const { return value == o.value; }     \
        std::uint32_t value = UNFILLED;                                         \
    }

A2C_UNFILLED_PAYLOAD( unfilledASt );
A2C_UNFILLED_PAYLOAD( unfilledBSt );

// The value a bridged payload must arrive as: whole under a direct verdict,
// truncated to _bitWidth under a packed one.
static constexpr std::uint32_t bridged( std::uint32_t v, bool direct )
{
    return direct ? v : ( v & PAYLOAD_MASK );
}

static int g_checks = 0;
static int g_failures = 0;

static void expectEqual( const char* what, std::uint64_t got, std::uint64_t want )
{
    ++g_checks;
    if (got != want) {
        ++g_failures;
        std::printf( "FAIL %s: got 0x%llx want 0x%llx\n", what,
                     (unsigned long long)got, (unsigned long long)want );
    }
}

static const int TRANSFERS = 4;

// Distinct high halves per field, so a bridge that crosses two payload slots
// fails rather than passing on equal low halves.
static std::uint32_t dataVal( int i ) { return 0xAAA10000u | (std::uint32_t)( 0x1000 + i ); }
static std::uint32_t addrVal( int i ) { return 0xBBB20000u | (std::uint32_t)( 0x2000 + i ); }
static std::uint32_t idVal( int i )   { return 0xCCC30000u | (std::uint32_t)( 0x3000 + i ); }
static std::uint32_t destVal( int i ) { return 0xDDD40000u | (std::uint32_t)( 0x4000 + i ); }
static std::uint32_t userVal( int i ) { return 0xEEE50000u | (std::uint32_t)( 0x5000 + i ); }

// Spacing between beats for the publish/sample and request/response harnesses.
// The raw harnesses write back to back on purpose: raw_channel::write() must not
// return before the consumer has taken the value, and the thunker is the shape
// that had the consumer parked at the moment of the write.
static void pace() { sc_core::wait( 10, sc_core::SC_NS ); }

// ===========================================================================
// raw
// ===========================================================================
template <class UpT, class DownT, bool Direct>
struct rawConsumerHarness : sc_core::sc_module
{
    raw_channel<UpT> upChan;
    raw_in<DownT> childPort;
    raw_port_thunker<UpT, DownT, Direct> thunker;
    const char* label;
    int beats = 0;

    rawConsumerHarness( sc_core::sc_module_name n, const char* label_ )
      : sc_core::sc_module( n ), upChan( "upChan", "tb" ), childPort( "childPort" ),
        thunker( "thunker", upChan, childPort, "tb" ), label( label_ )
    {
        SC_HAS_PROCESS( rawConsumerHarness );
        SC_THREAD( drive );
        SC_THREAD( sink );
    }

    void drive()
    {
        for (int i = 0; i < TRANSFERS; ++i) {
            UpT v;
            v.value = dataVal( i );
            upChan.write( v, (std::uint64_t)-1 );
        }
    }

    void sink()
    {
        for (int i = 0;; ++i) {
            DownT v;
            childPort->read( v );
            ++beats;
            if (i < TRANSFERS) expectEqual( label, v.value, bridged( dataVal( i ), Direct ) );
        }
    }
};

// Producer-child shape: the child drives, thunkOut() forwards up.
template <class UpT, class DownT, bool Direct>
struct rawProducerHarness : sc_core::sc_module
{
    raw_channel<UpT> upChan;
    raw_out<DownT> childPort;
    raw_port_thunker<UpT, DownT, Direct> thunker;
    const char* label;
    int beats = 0;

    rawProducerHarness( sc_core::sc_module_name n, const char* label_ )
      : sc_core::sc_module( n ), upChan( "upChan", "tb" ), childPort( "childPort" ),
        thunker( "thunker", upChan, childPort, "tb" ), label( label_ )
    {
        SC_HAS_PROCESS( rawProducerHarness );
        SC_THREAD( drive );
        SC_THREAD( sink );
    }

    void drive()
    {
        for (int i = 0; i < TRANSFERS; ++i) {
            DownT v;
            v.value = dataVal( i );
            childPort->write( v, (std::uint64_t)-1 );
        }
    }

    void sink()
    {
        for (int i = 0;; ++i) {
            UpT v;
            upChan.read( v );
            ++beats;
            if (i < TRANSFERS) expectEqual( label, v.value, bridged( dataVal( i ), Direct ) );
        }
    }
};

// connectionMap shape: the up side is an UNBOUND parent port, resolved on the
// spawned thread's first iteration.
template <class UpT, class DownT, bool Direct>
struct rawUpPortConsumerHarness : sc_core::sc_module
{
    raw_channel<UpT> upChan;
    raw_in<UpT> upPort;
    raw_in<DownT> childPort;
    raw_port_thunker<UpT, DownT, Direct> thunker;
    const char* label;
    int beats = 0;

    rawUpPortConsumerHarness( sc_core::sc_module_name n, const char* label_ )
      : sc_core::sc_module( n ), upChan( "upChan", "tb" ), upPort( "upPort" ),
        childPort( "childPort" ), thunker( "thunker", upPort, childPort, "tb" ), label( label_ )
    {
        // Bound after the adapter captured the port, which is the ordering the
        // generated container produces and the reason the resolution is lazy.
        upPort( upChan );
        SC_HAS_PROCESS( rawUpPortConsumerHarness );
        SC_THREAD( drive );
        SC_THREAD( sink );
    }

    void drive()
    {
        for (int i = 0; i < TRANSFERS; ++i) {
            UpT v;
            v.value = dataVal( i );
            upChan.write( v, (std::uint64_t)-1 );
        }
    }

    void sink()
    {
        for (int i = 0;; ++i) {
            DownT v;
            childPort->read( v );
            ++beats;
            if (i < TRANSFERS) expectEqual( label, v.value, bridged( dataVal( i ), Direct ) );
        }
    }
};

// producer (out) port shape: unbound parent OUT port, resolved in thunkOut().
template <class UpT, class DownT, bool Direct>
struct rawUpPortProducerHarness : sc_core::sc_module
{
    raw_channel<UpT> upChan;
    raw_out<UpT> upPort;
    raw_out<DownT> childPort;
    raw_port_thunker<UpT, DownT, Direct> thunker;
    const char* label;
    int beats = 0;

    rawUpPortProducerHarness( sc_core::sc_module_name n, const char* label_ )
      : sc_core::sc_module( n ), upChan( "upChan", "tb" ), upPort( "upPort" ),
        childPort( "childPort" ), thunker( "thunker", upPort, childPort, "tb" ), label( label_ )
    {
        upPort( upChan );
        SC_HAS_PROCESS( rawUpPortProducerHarness );
        SC_THREAD( drive );
        SC_THREAD( sink );
    }

    void drive()
    {
        for (int i = 0; i < TRANSFERS; ++i) {
            DownT v;
            v.value = dataVal( i );
            childPort->write( v, (std::uint64_t)-1 );
        }
    }

    void sink()
    {
        for (int i = 0;; ++i) {
            UpT v;
            upChan.read( v );
            ++beats;
            if (i < TRANSFERS) expectEqual( label, v.value, bridged( dataVal( i ), Direct ) );
        }
    }
};

// ===========================================================================
// status
// ===========================================================================
template <class UpT, class DownT, bool Direct>
struct statusConsumerHarness : sc_core::sc_module
{
    status_channel<UpT> upChan;
    status_in<DownT> childPort;
    status_port_thunker<UpT, DownT, Direct> thunker;
    const char* label;
    int beats = 0;

    statusConsumerHarness( sc_core::sc_module_name n, const char* label_ )
      : sc_core::sc_module( n ), upChan( "upChan", "tb" ), childPort( "childPort" ),
        thunker( "thunker", upChan, childPort, "tb" ), label( label_ )
    {
        SC_HAS_PROCESS( statusConsumerHarness );
        SC_THREAD( drive );
        SC_THREAD( sink );
    }

    void drive()
    {
        for (int i = 0; i < TRANSFERS; ++i) {
            // status publishes rather than handshakes: a reader that is not
            // waiting when the value changes never sees it, so each update is
            // given its own time step.
            pace();
            UpT v;
            v.value = dataVal( i );
            upChan.write( v );
        }
    }

    void sink()
    {
        for (int i = 0;; ++i) {
            DownT v;
            childPort->read( v );
            ++beats;
            if (i < TRANSFERS) expectEqual( label, v.value, bridged( dataVal( i ), Direct ) );
        }
    }
};

template <class UpT, class DownT, bool Direct>
struct statusProducerHarness : sc_core::sc_module
{
    status_channel<UpT> upChan;
    status_out<DownT> childPort;
    status_port_thunker<UpT, DownT, Direct> thunker;
    const char* label;
    int beats = 0;

    statusProducerHarness( sc_core::sc_module_name n, const char* label_ )
      : sc_core::sc_module( n ), upChan( "upChan", "tb" ), childPort( "childPort" ),
        thunker( "thunker", upChan, childPort, "tb" ), label( label_ )
    {
        SC_HAS_PROCESS( statusProducerHarness );
        SC_THREAD( drive );
        SC_THREAD( sink );
    }

    void drive()
    {
        for (int i = 0; i < TRANSFERS; ++i) {
            pace();
            DownT v;
            v.value = dataVal( i );
            childPort->write( v );
        }
    }

    void sink()
    {
        for (int i = 0;; ++i) {
            UpT v;
            upChan.read( v );
            ++beats;
            if (i < TRANSFERS) expectEqual( label, v.value, bridged( dataVal( i ), Direct ) );
        }
    }
};

// status initial value: the up side's value at construction reaches the child
// before any update, and seeding it is not an update, so no reader is woken.
static constexpr std::uint32_t STATUS_INITIAL = 0x5A5Au;

template <class UpT, class DownT, bool Direct>
struct statusInitialConsumerHarness : sc_core::sc_module
{
    status_channel<UpT> upChan;
    status_in<DownT> childPort;
    status_port_thunker<UpT, DownT, Direct> thunker;
    const char* label;
    int beats = 0;

    statusInitialConsumerHarness( sc_core::sc_module_name n, const char* label_ )
      : sc_core::sc_module( n ), upChan( "upChan", "tb", STATUS_INITIAL ), childPort( "childPort" ),
        thunker( "thunker", upChan, childPort, "tb" ), label( label_ )
    {
        SC_HAS_PROCESS( statusInitialConsumerHarness );
        SC_THREAD( sample );
        SC_THREAD( sink );
    }

    void sample()
    {
        pace();
        expectEqual( label, childPort->readNonBlocking().value, STATUS_INITIAL );
    }

    void sink()
    {
        while (true) {
            DownT v;
            childPort->read( v );
            ++beats;
        }
    }
};

template <class UpT, class DownT, bool Direct>
struct statusInitialProducerHarness : sc_core::sc_module
{
    status_channel<UpT> upChan;
    status_out<DownT> childPort;
    status_port_thunker<UpT, DownT, Direct> thunker;
    const char* label;
    int beats = 0;

    statusInitialProducerHarness( sc_core::sc_module_name n, const char* label_ )
      : sc_core::sc_module( n ), upChan( "upChan", "tb", STATUS_INITIAL ), childPort( "childPort" ),
        thunker( "thunker", upChan, childPort, "tb" ), label( label_ )
    {
        SC_HAS_PROCESS( statusInitialProducerHarness );
        SC_THREAD( sample );
        SC_THREAD( sink );
    }

    void sample()
    {
        pace();
        expectEqual( label, childPort->readNonBlocking().value, STATUS_INITIAL );
        expectEqual( label, upChan.readNonBlocking().value, STATUS_INITIAL );
    }

    void sink()
    {
        while (true) {
            UpT v;
            upChan.read( v );
            ++beats;
        }
    }
};

// The lazy port shapes resolve the up side only once binding completes, so
// their seed is taken from the bound parent port rather than a captured iface.
template <class UpT, class DownT, bool Direct>
struct statusInitialUpPortConsumerHarness : sc_core::sc_module
{
    status_channel<UpT> upChan;
    status_in<UpT> upPort;
    status_in<DownT> childPort;
    status_port_thunker<UpT, DownT, Direct> thunker;
    const char* label;
    int beats = 0;

    statusInitialUpPortConsumerHarness( sc_core::sc_module_name n, const char* label_ )
      : sc_core::sc_module( n ), upChan( "upChan", "tb", STATUS_INITIAL ), upPort( "upPort" ),
        childPort( "childPort" ), thunker( "thunker", upPort, childPort, "tb" ), label( label_ )
    {
        upPort( upChan );
        SC_HAS_PROCESS( statusInitialUpPortConsumerHarness );
        SC_THREAD( sample );
        SC_THREAD( sink );
    }

    void sample()
    {
        pace();
        expectEqual( label, childPort->readNonBlocking().value, STATUS_INITIAL );
    }

    void sink()
    {
        while (true) {
            DownT v;
            childPort->read( v );
            ++beats;
        }
    }
};

template <class UpT, class DownT, bool Direct>
struct statusInitialUpPortProducerHarness : sc_core::sc_module
{
    status_channel<UpT> upChan;
    status_out<UpT> upPort;
    status_out<DownT> childPort;
    status_port_thunker<UpT, DownT, Direct> thunker;
    const char* label;
    int beats = 0;

    statusInitialUpPortProducerHarness( sc_core::sc_module_name n, const char* label_ )
      : sc_core::sc_module( n ), upChan( "upChan", "tb", STATUS_INITIAL ), upPort( "upPort" ),
        childPort( "childPort" ), thunker( "thunker", upPort, childPort, "tb" ), label( label_ )
    {
        upPort( upChan );
        SC_HAS_PROCESS( statusInitialUpPortProducerHarness );
        SC_THREAD( sample );
        SC_THREAD( sink );
    }

    void sample()
    {
        pace();
        expectEqual( label, childPort->readNonBlocking().value, STATUS_INITIAL );
        expectEqual( label, upChan.readNonBlocking().value, STATUS_INITIAL );
    }

    void sink()
    {
        while (true) {
            UpT v;
            upChan.read( v );
            ++beats;
        }
    }
};

// Two thunkers in a chain, as a transit container produces: the inner one's up
// side is a port bound to the outer one's owned channel. A container builds its
// children before its own members, so the inner seed can run first; it must
// still see the parent's value. Both construction orders are run.
template <bool InnerFirst>
struct statusChainConsumerHarness : sc_core::sc_module
{
    using Outer = status_port_thunker<maskASt, maskBSt, false>;
    using Inner = status_port_thunker<maskBSt, maskASt, false>;
    status_channel<maskASt> upChan;
    status_in<maskBSt> midPort;
    status_in<maskASt> childPort;
    std::unique_ptr<Outer> outer;
    std::unique_ptr<Inner> inner;
    const char* label;
    int beats = 0;

    statusChainConsumerHarness( sc_core::sc_module_name n, const char* label_ )
      : sc_core::sc_module( n ), upChan( "upChan", "tb", STATUS_INITIAL ), midPort( "midPort" ),
        childPort( "childPort" ), label( label_ )
    {
        if (InnerFirst) inner = std::make_unique<Inner>( "inner", midPort, childPort, "tb" );
        outer = std::make_unique<Outer>( "outer", upChan, midPort, "tb" );
        if (!InnerFirst) inner = std::make_unique<Inner>( "inner", midPort, childPort, "tb" );
        SC_HAS_PROCESS( statusChainConsumerHarness );
        SC_THREAD( sample );
        SC_THREAD( sink );
    }

    void sample()
    {
        pace();
        expectEqual( label, childPort->readNonBlocking().value, STATUS_INITIAL );
    }

    void sink()
    {
        while (true) {
            maskASt v;
            childPort->read( v );
            ++beats;
        }
    }
};

template <bool InnerFirst>
struct statusChainProducerHarness : sc_core::sc_module
{
    using Outer = status_port_thunker<maskASt, maskBSt, false>;
    using Inner = status_port_thunker<maskBSt, maskASt, false>;
    status_channel<maskASt> upChan;
    status_out<maskBSt> midPort;
    status_out<maskASt> childPort;
    std::unique_ptr<Outer> outer;
    std::unique_ptr<Inner> inner;
    const char* label;
    int beats = 0;

    statusChainProducerHarness( sc_core::sc_module_name n, const char* label_ )
      : sc_core::sc_module( n ), upChan( "upChan", "tb", STATUS_INITIAL ), midPort( "midPort" ),
        childPort( "childPort" ), label( label_ )
    {
        if (InnerFirst) inner = std::make_unique<Inner>( "inner", midPort, childPort, "tb" );
        outer = std::make_unique<Outer>( "outer", upChan, midPort, "tb" );
        if (!InnerFirst) inner = std::make_unique<Inner>( "inner", midPort, childPort, "tb" );
        SC_HAS_PROCESS( statusChainProducerHarness );
        SC_THREAD( sample );
        SC_THREAD( sink );
    }

    void sample()
    {
        pace();
        expectEqual( label, childPort->readNonBlocking().value, STATUS_INITIAL );
        expectEqual( label, upChan.readNonBlocking().value, STATUS_INITIAL );
    }

    void sink()
    {
        while (true) {
            maskASt v;
            upChan.read( v );
            ++beats;
        }
    }
};

// A child producer that writes before its first wait() may run before or after
// the adapter's thread; the kernel does not fix the order. The write must reach
// the parent either way, so both creation orders are run.
static constexpr std::uint32_t STATUS_TIME_ZERO = 0x1234u;

template <class UpT, class DownT, bool Direct, bool WriterFirst>
struct statusTimeZeroProducerHarness : sc_core::sc_module
{
    status_channel<UpT> upChan;
    status_out<DownT> childPort;
    std::unique_ptr<status_port_thunker<UpT, DownT, Direct>> thunker;
    int beats = 0;

    statusTimeZeroProducerHarness( sc_core::sc_module_name n )
      : sc_core::sc_module( n ), upChan( "upChan", "tb", STATUS_INITIAL ), childPort( "childPort" )
    {
        SC_HAS_PROCESS( statusTimeZeroProducerHarness );
        if (WriterFirst) SC_THREAD( drive );
        thunker = std::make_unique<status_port_thunker<UpT, DownT, Direct>>( "thunker", upChan, childPort, "tb" );
        if (!WriterFirst) SC_THREAD( drive );
        SC_THREAD( sink );
    }

    void drive()
    {
        DownT v;
        v.value = STATUS_TIME_ZERO;
        childPort->write( v );
    }

    void sink()
    {
        while (true) {
            UpT v;
            upChan.read( v );
            ++beats;
        }
    }
};

// status notification semantics. read() cannot tell a value change from a
// command, so a transparent bridge raises exactly one far-side notification per
// near-side one. The sequence mixes the three writers: write() drops a repeat
// of the published value, reg_write_cmd() always notifies, reg_write() never
// does. The same sequence also drives a plain reference channel, so the pinned
// count is what the channel itself does.
static const int STATUS_SEQUENCE_NOTIFICATIONS = 4;

template <class T, class Writer>
static void statusCommandSequence( Writer* w )
{
    T x, y;
    x.value = dataVal( 0 );
    y.value = dataVal( 1 );
    pace(); w->write( x );          // notifies
    pace(); w->write( x );          // repeat of the published value: silent
    pace(); w->reg_write_cmd( x );  // command: notifies although unchanged
    pace(); w->reg_write_cmd( x );  // notifies again
    pace(); w->reg_write( y );      // silent update
    pace(); w->write( x );          // differs from the silent value: notifies
}

template <class UpT, class DownT, bool Direct>
struct statusCommandConsumerHarness : sc_core::sc_module
{
    status_channel<UpT> refChan;
    status_channel<UpT> upChan;
    status_in<DownT> childPort;
    status_port_thunker<UpT, DownT, Direct> thunker;
    const char* label;
    int refBeats = 0;
    int beats = 0;

    statusCommandConsumerHarness( sc_core::sc_module_name n, const char* label_ )
      : sc_core::sc_module( n ), refChan( "refChan", "tb" ), upChan( "upChan", "tb" ),
        childPort( "childPort" ), thunker( "thunker", upChan, childPort, "tb" ), label( label_ )
    {
        SC_HAS_PROCESS( statusCommandConsumerHarness );
        SC_THREAD( driveRef );
        SC_THREAD( drive );
        SC_THREAD( refSink );
        SC_THREAD( sink );
    }

    void driveRef() { statusCommandSequence<UpT>( &refChan ); }
    void drive() { statusCommandSequence<UpT>( &upChan ); }

    void refSink()
    {
        while (true) {
            UpT v;
            refChan.read( v );
            ++refBeats;
        }
    }

    void sink()
    {
        while (true) {
            DownT v;
            childPort->read( v );
            ++beats;
            expectEqual( label, v.value, bridged( dataVal( 0 ), Direct ) );
        }
    }
};

template <class UpT, class DownT, bool Direct>
struct statusCommandProducerHarness : sc_core::sc_module
{
    status_channel<DownT> refChan;
    status_channel<UpT> upChan;
    status_out<DownT> childPort;
    status_port_thunker<UpT, DownT, Direct> thunker;
    const char* label;
    int refBeats = 0;
    int beats = 0;

    statusCommandProducerHarness( sc_core::sc_module_name n, const char* label_ )
      : sc_core::sc_module( n ), refChan( "refChan", "tb" ), upChan( "upChan", "tb" ),
        childPort( "childPort" ), thunker( "thunker", upChan, childPort, "tb" ), label( label_ )
    {
        SC_HAS_PROCESS( statusCommandProducerHarness );
        SC_THREAD( driveRef );
        SC_THREAD( drive );
        SC_THREAD( refSink );
        SC_THREAD( sink );
    }

    void driveRef() { statusCommandSequence<DownT>( &refChan ); }
    void drive() { statusCommandSequence<DownT>( childPort.operator->() ); }

    void refSink()
    {
        while (true) {
            DownT v;
            refChan.read( v );
            ++refBeats;
        }
    }

    void sink()
    {
        while (true) {
            UpT v;
            upChan.read( v );
            ++beats;
            expectEqual( label, v.value, bridged( dataVal( 0 ), Direct ) );
        }
    }
};

// ===========================================================================
// pop_ack - the payload travels on the acknowledge, opposite to the request.
// ===========================================================================
template <class UpT, class DownT, bool Direct>
struct popAckConsumerHarness : sc_core::sc_module
{
    pop_ack_channel<UpT> upChan;
    pop_ack_in<DownT> childPort;
    pop_ack_port_thunker<UpT, DownT, Direct> thunker;
    const char* label;
    int beats = 0;

    popAckConsumerHarness( sc_core::sc_module_name n, const char* label_ )
      : sc_core::sc_module( n ), upChan( "upChan", "tb" ), childPort( "childPort" ),
        thunker( "thunker", upChan, childPort, "tb" ), label( label_ )
    {
        SC_HAS_PROCESS( popAckConsumerHarness );
        SC_THREAD( drive );
        SC_THREAD( sink );
    }

    void drive()
    {
        for (int i = 0; i < TRANSFERS; ++i) {
            UpT v;
            upChan.pop( v );
            expectEqual( label, v.value, bridged( dataVal( i ), Direct ) );
        }
    }

    void sink()
    {
        for (int i = 0;; ++i) {
            childPort->popReceive();
            ++beats;
            DownT v;
            v.value = dataVal( i );
            childPort->ack( v );
        }
    }
};

template <class UpT, class DownT, bool Direct>
struct popAckProducerHarness : sc_core::sc_module
{
    pop_ack_channel<UpT> upChan;
    pop_ack_out<DownT> childPort;
    pop_ack_port_thunker<UpT, DownT, Direct> thunker;
    const char* label;
    int beats = 0;

    popAckProducerHarness( sc_core::sc_module_name n, const char* label_ )
      : sc_core::sc_module( n ), upChan( "upChan", "tb" ), childPort( "childPort" ),
        thunker( "thunker", upChan, childPort, "tb" ), label( label_ )
    {
        SC_HAS_PROCESS( popAckProducerHarness );
        SC_THREAD( drive );
        SC_THREAD( sink );
    }

    void drive()
    {
        for (int i = 0; i < TRANSFERS; ++i) {
            DownT v;
            childPort->pop( v );
            expectEqual( label, v.value, bridged( dataVal( i ), Direct ) );
        }
    }

    void sink()
    {
        for (int i = 0;; ++i) {
            upChan.popReceive();
            ++beats;
            UpT v;
            v.value = dataVal( i );
            upChan.ack( v );
        }
    }
};

// ===========================================================================
// memory and apb - both the write-data leg and the read-response leg, which is
// why data_t gates four call sites while addr_t gates two. The two protocols
// share the request / complete-on-read handshake, so one harness serves both.
// ===========================================================================
template <template <class, class> class Chan, template <class, class> class InPort,
          template <class, class, class, class, bool, bool> class Thunker,
          class UpA, class UpD, class DownA, class DownD, bool DirectAddr, bool DirectData>
struct reqCompConsumerHarness : sc_core::sc_module
{
    Chan<UpA, UpD> upChan;
    InPort<DownA, DownD> childPort;
    Thunker<UpA, UpD, DownA, DownD, DirectAddr, DirectData> thunker;
    const char* label;
    int beats = 0;

    reqCompConsumerHarness( sc_core::sc_module_name n, const char* label_ )
      : sc_core::sc_module( n ), upChan( "upChan", "tb" ), childPort( "childPort" ),
        thunker( "thunker", upChan, childPort, "tb" ), label( label_ )
    {
        SC_HAS_PROCESS( reqCompConsumerHarness );
        SC_THREAD( drive );
        SC_THREAD( sink );
    }

    void drive()
    {
        for (int i = 0; i < TRANSFERS; ++i) {
            UpA addr;
            UpD data;
            addr.value = addrVal( i );
            data.value = dataVal( i );
            upChan.request( true, addr, data );
            pace();
            UpD readData;
            upChan.request( false, addr, readData );
            expectEqual( label, readData.value, bridged( dataVal( i ), DirectData ) );
        }
    }

    void sink()
    {
        // One transaction per iteration, write and read alternating.
        for (int t = 0;; ++t) {
            bool isWrite = false;
            DownA addr;
            DownD data;
            childPort->reqReceive( isWrite, addr, data );
            ++beats;
            const int i = t / 2;
            if (t < 2 * TRANSFERS) {
                expectEqual( label, isWrite ? 1u : 0u, ( t % 2 ) == 0 ? 1u : 0u );
                expectEqual( label, addr.value, bridged( addrVal( i ), DirectAddr ) );
                if (isWrite) expectEqual( label, data.value, bridged( dataVal( i ), DirectData ) );
            }
            if (!isWrite) {
                DownD resp;
                resp.value = dataVal( i );
                childPort->complete( resp );
            }
        }
    }
};

template <template <class, class> class Chan, template <class, class> class OutPort,
          template <class, class, class, class, bool, bool> class Thunker,
          class UpA, class UpD, class DownA, class DownD, bool DirectAddr, bool DirectData>
struct reqCompProducerHarness : sc_core::sc_module
{
    Chan<UpA, UpD> upChan;
    OutPort<DownA, DownD> childPort;
    Thunker<UpA, UpD, DownA, DownD, DirectAddr, DirectData> thunker;
    const char* label;
    int beats = 0;

    reqCompProducerHarness( sc_core::sc_module_name n, const char* label_ )
      : sc_core::sc_module( n ), upChan( "upChan", "tb" ), childPort( "childPort" ),
        thunker( "thunker", upChan, childPort, "tb" ), label( label_ )
    {
        SC_HAS_PROCESS( reqCompProducerHarness );
        SC_THREAD( drive );
        SC_THREAD( sink );
    }

    void drive()
    {
        for (int i = 0; i < TRANSFERS; ++i) {
            DownA addr;
            DownD data;
            addr.value = addrVal( i );
            data.value = dataVal( i );
            childPort->request( true, addr, data );
            pace();
            DownD readData;
            childPort->request( false, addr, readData );
            expectEqual( label, readData.value, bridged( dataVal( i ), DirectData ) );
        }
    }

    void sink()
    {
        for (int t = 0;; ++t) {
            bool isWrite = false;
            UpA addr;
            UpD data;
            upChan.reqReceive( isWrite, addr, data );
            ++beats;
            const int i = t / 2;
            if (t < 2 * TRANSFERS) {
                expectEqual( label, isWrite ? 1u : 0u, ( t % 2 ) == 0 ? 1u : 0u );
                expectEqual( label, addr.value, bridged( addrVal( i ), DirectAddr ) );
                if (isWrite) expectEqual( label, data.value, bridged( dataVal( i ), DirectData ) );
            }
            if (!isWrite) {
                UpD resp;
                resp.value = dataVal( i );
                upChan.complete( resp );
            }
        }
    }
};

template <class UpA, class UpD, class DownA, class DownD, bool DirectAddr, bool DirectData>
using memoryConsumerHarness = reqCompConsumerHarness<memory_channel, memory_in, memory_port_thunker,
                                                     UpA, UpD, DownA, DownD, DirectAddr, DirectData>;
template <class UpA, class UpD, class DownA, class DownD, bool DirectAddr, bool DirectData>
using memoryProducerHarness = reqCompProducerHarness<memory_channel, memory_out, memory_port_thunker,
                                                     UpA, UpD, DownA, DownD, DirectAddr, DirectData>;
template <class UpA, class UpD, class DownA, class DownD, bool DirectAddr, bool DirectData>
using apbConsumerHarness = reqCompConsumerHarness<apb_channel, apb_in, apb_port_thunker,
                                                  UpA, UpD, DownA, DownD, DirectAddr, DirectData>;
template <class UpA, class UpD, class DownA, class DownD, bool DirectAddr, bool DirectData>
using apbProducerHarness = reqCompProducerHarness<apb_channel, apb_out, apb_port_thunker,
                                                  UpA, UpD, DownA, DownD, DirectAddr, DirectData>;

// ===========================================================================
// external_reg - the register-write leg and the read-back leg are independent,
// which is why one data_t gates four sites and each shape runs two threads.
// ===========================================================================
template <class UpT, class DownT, bool Direct>
struct externalRegConsumerHarness : sc_core::sc_module
{
    external_reg_channel<UpT> upChan;
    external_reg_in<DownT> childPort;
    external_reg_port_thunker<UpT, DownT, Direct> thunker;
    const char* label;
    int beats = 0;

    externalRegConsumerHarness( sc_core::sc_module_name n, const char* label_ )
      : sc_core::sc_module( n ), upChan( "upChan", "tb" ), childPort( "childPort" ),
        thunker( "thunker", upChan, childPort, "tb" ), label( label_ )
    {
        SC_HAS_PROCESS( externalRegConsumerHarness );
        SC_THREAD( drive );
        SC_THREAD( readBack );
        SC_THREAD( echo );
    }

    void drive()
    {
        for (int i = 0; i < TRANSFERS; ++i) {
            pace();
            UpT v;
            v.value = dataVal( i );
            upChan.reg_write_cmd( v );
        }
    }

    void readBack()
    {
        for (int i = 0;; ++i) {
            UpT v;
            upChan.reg_read( v );
            ++beats;
            // Two hops, down then up; the second is idempotent on an already
            // bridged value, so the expectation is the same either way.
            if (i < TRANSFERS) expectEqual( label, v.value, bridged( dataVal( i ), Direct ) );
        }
    }

    void echo()
    {
        for (int i = 0;; ++i) {
            DownT v;
            childPort->read( v );
            ++beats;
            if (i < TRANSFERS) expectEqual( label, v.value, bridged( dataVal( i ), Direct ) );
            childPort->write( v );
        }
    }
};

template <class UpT, class DownT, bool Direct>
struct externalRegProducerHarness : sc_core::sc_module
{
    external_reg_channel<UpT> upChan;
    external_reg_out<DownT> childPort;
    external_reg_port_thunker<UpT, DownT, Direct> thunker;
    const char* label;
    int beats = 0;

    externalRegProducerHarness( sc_core::sc_module_name n, const char* label_ )
      : sc_core::sc_module( n ), upChan( "upChan", "tb" ), childPort( "childPort" ),
        thunker( "thunker", upChan, childPort, "tb" ), label( label_ )
    {
        SC_HAS_PROCESS( externalRegProducerHarness );
        SC_THREAD( drive );
        SC_THREAD( readBack );
        SC_THREAD( echo );
    }

    void drive()
    {
        for (int i = 0; i < TRANSFERS; ++i) {
            pace();
            DownT v;
            v.value = dataVal( i );
            childPort->reg_write_cmd( v );
        }
    }

    void readBack()
    {
        for (int i = 0;; ++i) {
            DownT v;
            childPort->reg_read( v );
            ++beats;
            if (i < TRANSFERS) expectEqual( label, v.value, bridged( dataVal( i ), Direct ) );
        }
    }

    void echo()
    {
        for (int i = 0;; ++i) {
            UpT v;
            upChan.read( v );
            ++beats;
            if (i < TRANSFERS) expectEqual( label, v.value, bridged( dataVal( i ), Direct ) );
            upChan.write( v );
        }
    }
};

// external_reg leg separation. A command (reg_write_cmd) notifies the owner and
// leaves both mirrors alone; the owner's mirror publication (update_mirror)
// crosses to the driver as a mirror update with its notification. Values that
// originate on one side are checked unconverted on that side, so a mirror
// echoed back through the bridge (and truncated by the packed arm) fails.
template <class T>
static T payloadOf( std::uint32_t v )
{
    T out;
    out.value = v;
    return out;
}

// Parent driver on upChan, child register owner behind the bridge.
template <class UpT, class DownT, bool Direct>
struct externalRegMirrorConsumerHarness : sc_core::sc_module
{
    external_reg_channel<UpT> upChan;
    external_reg_in<DownT> childPort;
    external_reg_port_thunker<UpT, DownT, Direct> thunker;
    const char* label;
    int cmdBeats = 0;
    int readBackBeats = 0;
    int upMirrorEvents = 0;
    int downMirrorEvents = 0;

    externalRegMirrorConsumerHarness( sc_core::sc_module_name n, const char* label_ )
      : sc_core::sc_module( n ), upChan( "upChan", "tb" ), childPort( "childPort" ),
        thunker( "thunker", upChan, childPort, "tb" ), label( label_ )
    {
        SC_HAS_PROCESS( externalRegMirrorConsumerHarness );
        SC_THREAD( drive );
        SC_THREAD( ownerCommands );
        SC_THREAD( driverReadBack );
        SC_THREAD( upMirrorWatch );
        SC_THREAD( downMirrorWatch );
    }

    void drive()
    {
        pace(); upChan.reg_write_cmd( payloadOf<UpT>( dataVal( 0 ) ) );
        pace(); upChan.reg_write_cmd( payloadOf<UpT>( dataVal( 0 ) ) );
        pace();
        expectEqual( label, cmdBeats, 2 );
        expectEqual( label, childPort->readNonBlocking().value, 0 );
        expectEqual( label, upChan.readNonBlocking().value, 0 );
        expectEqual( label, upMirrorEvents, 0 );
        expectEqual( label, downMirrorEvents, 0 );

        childPort->update_mirror( payloadOf<DownT>( dataVal( 1 ) ) );
        pace();
        expectEqual( label, upChan.readNonBlocking().value, bridged( dataVal( 1 ), Direct ) );
        expectEqual( label, childPort->readNonBlocking().value, dataVal( 1 ) );
        expectEqual( label, cmdBeats, 2 );
        expectEqual( label, upMirrorEvents, 1 );
        expectEqual( label, downMirrorEvents, 1 );

        upChan.reg_write_cmd( payloadOf<UpT>( dataVal( 2 ) ) );
        pace();
        expectEqual( label, cmdBeats, 3 );
        expectEqual( label, childPort->readNonBlocking().value, dataVal( 1 ) );
        expectEqual( label, upChan.readNonBlocking().value, bridged( dataVal( 1 ), Direct ) );
        expectEqual( label, upMirrorEvents, 1 );
        expectEqual( label, downMirrorEvents, 1 );

        // Two publications one delta apart: the bridge's echo of the first
        // must not overwrite the second on either side.
        childPort->update_mirror( payloadOf<DownT>( dataVal( 3 ) ) );
        sc_core::wait( sc_core::SC_ZERO_TIME );
        childPort->update_mirror( payloadOf<DownT>( dataVal( 4 ) ) );
        pace();
        expectEqual( label, childPort->readNonBlocking().value, dataVal( 4 ) );
        expectEqual( label, upChan.readNonBlocking().value, bridged( dataVal( 4 ), Direct ) );

        // Read-back: the repeat is dropped at the source and so crosses once.
        childPort->write( payloadOf<DownT>( dataVal( 5 ) ) );
        pace();
        childPort->write( payloadOf<DownT>( dataVal( 5 ) ) );
        pace();
        expectEqual( label, readBackBeats, 1 );
    }

    void ownerCommands()
    {
        for (int i = 0;; ++i) {
            DownT v;
            childPort->read( v );
            ++cmdBeats;
            expectEqual( label, v.value, bridged( dataVal( i < 2 ? 0 : 2 ), Direct ) );
        }
    }

    void driverReadBack()
    {
        while (true) {
            UpT v;
            upChan.reg_read( v );
            ++readBackBeats;
            expectEqual( label, v.value, bridged( dataVal( 5 ), Direct ) );
        }
    }

    void upMirrorWatch() { while (true) { upChan.wait_mirror(); ++upMirrorEvents; } }
    void downMirrorWatch() { while (true) { childPort->wait_mirror(); ++downMirrorEvents; } }
};

// Child driver behind the bridge, parent register owner on upChan.
template <class UpT, class DownT, bool Direct>
struct externalRegMirrorProducerHarness : sc_core::sc_module
{
    external_reg_channel<UpT> upChan;
    external_reg_out<DownT> childPort;
    external_reg_port_thunker<UpT, DownT, Direct> thunker;
    const char* label;
    int cmdBeats = 0;
    int readBackBeats = 0;
    int upMirrorEvents = 0;
    int downMirrorEvents = 0;

    externalRegMirrorProducerHarness( sc_core::sc_module_name n, const char* label_ )
      : sc_core::sc_module( n ), upChan( "upChan", "tb" ), childPort( "childPort" ),
        thunker( "thunker", upChan, childPort, "tb" ), label( label_ )
    {
        SC_HAS_PROCESS( externalRegMirrorProducerHarness );
        SC_THREAD( drive );
        SC_THREAD( ownerCommands );
        SC_THREAD( driverReadBack );
        SC_THREAD( upMirrorWatch );
        SC_THREAD( downMirrorWatch );
    }

    void drive()
    {
        pace(); childPort->reg_write_cmd( payloadOf<DownT>( dataVal( 0 ) ) );
        pace(); childPort->reg_write_cmd( payloadOf<DownT>( dataVal( 0 ) ) );
        pace();
        expectEqual( label, cmdBeats, 2 );
        expectEqual( label, upChan.readNonBlocking().value, 0 );
        expectEqual( label, childPort->readNonBlocking().value, 0 );
        expectEqual( label, upMirrorEvents, 0 );
        expectEqual( label, downMirrorEvents, 0 );

        upChan.update_mirror( payloadOf<UpT>( dataVal( 1 ) ) );
        pace();
        expectEqual( label, childPort->readNonBlocking().value, bridged( dataVal( 1 ), Direct ) );
        expectEqual( label, upChan.readNonBlocking().value, dataVal( 1 ) );
        expectEqual( label, cmdBeats, 2 );
        expectEqual( label, upMirrorEvents, 1 );
        expectEqual( label, downMirrorEvents, 1 );

        childPort->reg_write_cmd( payloadOf<DownT>( dataVal( 2 ) ) );
        pace();
        expectEqual( label, cmdBeats, 3 );
        expectEqual( label, upChan.readNonBlocking().value, dataVal( 1 ) );
        expectEqual( label, childPort->readNonBlocking().value, bridged( dataVal( 1 ), Direct ) );
        expectEqual( label, upMirrorEvents, 1 );
        expectEqual( label, downMirrorEvents, 1 );

        upChan.update_mirror( payloadOf<UpT>( dataVal( 3 ) ) );
        sc_core::wait( sc_core::SC_ZERO_TIME );
        upChan.update_mirror( payloadOf<UpT>( dataVal( 4 ) ) );
        pace();
        expectEqual( label, upChan.readNonBlocking().value, dataVal( 4 ) );
        expectEqual( label, childPort->readNonBlocking().value, bridged( dataVal( 4 ), Direct ) );

        upChan.write( payloadOf<UpT>( dataVal( 5 ) ) );
        pace();
        upChan.write( payloadOf<UpT>( dataVal( 5 ) ) );
        pace();
        expectEqual( label, readBackBeats, 1 );
    }

    void ownerCommands()
    {
        for (int i = 0;; ++i) {
            UpT v;
            upChan.read( v );
            ++cmdBeats;
            expectEqual( label, v.value, bridged( dataVal( i < 2 ? 0 : 2 ), Direct ) );
        }
    }

    void driverReadBack()
    {
        while (true) {
            DownT v;
            childPort->reg_read( v );
            ++readBackBeats;
            expectEqual( label, v.value, bridged( dataVal( 5 ), Direct ) );
        }
    }

    void upMirrorWatch() { while (true) { upChan.wait_mirror(); ++upMirrorEvents; } }
    void downMirrorWatch() { while (true) { childPort->wait_mirror(); ++downMirrorEvents; } }
};

// external_reg mirror publisher: the owner publishes back to back and the
// driver side must settle on the owner's last value, with the owner's own
// mirror never written by the bridge. One sequence runs in all four shapes.
// Publications land in one delta, one delta apart and 1 ns apart, and one
// returns to the value before it. The lossy steps republish a value whose
// packed image the driver already holds, so the packed arm forwards a mirror
// that does not change. Where the shape leaves the driver-side mirror
// writable (the consumer shapes' parent channel), a stray write there in the
// same delta as an owner publication must lose to the owner and never reach
// the owner's mirror.
template <class OwnerT, bool Direct>
struct externalRegMirrorPublisher : sc_core::sc_module
{
    const char* label;
    std::uint32_t published = 0;
    int ownerOverwrites = 0;

    externalRegMirrorPublisher( sc_core::sc_module_name n, const char* label_ )
      : sc_core::sc_module( n ), label( label_ )
    {
        SC_HAS_PROCESS( externalRegMirrorPublisher );
        SC_THREAD( publish );
        SC_THREAD( ownerWatch );
    }

    virtual external_reg_in_if<OwnerT>* owner() = 0;
    virtual std::uint32_t driverMirror() = 0;
    virtual void stray( std::uint32_t ) {}

    void post( std::uint32_t v )
    {
        published = v;
        owner()->update_mirror( payloadOf<OwnerT>( v ) );
    }

    void settle()
    {
        pace();
        expectEqual( label, driverMirror(), bridged( published, Direct ) );
        expectEqual( label, owner()->readNonBlocking().value, published );
    }

    void publish()
    {
        pace();
        post( dataVal( 0 ) );
        post( dataVal( 1 ) );
        settle();
        post( dataVal( 2 ) );
        sc_core::wait( sc_core::SC_ZERO_TIME );
        post( dataVal( 3 ) );
        settle();
        post( dataVal( 4 ) );
        sc_core::wait( 1, sc_core::SC_NS );
        post( dataVal( 5 ) );
        settle();
        post( dataVal( 5 ) & PAYLOAD_MASK );
        settle();
        post( dataVal( 6 ) );
        settle();
        post( dataVal( 7 ) );
        sc_core::wait( sc_core::SC_ZERO_TIME );
        post( dataVal( 6 ) );
        settle();
        post( dataVal( 8 ) );
        post( dataVal( 8 ) & PAYLOAD_MASK );
        sc_core::wait( sc_core::SC_ZERO_TIME );
        post( dataVal( 9 ) );
        settle();
        stray( dataVal( 10 ) );
        post( dataVal( 11 ) );
        settle();
        post( dataVal( 12 ) );
        stray( dataVal( 13 ) );
        settle();
        expectEqual( label, ownerOverwrites, 0 );
    }

    // Every change of the owner's mirror must be the owner's own publication.
    void ownerWatch()
    {
        while (true) {
            owner()->wait_mirror();
            if (owner()->readNonBlocking().value != published) ++ownerOverwrites;
        }
    }
};

// connections shape: parent driver on upChan, child owner behind the bridge.
template <class UpT, class DownT, bool Direct>
struct externalRegPublishConsumerHarness : externalRegMirrorPublisher<DownT, Direct>
{
    external_reg_channel<UpT> upChan;
    external_reg_in<DownT> childPort;
    external_reg_port_thunker<UpT, DownT, Direct> thunker;

    externalRegPublishConsumerHarness( sc_core::sc_module_name n, const char* label_ )
      : externalRegMirrorPublisher<DownT, Direct>( n, label_ ),
        upChan( "upChan", "tb" ), childPort( "childPort" ),
        thunker( "thunker", upChan, childPort, "tb" ) {}

    external_reg_in_if<DownT>* owner() override { return childPort.operator->(); }
    std::uint32_t driverMirror() override { return upChan.readNonBlocking().value; }
    void stray( std::uint32_t v ) override { upChan.update_mirror( payloadOf<UpT>( v ) ); }
};

// connectionMap shape: as above through an unbound parent in port.
template <class UpT, class DownT, bool Direct>
struct externalRegPublishUpPortConsumerHarness : externalRegMirrorPublisher<DownT, Direct>
{
    external_reg_channel<UpT> upChan;
    external_reg_in<UpT> upPort;
    external_reg_in<DownT> childPort;
    external_reg_port_thunker<UpT, DownT, Direct> thunker;

    externalRegPublishUpPortConsumerHarness( sc_core::sc_module_name n, const char* label_ )
      : externalRegMirrorPublisher<DownT, Direct>( n, label_ ),
        upChan( "upChan", "tb" ), upPort( "upPort" ), childPort( "childPort" ),
        thunker( "thunker", upPort, childPort, "tb" )
    {
        upPort( upChan );
    }

    external_reg_in_if<DownT>* owner() override { return childPort.operator->(); }
    std::uint32_t driverMirror() override { return upChan.readNonBlocking().value; }
    void stray( std::uint32_t v ) override { upChan.update_mirror( payloadOf<UpT>( v ) ); }
};

// producer (out) shape: parent owner on upChan, child driver behind the bridge.
template <class UpT, class DownT, bool Direct>
struct externalRegPublishProducerHarness : externalRegMirrorPublisher<UpT, Direct>
{
    external_reg_channel<UpT> upChan;
    external_reg_out<DownT> childPort;
    external_reg_port_thunker<UpT, DownT, Direct> thunker;

    externalRegPublishProducerHarness( sc_core::sc_module_name n, const char* label_ )
      : externalRegMirrorPublisher<UpT, Direct>( n, label_ ),
        upChan( "upChan", "tb" ), childPort( "childPort" ),
        thunker( "thunker", upChan, childPort, "tb" ) {}

    external_reg_in_if<UpT>* owner() override { return &upChan; }
    std::uint32_t driverMirror() override { return childPort->readNonBlocking().value; }
};

// producer (out) port shape: as above through an unbound parent out port.
template <class UpT, class DownT, bool Direct>
struct externalRegPublishUpPortProducerHarness : externalRegMirrorPublisher<UpT, Direct>
{
    external_reg_channel<UpT> upChan;
    external_reg_out<UpT> upPort;
    external_reg_out<DownT> childPort;
    external_reg_port_thunker<UpT, DownT, Direct> thunker;

    externalRegPublishUpPortProducerHarness( sc_core::sc_module_name n, const char* label_ )
      : externalRegMirrorPublisher<UpT, Direct>( n, label_ ),
        upChan( "upChan", "tb" ), upPort( "upPort" ), childPort( "childPort" ),
        thunker( "thunker", upPort, childPort, "tb" )
    {
        upPort( upChan );
    }

    external_reg_in_if<UpT>* owner() override { return &upChan; }
    std::uint32_t driverMirror() override { return childPort->readNonBlocking().value; }
};

// ===========================================================================
// axi4_stream - the envelope is bridged member by member, one verdict per
// REQUIRED struct parameter (tdata_t, tid_t, tdest_t). tuser_t is an optional
// payload: it carries no verdict and, when present on both sides, always takes
// the packed arm, so the harness expects the packed value for it.
// ===========================================================================
template <class UpTDATA, class UpTID, class UpTDEST, class UpTUSER,
          class DownTDATA, class DownTID, class DownTDEST, class DownTUSER,
          bool DirectTdata, bool DirectTid, bool DirectTdest>
struct axi4StreamConsumerHarness : sc_core::sc_module
{
    using UpInfo = axi4StreamInfoSt<UpTDATA, UpTID, UpTDEST, UpTUSER>;
    using DownInfo = axi4StreamInfoSt<DownTDATA, DownTID, DownTDEST, DownTUSER>;

    axi4_stream_channel<UpTDATA, UpTID, UpTDEST, UpTUSER> upChan;
    axi4_stream_in<DownTDATA, DownTID, DownTDEST, DownTUSER> childPort;
    axi4_stream_port_thunker<UpTDATA, UpTID, UpTDEST,
                             DownTDATA, DownTID, DownTDEST,
                             DirectTdata, DirectTid, DirectTdest,
                             UpTUSER, DownTUSER> thunker;
    const char* label;
    int beats = 0;

    axi4StreamConsumerHarness( sc_core::sc_module_name n, const char* label_ )
      : sc_core::sc_module( n ), upChan( "upChan", "tb" ), childPort( "childPort" ),
        thunker( "thunker", upChan, childPort, "tb" ), label( label_ )
    {
        SC_HAS_PROCESS( axi4StreamConsumerHarness );
        SC_THREAD( drive );
        SC_THREAD( sink );
    }

    void drive()
    {
        for (int i = 0; i < TRANSFERS; ++i) {
            UpInfo info;
            info.tdata.value = dataVal( i );
            info.tid.value = idVal( i );
            info.tdest.value = destVal( i );
            info.tuser.value = userVal( i );
            info.tlast = ( i == TRANSFERS - 1 );
            info.tstrb[0] = Q_TRUE;
            info.tkeep[1] = Q_TRUE;
            upChan.sendInfo( info, std::nullopt );
        }
    }

    void sink()
    {
        for (int i = 0;; ++i) {
            DownInfo info;
            childPort->receiveInfo( info );
            ++beats;
            if (i >= TRANSFERS) continue;
            expectEqual( label, info.tdata.value, bridged( dataVal( i ), DirectTdata ) );
            expectEqual( label, info.tid.value, bridged( idVal( i ), DirectTid ) );
            expectEqual( label, info.tdest.value, bridged( destVal( i ), DirectTdest ) );
            // Optional tuser_t has no verdict: it always crosses packed.
            expectEqual( label, info.tuser.value, bridged( userVal( i ), false ) );
            // tlast and the byte qualifiers carry no verdict and must cross
            // unchanged.
            expectEqual( label, info.tlast ? 1u : 0u, ( i == TRANSFERS - 1 ) ? 1u : 0u );
            expectEqual( label, info.tstrb[0] == Q_TRUE ? 1u : 0u, 1u );
            expectEqual( label, info.tstrb[1] == Q_TRUE ? 1u : 0u, 0u );
            expectEqual( label, info.tkeep[0] == Q_TRUE ? 1u : 0u, 0u );
            expectEqual( label, info.tkeep[1] == Q_TRUE ? 1u : 0u, 1u );
        }
    }
};

template <class UpTDATA, class UpTID, class UpTDEST, class UpTUSER,
          class DownTDATA, class DownTID, class DownTDEST, class DownTUSER,
          bool DirectTdata, bool DirectTid, bool DirectTdest>
struct axi4StreamProducerHarness : sc_core::sc_module
{
    using UpInfo = axi4StreamInfoSt<UpTDATA, UpTID, UpTDEST, UpTUSER>;
    using DownInfo = axi4StreamInfoSt<DownTDATA, DownTID, DownTDEST, DownTUSER>;

    axi4_stream_channel<UpTDATA, UpTID, UpTDEST, UpTUSER> upChan;
    axi4_stream_out<DownTDATA, DownTID, DownTDEST, DownTUSER> childPort;
    axi4_stream_port_thunker<UpTDATA, UpTID, UpTDEST,
                             DownTDATA, DownTID, DownTDEST,
                             DirectTdata, DirectTid, DirectTdest,
                             UpTUSER, DownTUSER> thunker;
    const char* label;
    int beats = 0;

    axi4StreamProducerHarness( sc_core::sc_module_name n, const char* label_ )
      : sc_core::sc_module( n ), upChan( "upChan", "tb" ), childPort( "childPort" ),
        thunker( "thunker", upChan, childPort, "tb" ), label( label_ )
    {
        SC_HAS_PROCESS( axi4StreamProducerHarness );
        SC_THREAD( drive );
        SC_THREAD( sink );
    }

    void drive()
    {
        for (int i = 0; i < TRANSFERS; ++i) {
            DownInfo info;
            info.tdata.value = dataVal( i );
            info.tid.value = idVal( i );
            info.tdest.value = destVal( i );
            info.tuser.value = userVal( i );
            info.tlast = ( i == TRANSFERS - 1 );
            info.tstrb[0] = Q_TRUE;
            info.tkeep[1] = Q_TRUE;
            childPort->sendInfo( info, std::nullopt );
        }
    }

    void sink()
    {
        for (int i = 0;; ++i) {
            UpInfo info;
            upChan.receiveInfo( info );
            ++beats;
            if (i >= TRANSFERS) continue;
            expectEqual( label, info.tdata.value, bridged( dataVal( i ), DirectTdata ) );
            expectEqual( label, info.tid.value, bridged( idVal( i ), DirectTid ) );
            expectEqual( label, info.tdest.value, bridged( destVal( i ), DirectTdest ) );
            // Optional tuser_t has no verdict: it always crosses packed.
            expectEqual( label, info.tuser.value, bridged( userVal( i ), false ) );
            expectEqual( label, info.tlast ? 1u : 0u, ( i == TRANSFERS - 1 ) ? 1u : 0u );
            expectEqual( label, info.tstrb[0] == Q_TRUE ? 1u : 0u, 1u );
            expectEqual( label, info.tkeep[1] == Q_TRUE ? 1u : 0u, 1u );
        }
    }
};

// ===========================================================================
// axi_read / axi_write with matching optional user types and a non-default id
// width
// ===========================================================================
// axi_thunker_runtime.cpp covers the rest of these protocols. Here a user type
// shared by both sides takes copyPayload's identity arm and lets the data
// envelopes share a burst buffer, and IDW = 6 shows UpIDW/DownIDW are in use.
// The required payloads cross at a direct verdict, so they arrive whole.
static constexpr unsigned AXI_IDW = 6;
static std::uint32_t axiIdVal( int i ) { return (std::uint32_t)( 0x21 + i ); }

struct axiReadConsumerHarness : sc_core::sc_module
{
    using UpAddr = axiReadAddressSt<maskASt, maskASt, _axiIdT, AXI_IDW>;
    using DownAddr = axiReadAddressSt<maskBSt, maskASt, _axiIdT, AXI_IDW>;
    using UpResp = axiReadRespSt<maskASt, maskASt, _axiIdT, AXI_IDW>;
    using DownResp = axiReadRespSt<maskBSt, maskASt, _axiIdT, AXI_IDW>;

    axi_read_channel<maskASt, maskASt, maskASt, maskASt, _axiIdT, AXI_IDW> upChan;
    axi_read_in<maskBSt, maskBSt, maskASt, maskASt, _axiIdT, AXI_IDW> childPort;
    axi_read_port_thunker<maskASt, maskASt, maskBSt, maskBSt, true, true,
                          maskASt, maskASt, _axiIdT, AXI_IDW,
                          maskASt, maskASt, _axiIdT, AXI_IDW> thunker;
    const char* label = "axi_read optional same types";
    int beats = 0;

    axiReadConsumerHarness( sc_core::sc_module_name n )
      : sc_core::sc_module( n ), upChan( "upChan", "tb" ), childPort( "childPort" ),
        thunker( "thunker", upChan, childPort, "tb" )
    {
        SC_HAS_PROCESS( axiReadConsumerHarness );
        SC_THREAD( drive );
        SC_THREAD( sink );
    }

    void drive()
    {
        for (int i = 0; i < TRANSFERS; ++i) {
            UpAddr addr;
            addr.arid = (_axiIdT)axiIdVal( i );
            addr.araddr.value = addrVal( i );
            addr.arlen = 0;
            addr.arsize = 2;
            addr.arburst = AXIBURST_INCR;
            addr.user.value = userVal( i );
            upChan.sendAddr( addr, std::nullopt );
            UpResp resp;
            upChan.receiveData( resp );
            ++beats;
            expectEqual( label, resp.rid, axiIdVal( i ) );
            expectEqual( label, resp.rdata.value, dataVal( i ) );
            expectEqual( label, resp.rresp, AXIRESP_EXOKAY );
            expectEqual( label, resp.rlast ? 1u : 0u, 1u );
            expectEqual( label, resp.user.value, destVal( i ) );
        }
    }

    void sink()
    {
        for (int i = 0;; ++i) {
            DownAddr addr;
            childPort->receiveAddr( addr );
            if (i < TRANSFERS) {
                expectEqual( label, addr.arid, axiIdVal( i ) );
                expectEqual( label, addr.araddr.value, addrVal( i ) );
                expectEqual( label, addr.arburst, AXIBURST_INCR );
                expectEqual( label, addr.user.value, userVal( i ) );
            }
            DownResp resp;
            resp.rid = addr.arid;
            resp.rdata.value = dataVal( i );
            resp.rresp = AXIRESP_EXOKAY;
            resp.rlast = true;
            resp.user.value = destVal( i );
            childPort->sendData( resp );
        }
    }
};

struct axiWriteConsumerHarness : sc_core::sc_module
{
    using UpAddr = axiWriteAddressSt<maskASt, maskASt, _axiIdT, AXI_IDW>;
    using DownAddr = axiWriteAddressSt<maskBSt, maskASt, _axiIdT, AXI_IDW>;
    using UpData = axiWriteDataSt<maskASt, maskASt, maskASt, _axiIdT, AXI_IDW>;
    using DownData = axiWriteDataSt<maskBSt, maskBSt, maskASt, _axiIdT, AXI_IDW>;
    using UpResp = axiWriteRespSt<maskASt, _axiIdT, AXI_IDW>;
    using DownResp = axiWriteRespSt<maskASt, _axiIdT, AXI_IDW>;

    axi_write_channel<maskASt, maskASt, maskASt, maskASt, maskASt, maskASt, _axiIdT, AXI_IDW> upChan;
    axi_write_in<maskBSt, maskBSt, maskBSt, maskASt, maskASt, maskASt, _axiIdT, AXI_IDW> childPort;
    axi_write_port_thunker<maskASt, maskASt, maskASt, maskBSt, maskBSt, maskBSt,
                           true, true, true,
                           maskASt, maskASt, maskASt, _axiIdT, AXI_IDW,
                           maskASt, maskASt, maskASt, _axiIdT, AXI_IDW> thunker;
    const char* label = "axi_write optional same types";
    int beats = 0;

    axiWriteConsumerHarness( sc_core::sc_module_name n )
      : sc_core::sc_module( n ), upChan( "upChan", "tb" ), childPort( "childPort" ),
        thunker( "thunker", upChan, childPort, "tb" )
    {
        SC_HAS_PROCESS( axiWriteConsumerHarness );
        SC_THREAD( drive );
        SC_THREAD( sink );
    }

    void drive()
    {
        for (int i = 0; i < TRANSFERS; ++i) {
            UpAddr addr;
            addr.awid = (_axiIdT)axiIdVal( i );
            addr.awaddr.value = addrVal( i );
            addr.awlen = 0;
            addr.awsize = 2;
            addr.awburst = AXIBURST_INCR;
            addr.user.value = userVal( i );
            upChan.sendAddr( addr, std::nullopt );
            UpData data;
            data.wid = (_axiIdT)axiIdVal( i );
            data.wdata.value = dataVal( i );
            data.wstrb.value = idVal( i );
            data.wlast = true;
            data.user.value = destVal( i );
            upChan.sendData( data );
            UpResp resp;
            upChan.receiveResp( resp );
            ++beats;
            expectEqual( label, resp.bid, axiIdVal( i ) );
            expectEqual( label, resp.bresp, AXIRESP_EXOKAY );
            expectEqual( label, resp.user.value, userVal( i ) ^ 0x00FF0000u );
        }
    }

    void sink()
    {
        for (int i = 0;; ++i) {
            DownAddr addr;
            childPort->receiveAddr( addr );
            DownData data;
            childPort->receiveData( data );
            if (i < TRANSFERS) {
                expectEqual( label, addr.awid, axiIdVal( i ) );
                expectEqual( label, addr.awaddr.value, addrVal( i ) );
                expectEqual( label, addr.user.value, userVal( i ) );
                expectEqual( label, data.wid, axiIdVal( i ) );
                expectEqual( label, data.wdata.value, dataVal( i ) );
                expectEqual( label, data.wstrb.value, idVal( i ) );
                expectEqual( label, data.wlast ? 1u : 0u, 1u );
                expectEqual( label, data.user.value, destVal( i ) );
            }
            DownResp resp;
            resp.bid = addr.awid;
            resp.bresp = AXIRESP_EXOKAY;
            resp.user.value = userVal( i ) ^ 0x00FF0000u;
            childPort->sendResp( resp );
        }
    }
};

// ===========================================================================
// Explicit instantiation of every new template, at both verdict settings and,
// for the two multi-payload protocols, at complementary verdict subsets.
// ===========================================================================
template class raw_port_thunker<maskASt, maskBSt, false>;
template class raw_port_thunker<maskASt, maskBSt, true>;
template class status_port_thunker<maskASt, maskBSt, false>;
template class status_port_thunker<maskASt, maskBSt, true>;
template class pop_ack_port_thunker<maskASt, maskBSt, false>;
template class pop_ack_port_thunker<maskASt, maskBSt, true>;
template class external_reg_port_thunker<maskASt, maskBSt, false>;
template class external_reg_port_thunker<maskASt, maskBSt, true>;
template class memory_port_thunker<maskASt, maskASt, maskBSt, maskBSt, false, false>;
template class memory_port_thunker<maskASt, maskASt, maskBSt, maskBSt, true, true>;
template class memory_port_thunker<maskASt, maskASt, maskBSt, maskBSt, true, false>;
template class memory_port_thunker<maskASt, maskASt, maskBSt, maskBSt, false, true>;
template class apb_port_thunker<maskASt, unfilledASt, maskBSt, unfilledBSt, false, false>;
template class axi4_stream_port_thunker<maskASt, maskASt, maskASt,
                                        maskBSt, maskBSt, maskBSt,
                                        true, false, true, maskASt, maskBSt>;
template class axi4_stream_port_thunker<maskASt, maskASt, maskASt,
                                        maskBSt, maskBSt, maskBSt,
                                        false, true, false, maskASt, maskBSt>;
// The generator omits an absent optional payload: both tuser_t default to the
// std::monostate sentinel and the tuser copy is compiled out.
template class axi4_stream_port_thunker<maskASt, maskASt, maskASt,
                                        maskBSt, maskBSt, maskBSt,
                                        true, true, true>;

int sc_main( int, char*[] )
{
    // -- consumer-child shape: thunkIn() ------------------------------------
    rawConsumerHarness<maskASt, maskBSt, false> rawC0( "rawC0", "raw in packed" );
    rawConsumerHarness<maskASt, maskBSt, true> rawC1( "rawC1", "raw in direct" );
    statusConsumerHarness<maskASt, maskBSt, false> statusC0( "statusC0", "status in packed" );
    statusConsumerHarness<maskASt, maskBSt, true> statusC1( "statusC1", "status in direct" );
    popAckConsumerHarness<maskASt, maskBSt, false> popC0( "popC0", "pop_ack in packed" );
    popAckConsumerHarness<maskASt, maskBSt, true> popC1( "popC1", "pop_ack in direct" );
    externalRegConsumerHarness<maskASt, maskBSt, false> extC0( "extC0", "external_reg in packed" );
    externalRegConsumerHarness<maskASt, maskBSt, true> extC1( "extC1", "external_reg in direct" );

    // memory: both verdicts, then each alone, so a flag driving the wrong
    // payload slot fails.
    memoryConsumerHarness<maskASt, maskASt, maskBSt, maskBSt, false, false>
        memC0( "memC0", "memory in packed" );
    memoryConsumerHarness<maskASt, maskASt, maskBSt, maskBSt, true, true>
        memC1( "memC1", "memory in direct" );
    memoryConsumerHarness<maskASt, maskASt, maskBSt, maskBSt, true, false>
        memC2( "memC2", "memory in addr-only direct" );
    memoryConsumerHarness<maskASt, maskASt, maskBSt, maskBSt, false, true>
        memC3( "memC3", "memory in data-only direct" );

    axi4StreamConsumerHarness<maskASt, maskASt, maskASt, maskASt,
                              maskBSt, maskBSt, maskBSt, maskBSt,
                              true, false, true> streamC0( "streamC0", "axi4_stream in tdata/tdest direct" );
    axi4StreamConsumerHarness<maskASt, maskASt, maskASt, maskASt,
                              maskBSt, maskBSt, maskBSt, maskBSt,
                              false, true, false> streamC1( "streamC1", "axi4_stream in tid direct" );

    // -- producer-child shape: thunkOut() -----------------------------------
    rawProducerHarness<maskASt, maskBSt, false> rawP0( "rawP0", "raw out packed" );
    rawProducerHarness<maskASt, maskBSt, true> rawP1( "rawP1", "raw out direct" );
    statusProducerHarness<maskASt, maskBSt, false> statusP0( "statusP0", "status out packed" );
    statusProducerHarness<maskASt, maskBSt, true> statusP1( "statusP1", "status out direct" );
    popAckProducerHarness<maskASt, maskBSt, false> popP0( "popP0", "pop_ack out packed" );
    popAckProducerHarness<maskASt, maskBSt, true> popP1( "popP1", "pop_ack out direct" );
    externalRegProducerHarness<maskASt, maskBSt, false> extP0( "extP0", "external_reg out packed" );
    externalRegProducerHarness<maskASt, maskBSt, true> extP1( "extP1", "external_reg out direct" );
    memoryProducerHarness<maskASt, maskASt, maskBSt, maskBSt, true, false>
        memP0( "memP0", "memory out addr-only direct" );
    memoryProducerHarness<maskASt, maskASt, maskBSt, maskBSt, false, true>
        memP1( "memP1", "memory out data-only direct" );
    axi4StreamProducerHarness<maskASt, maskASt, maskASt, maskASt,
                              maskBSt, maskBSt, maskBSt, maskBSt,
                              true, false, true> streamP0( "streamP0", "axi4_stream out tdata/tdest direct" );
    axi4StreamProducerHarness<maskASt, maskASt, maskASt, maskASt,
                              maskBSt, maskBSt, maskBSt, maskBSt,
                              false, true, false> streamP1( "streamP1", "axi4_stream out tid direct" );

    // -- notification and leg semantics, both shapes, both verdicts ---------
    statusCommandConsumerHarness<maskASt, maskBSt, false> statusCmdC0( "statusCmdC0", "status cmd in packed" );
    statusCommandConsumerHarness<maskASt, maskBSt, true> statusCmdC1( "statusCmdC1", "status cmd in direct" );
    statusCommandProducerHarness<maskASt, maskBSt, false> statusCmdP0( "statusCmdP0", "status cmd out packed" );
    statusCommandProducerHarness<maskASt, maskBSt, true> statusCmdP1( "statusCmdP1", "status cmd out direct" );
    statusInitialConsumerHarness<maskASt, maskBSt, false> statusInitC0( "statusInitC0", "status initial in packed" );
    statusInitialConsumerHarness<maskASt, maskBSt, true> statusInitC1( "statusInitC1", "status initial in direct" );
    statusInitialProducerHarness<maskASt, maskBSt, false> statusInitP0( "statusInitP0", "status initial out packed" );
    statusInitialProducerHarness<maskASt, maskBSt, true> statusInitP1( "statusInitP1", "status initial out direct" );
    statusInitialUpPortConsumerHarness<maskASt, maskBSt, false> statusInitUpC0( "statusInitUpC0", "status initial in up-port packed" );
    statusInitialUpPortConsumerHarness<maskASt, maskBSt, true> statusInitUpC1( "statusInitUpC1", "status initial in up-port direct" );
    statusInitialUpPortProducerHarness<maskASt, maskBSt, false> statusInitUpP0( "statusInitUpP0", "status initial out up-port packed" );
    statusInitialUpPortProducerHarness<maskASt, maskBSt, true> statusInitUpP1( "statusInitUpP1", "status initial out up-port direct" );
    statusChainConsumerHarness<true> statusChainC0( "statusChainC0", "status chain in inner-first" );
    statusChainConsumerHarness<false> statusChainC1( "statusChainC1", "status chain in outer-first" );
    statusChainProducerHarness<true> statusChainP0( "statusChainP0", "status chain out inner-first" );
    statusChainProducerHarness<false> statusChainP1( "statusChainP1", "status chain out outer-first" );
    statusTimeZeroProducerHarness<maskASt, maskBSt, false, true> statusT0W0( "statusT0W0" );
    statusTimeZeroProducerHarness<maskASt, maskBSt, false, false> statusT0A0( "statusT0A0" );
    statusTimeZeroProducerHarness<maskASt, maskBSt, true, true> statusT0W1( "statusT0W1" );
    statusTimeZeroProducerHarness<maskASt, maskBSt, true, false> statusT0A1( "statusT0A1" );
    externalRegMirrorConsumerHarness<maskASt, maskBSt, false> extMirC0( "extMirC0", "external_reg legs in packed" );
    externalRegMirrorConsumerHarness<maskASt, maskBSt, true> extMirC1( "extMirC1", "external_reg legs in direct" );
    externalRegMirrorProducerHarness<maskASt, maskBSt, false> extMirP0( "extMirP0", "external_reg legs out packed" );
    externalRegMirrorProducerHarness<maskASt, maskBSt, true> extMirP1( "extMirP1", "external_reg legs out direct" );

    // -- external_reg mirror: owner publications converge on the driver ------
    externalRegPublishConsumerHarness<maskASt, maskBSt, false> extPubC0( "extPubC0", "external_reg publish in packed" );
    externalRegPublishConsumerHarness<maskASt, maskBSt, true> extPubC1( "extPubC1", "external_reg publish in direct" );
    externalRegPublishUpPortConsumerHarness<maskASt, maskBSt, false> extPubUpC0( "extPubUpC0", "external_reg publish in up-port packed" );
    externalRegPublishUpPortConsumerHarness<maskASt, maskBSt, true> extPubUpC1( "extPubUpC1", "external_reg publish in up-port direct" );
    externalRegPublishProducerHarness<maskASt, maskBSt, false> extPubP0( "extPubP0", "external_reg publish out packed" );
    externalRegPublishProducerHarness<maskASt, maskBSt, true> extPubP1( "extPubP1", "external_reg publish out direct" );
    externalRegPublishUpPortProducerHarness<maskASt, maskBSt, false> extPubUpP0( "extPubUpP0", "external_reg publish out up-port packed" );
    externalRegPublishUpPortProducerHarness<maskASt, maskBSt, true> extPubUpP1( "extPubUpP1", "external_reg publish out up-port direct" );

    // -- read data never filled by reqReceive() must not be converted --------
    // Packed data verdict only: the direct arm bit_casts and packs nothing.
    memoryConsumerHarness<maskASt, unfilledASt, maskBSt, unfilledBSt, false, false>
        memUnfilledC( "memUnfilledC", "memory in unfilled read data" );
    memoryProducerHarness<maskASt, unfilledASt, maskBSt, unfilledBSt, false, false>
        memUnfilledP( "memUnfilledP", "memory out unfilled read data" );
    apbConsumerHarness<maskASt, unfilledASt, maskBSt, unfilledBSt, false, false>
        apbUnfilledC( "apbUnfilledC", "apb in unfilled read data" );
    apbProducerHarness<maskASt, unfilledASt, maskBSt, unfilledBSt, false, false>
        apbUnfilledP( "apbUnfilledP", "apb out unfilled read data" );

    // -- axi_read / axi_write: matching optional types, id width 6 ---------
    axiReadConsumerHarness axiRdSame( "axiRdSame" );
    axiWriteConsumerHarness axiWrSame( "axiWrSame" );

    // -- port shapes: the lazily resolved up side, both directions ----------
    rawUpPortConsumerHarness<maskASt, maskBSt, false> rawUpC( "rawUpC", "raw in up-port packed" );
    rawUpPortProducerHarness<maskASt, maskBSt, true> rawUpP( "rawUpP", "raw out up-port direct" );

    sc_core::sc_start();

    // Beat accounting. A bridge that duplicated a transaction would satisfy
    // every value check above and fail here.
    expectEqual( "rawC0 beats", rawC0.beats, TRANSFERS );
    expectEqual( "rawC1 beats", rawC1.beats, TRANSFERS );
    expectEqual( "statusC0 beats", statusC0.beats, TRANSFERS );
    expectEqual( "statusC1 beats", statusC1.beats, TRANSFERS );
    expectEqual( "popC0 beats", popC0.beats, TRANSFERS );
    expectEqual( "popC1 beats", popC1.beats, TRANSFERS );
    expectEqual( "extC0 beats", extC0.beats, 2 * TRANSFERS );
    expectEqual( "extC1 beats", extC1.beats, 2 * TRANSFERS );
    expectEqual( "memC0 beats", memC0.beats, 2 * TRANSFERS );
    expectEqual( "memC1 beats", memC1.beats, 2 * TRANSFERS );
    expectEqual( "memC2 beats", memC2.beats, 2 * TRANSFERS );
    expectEqual( "memC3 beats", memC3.beats, 2 * TRANSFERS );
    expectEqual( "streamC0 beats", streamC0.beats, TRANSFERS );
    expectEqual( "streamC1 beats", streamC1.beats, TRANSFERS );
    expectEqual( "rawP0 beats", rawP0.beats, TRANSFERS );
    expectEqual( "rawP1 beats", rawP1.beats, TRANSFERS );
    expectEqual( "statusP0 beats", statusP0.beats, TRANSFERS );
    expectEqual( "statusP1 beats", statusP1.beats, TRANSFERS );
    expectEqual( "popP0 beats", popP0.beats, TRANSFERS );
    expectEqual( "popP1 beats", popP1.beats, TRANSFERS );
    expectEqual( "extP0 beats", extP0.beats, 2 * TRANSFERS );
    expectEqual( "extP1 beats", extP1.beats, 2 * TRANSFERS );
    expectEqual( "memP0 beats", memP0.beats, 2 * TRANSFERS );
    expectEqual( "memP1 beats", memP1.beats, 2 * TRANSFERS );
    expectEqual( "streamP0 beats", streamP0.beats, TRANSFERS );
    expectEqual( "streamP1 beats", streamP1.beats, TRANSFERS );
    expectEqual( "rawUpC beats", rawUpC.beats, TRANSFERS );
    expectEqual( "rawUpP beats", rawUpP.beats, TRANSFERS );
    expectEqual( "statusCmdC0 reference", statusCmdC0.refBeats, STATUS_SEQUENCE_NOTIFICATIONS );
    expectEqual( "statusCmdC0 beats", statusCmdC0.beats, STATUS_SEQUENCE_NOTIFICATIONS );
    expectEqual( "statusCmdC1 reference", statusCmdC1.refBeats, STATUS_SEQUENCE_NOTIFICATIONS );
    expectEqual( "statusCmdC1 beats", statusCmdC1.beats, STATUS_SEQUENCE_NOTIFICATIONS );
    expectEqual( "statusCmdP0 reference", statusCmdP0.refBeats, STATUS_SEQUENCE_NOTIFICATIONS );
    expectEqual( "statusCmdP0 beats", statusCmdP0.beats, STATUS_SEQUENCE_NOTIFICATIONS );
    expectEqual( "statusCmdP1 reference", statusCmdP1.refBeats, STATUS_SEQUENCE_NOTIFICATIONS );
    expectEqual( "statusCmdP1 beats", statusCmdP1.beats, STATUS_SEQUENCE_NOTIFICATIONS );
    expectEqual( "statusInitC0 beats", statusInitC0.beats, 0 );
    expectEqual( "statusInitC1 beats", statusInitC1.beats, 0 );
    expectEqual( "statusInitP0 beats", statusInitP0.beats, 0 );
    expectEqual( "statusInitP1 beats", statusInitP1.beats, 0 );
    expectEqual( "statusInitUpC0 beats", statusInitUpC0.beats, 0 );
    expectEqual( "statusInitUpC1 beats", statusInitUpC1.beats, 0 );
    expectEqual( "statusInitUpP0 beats", statusInitUpP0.beats, 0 );
    expectEqual( "statusInitUpP1 beats", statusInitUpP1.beats, 0 );
    expectEqual( "statusChainC0 beats", statusChainC0.beats, 0 );
    expectEqual( "statusChainC1 beats", statusChainC1.beats, 0 );
    expectEqual( "statusChainP0 beats", statusChainP0.beats, 0 );
    expectEqual( "statusChainP1 beats", statusChainP1.beats, 0 );
    // One notification, carrying the time-zero write, in either process order.
    expectEqual( "statusT0W0 value", statusT0W0.upChan.readNonBlocking().value, STATUS_TIME_ZERO );
    expectEqual( "statusT0W0 beats", statusT0W0.beats, 1 );
    expectEqual( "statusT0A0 value", statusT0A0.upChan.readNonBlocking().value, STATUS_TIME_ZERO );
    expectEqual( "statusT0A0 beats", statusT0A0.beats, 1 );
    expectEqual( "statusT0W1 value", statusT0W1.upChan.readNonBlocking().value, STATUS_TIME_ZERO );
    expectEqual( "statusT0W1 beats", statusT0W1.beats, 1 );
    expectEqual( "statusT0A1 value", statusT0A1.upChan.readNonBlocking().value, STATUS_TIME_ZERO );
    expectEqual( "statusT0A1 beats", statusT0A1.beats, 1 );
    expectEqual( "extMirC0 commands", extMirC0.cmdBeats, 3 );
    expectEqual( "extMirC1 commands", extMirC1.cmdBeats, 3 );
    expectEqual( "extMirP0 commands", extMirP0.cmdBeats, 3 );
    expectEqual( "extMirP1 commands", extMirP1.cmdBeats, 3 );
    expectEqual( "memUnfilledC beats", memUnfilledC.beats, 2 * TRANSFERS );
    expectEqual( "memUnfilledP beats", memUnfilledP.beats, 2 * TRANSFERS );
    expectEqual( "apbUnfilledC beats", apbUnfilledC.beats, 2 * TRANSFERS );
    expectEqual( "apbUnfilledP beats", apbUnfilledP.beats, 2 * TRANSFERS );
    expectEqual( "axiRdSame beats", axiRdSame.beats, TRANSFERS );
    expectEqual( "axiWrSame beats", axiWrSame.beats, TRANSFERS );
    expectEqual( "unfilled read data converted", g_unfilledPacks, 0 );

    std::printf( "checks:%d failures:%d\n", g_checks, g_failures );
    if (g_checks == 0) {
        std::printf( "FAIL no checks executed\n" );
        return 1;
    }
    return g_failures == 0 ? 0 : 1;
}
