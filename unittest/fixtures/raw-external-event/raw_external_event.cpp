// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE
//
// Writers write TRANSFERS values back to back into raw channels and a slower
// reader takes 1 ns over each. argv[1] picks the reader's event:
//   internal  one channel, the channel's own event
//   external  one channel, a shared event passed through setExternalEvent, as
//             an arbitrating reader does
//   shared    channels A and B both on one shared event; the reader takes all
//             of A before any of B, so B's writer stays parked through A's reads
// argv[2] picks whether the writers or the reader are created first, so both
// delta orders of the wake that follows a write are run.
// Each read prints "read <chan> <value>" and each write prints
// "wrote <chan> <value>" when write() returns, in execution order. The run is
// bounded in simulation time, so a writer left waiting shows as writerDone=0
// rather than a hang.

#include "systemc.h"
#include "raw_channel.h"
#include <cstdint>
#include <format>
#include <iostream>
#include <string>

struct wordSt {
    using _packedSt = std::uint32_t;
    static constexpr unsigned _bitWidth = 32;
    static constexpr unsigned _byteWidth = sizeof( _packedSt );
    void pack( _packedSt& v ) const { v = value; }
    void unpack( const _packedSt& v ) { value = v; }
    static const char* getValueType() { return ""; }
    std::uint64_t getStructValue() const { return value; }
    std::string prt( bool = false ) const { return std::format( "word:0x{:x}", value ); }
    bool operator==( const wordSt& o ) const { return value == o.value; }
    std::uint32_t value = 0;
};

static const int TRANSFERS = 8;

struct rawHarness : sc_module
{
    raw_channel<wordSt> chanA;
    raw_channel<wordSt> chanB;
    raw_out<wordSt> writerA;
    raw_out<wordSt> writerB;
    raw_in<wordSt> readerA;
    raw_in<wordSt> readerB;
    sc_event shared;
    std::string mode;
    int writersDone = 0;
    bool readerDone = false;

    SC_HAS_PROCESS( rawHarness );
    rawHarness( sc_module_name n, std::string mode_, bool writerFirst )
      : sc_module( n ), chanA( "chanA", "tb" ), chanB( "chanB", "tb" ), writerA( "writerA" ),
        writerB( "writerB" ), readerA( "readerA" ), readerB( "readerB" ), shared( "shared" ), mode( mode_ )
    {
        writerA( chanA );
        readerA( chanA );
        writerB( chanB );
        readerB( chanB );
        if (writerFirst) {
            SC_THREAD( writeA );
            SC_THREAD( writeB );
            SC_THREAD( read );
        } else {
            SC_THREAD( read );
            SC_THREAD( writeA );
            SC_THREAD( writeB );
        }
    }

    int writers() const { return mode == "shared" ? 2 : 1; }

    void writeAll( raw_out<wordSt>& writer, const char* chan, std::uint32_t base )
    {
        for (int i = 0; i < TRANSFERS; ++i) {
            wordSt v;
            v.value = base + i;
            writer->write( v, (std::uint64_t)-1 );
            std::cout << std::format( "wrote {} 0x{:x}\n", chan, v.value );
        }
        ++writersDone;
    }

    void writeA() { writeAll( writerA, "A", 0x100 ); }
    void writeB() { if (mode == "shared") writeAll( writerB, "B", 0x200 ); }

    void readAll( raw_in<wordSt>& reader, const char* chan )
    {
        for (int i = 0; i < TRANSFERS; ++i) {
            wordSt v;
            reader->read( v );
            std::cout << std::format( "read {} 0x{:x}\n", chan, v.value );
            wait( 1, SC_NS );
        }
    }

    void read()
    {
        if (mode != "internal") readerA->setExternalEvent( &shared );
        if (mode == "shared") readerB->setExternalEvent( &shared );
        readAll( readerA, "A" );
        if (mode == "shared") readAll( readerB, "B" );
        readerDone = true;
    }
};

int sc_main( int argc, char* argv[] )
{
    std::string mode = argc > 1 ? argv[1] : "";
    std::string order = argc > 2 ? argv[2] : "";
    if ((mode != "internal" && mode != "external" && mode != "shared") ||
        (order != "writerFirst" && order != "readerFirst")) {
        std::cout << "usage: probe internal|external|shared writerFirst|readerFirst\n";
        return 2;
    }
    rawHarness harness( "harness", mode, order == "writerFirst" );
    sc_start( 1, SC_US );
    std::cout << std::format( "writerDone={} readerDone={}\n",
                              (int)(harness.writersDone == harness.writers()), (int)harness.readerDone );
    return 0;
}
