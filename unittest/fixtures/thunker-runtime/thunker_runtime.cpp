// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE
//
// Runtime acceptance harness for the six protocol port thunkers that carry a
// payload and had no adapter until now: axi4_stream, external_reg, memory,
// pop_ack, raw and status. Driven by unittest/test_thunker_runtime.py.
//
// Every one of the six templates is explicitly instantiated - as
// proto/model/test/test_port_thunker.cpp does for the other seven - AND run
// under the SystemC kernel, with the value observed on the far side asserted
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

#include "axi4_stream_port_thunker.h"
#include "external_reg_port_thunker.h"
#include "memory_port_thunker.h"
#include "pop_ack_port_thunker.h"
#include "raw_port_thunker.h"
#include "status_port_thunker.h"

#include <cstdint>
#include <cstdio>
#include <string>
#include <systemc.h>

static constexpr std::uint32_t PAYLOAD_MASK = 0xFFFFu;

#define A2C_TEST_PAYLOAD( NAME )                                                \
    struct NAME                                                                 \
    {                                                                           \
        using _packedSt = std::uint32_t;                                        \
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

A2C_TEST_PAYLOAD( maskASt );
A2C_TEST_PAYLOAD( maskBSt );

static_assert( sizeof( maskASt ) == sizeof( maskBSt ) );
static_assert( std::is_trivially_copyable_v<maskASt> && std::is_trivially_copyable_v<maskBSt> );

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

// raw_channel drives both handshake directions off one event and write() waits
// on the event it notifies, so a producer that writes again immediately can
// overwrite a value the consumer has not taken. That is a raw_channel property,
// not an adapter one - it reproduces with a hand-written forwarding thread and
// no thunker whenever the forwarder's process is created before the producer's.
// The raw harnesses therefore pace their producer instead of measuring it.
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
            pace();
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
            pace();
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
            pace();
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
            pace();
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
// memory - both the write-data leg and the read-response leg, which is why
// data_t gates four call sites while addr_t gates two.
// ===========================================================================
template <class UpA, class UpD, class DownA, class DownD, bool DirectAddr, bool DirectData>
struct memoryConsumerHarness : sc_core::sc_module
{
    memory_channel<UpA, UpD> upChan;
    memory_in<DownA, DownD> childPort;
    memory_port_thunker<UpA, UpD, DownA, DownD, DirectAddr, DirectData> thunker;
    const char* label;
    int beats = 0;

    memoryConsumerHarness( sc_core::sc_module_name n, const char* label_ )
      : sc_core::sc_module( n ), upChan( "upChan", "tb" ), childPort( "childPort" ),
        thunker( "thunker", upChan, childPort, "tb" ), label( label_ )
    {
        SC_HAS_PROCESS( memoryConsumerHarness );
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

template <class UpA, class UpD, class DownA, class DownD, bool DirectAddr, bool DirectData>
struct memoryProducerHarness : sc_core::sc_module
{
    memory_channel<UpA, UpD> upChan;
    memory_out<DownA, DownD> childPort;
    memory_port_thunker<UpA, UpD, DownA, DownD, DirectAddr, DirectData> thunker;
    const char* label;
    int beats = 0;

    memoryProducerHarness( sc_core::sc_module_name n, const char* label_ )
      : sc_core::sc_module( n ), upChan( "upChan", "tb" ), childPort( "childPort" ),
        thunker( "thunker", upChan, childPort, "tb" ), label( label_ )
    {
        SC_HAS_PROCESS( memoryProducerHarness );
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
            upChan.reg_write( v );
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
            childPort->reg_write( v );
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

// ===========================================================================
// axi4_stream - the envelope is bridged member by member, one verdict per
// struct parameter.
// ===========================================================================
template <class UpTDATA, class UpTID, class UpTDEST, class UpTUSER,
          class DownTDATA, class DownTID, class DownTDEST, class DownTUSER,
          bool DirectTdata, bool DirectTid, bool DirectTdest, bool DirectTuser>
struct axi4StreamConsumerHarness : sc_core::sc_module
{
    using UpInfo = axi4StreamInfoSt<UpTDATA, UpTID, UpTDEST, UpTUSER>;
    using DownInfo = axi4StreamInfoSt<DownTDATA, DownTID, DownTDEST, DownTUSER>;

    axi4_stream_channel<UpTDATA, UpTID, UpTDEST, UpTUSER> upChan;
    axi4_stream_in<DownTDATA, DownTID, DownTDEST, DownTUSER> childPort;
    axi4_stream_port_thunker<UpTDATA, UpTID, UpTDEST, UpTUSER,
                             DownTDATA, DownTID, DownTDEST, DownTUSER,
                             DirectTdata, DirectTid, DirectTdest, DirectTuser> thunker;
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
            expectEqual( label, info.tuser.value, bridged( userVal( i ), DirectTuser ) );
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
          bool DirectTdata, bool DirectTid, bool DirectTdest, bool DirectTuser>
struct axi4StreamProducerHarness : sc_core::sc_module
{
    using UpInfo = axi4StreamInfoSt<UpTDATA, UpTID, UpTDEST, UpTUSER>;
    using DownInfo = axi4StreamInfoSt<DownTDATA, DownTID, DownTDEST, DownTUSER>;

    axi4_stream_channel<UpTDATA, UpTID, UpTDEST, UpTUSER> upChan;
    axi4_stream_out<DownTDATA, DownTID, DownTDEST, DownTUSER> childPort;
    axi4_stream_port_thunker<UpTDATA, UpTID, UpTDEST, UpTUSER,
                             DownTDATA, DownTID, DownTDEST, DownTUSER,
                             DirectTdata, DirectTid, DirectTdest, DirectTuser> thunker;
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
            expectEqual( label, info.tuser.value, bridged( userVal( i ), DirectTuser ) );
            expectEqual( label, info.tlast ? 1u : 0u, ( i == TRANSFERS - 1 ) ? 1u : 0u );
            expectEqual( label, info.tstrb[0] == Q_TRUE ? 1u : 0u, 1u );
            expectEqual( label, info.tkeep[1] == Q_TRUE ? 1u : 0u, 1u );
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
template class axi4_stream_port_thunker<maskASt, maskASt, maskASt, maskASt,
                                        maskBSt, maskBSt, maskBSt, maskBSt,
                                        true, false, true, false>;
template class axi4_stream_port_thunker<maskASt, maskASt, maskASt, maskASt,
                                        maskBSt, maskBSt, maskBSt, maskBSt,
                                        false, true, false, true>;

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
                              true, false, true, false> streamC0( "streamC0", "axi4_stream in tdata/tdest direct" );
    axi4StreamConsumerHarness<maskASt, maskASt, maskASt, maskASt,
                              maskBSt, maskBSt, maskBSt, maskBSt,
                              false, true, false, true> streamC1( "streamC1", "axi4_stream in tid/tuser direct" );

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
                              true, false, true, false> streamP0( "streamP0", "axi4_stream out tdata/tdest direct" );
    axi4StreamProducerHarness<maskASt, maskASt, maskASt, maskASt,
                              maskBSt, maskBSt, maskBSt, maskBSt,
                              false, true, false, true> streamP1( "streamP1", "axi4_stream out tid/tuser direct" );

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

    std::printf( "checks:%d failures:%d\n", g_checks, g_failures );
    if (g_checks == 0) {
        std::printf( "FAIL no checks executed\n" );
        return 1;
    }
    return g_failures == 0 ? 0 : 1;
}
