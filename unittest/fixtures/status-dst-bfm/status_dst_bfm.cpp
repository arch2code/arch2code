// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE
//
// Drives a status_dst_bfm from a model writer and samples its HDL pin the way a
// Verilator --no-timing model does: an SC_METHOD sensitive to the clock and the
// pin that latches the pin on each rising edge it sees. Posedges fall at 5, 15,
// 25 ns and so on. argv[1] picks when the writer writes:
//   twoInOneClock  writes 1 at 17 ns and 2 at 19 ns, inside one clock
//   onEdge         writes 1 from a process woken by the 15 ns posedge
// The probe prints the value latched at each edge and the pin at the end.

#include "systemc.h"
#include "logging.h"
#include "q_assert.h"
#include "status_bfm.h"
#include <cstdint>
#include <format>
#include <iostream>
#include <string>

struct pinSt {
    typedef std::uint32_t _packedSt;
    static constexpr unsigned _bitWidth = 32;
    static const char* getValueType() { return ""; }
    std::uint64_t getStructValue() const { return value; }
    std::string prt( bool = false ) const { return std::format( "pin:0x{:x}", value ); }
    bool operator==( const pinSt& o ) const { return value == o.value; }
    void unpack( const _packedSt& p ) { value = p; }
    std::uint32_t sc_pack() const { return value; }
    void sc_unpack( std::uint32_t v ) { value = v; }
    std::uint32_t value = 0;
};

struct bfmHarness : sc_module
{
    sc_signal<bool> clk;
    sc_signal<bool> rst_n;
    status_channel<pinSt> chan;
    status_hdl_if<std::uint32_t> hdl;
    status_out<pinSt> writer;
    status_dst_bfm<pinSt, std::uint32_t> bfm;
    std::string scenario;
    bool lastClk = false;

    SC_HAS_PROCESS( bfmHarness );
    bfmHarness( sc_module_name n, std::string scenario_ )
      : sc_module( n ), clk( "clk" ), rst_n( "rst_n" ), chan( "chan", "tb" ), writer( "writer" ),
        bfm( "bfm" ), scenario( scenario_ )
    {
        writer( chan );
        bfm.if_p( chan );
        bfm.hdl_if_p( hdl );
        bfm.clk( clk );
        bfm.rst_n( rst_n );
        SC_THREAD( clockGen );
        SC_THREAD( write );
        SC_METHOD( rtlEval );
        sensitive << clk << hdl.data;
    }

    void clockGen()
    {
        rst_n.write( true );
        while (true) {
            wait( 5, SC_NS );
            clk.write( !clk.read() );
        }
    }

    void rtlEval()
    {
        bool risen = clk.read() && !lastClk;
        lastClk = clk.read();
        if (risen) {
            std::cout << std::format( "edge {} sampled=0x{:x}\n", sc_time_stamp().to_string(), hdl.data.read() );
        }
    }

    void write()
    {
        pinSt v;
        if (scenario == "twoInOneClock") {
            wait( 17, SC_NS );
            v.value = 1;
            writer->write( v );
            wait( 2, SC_NS );
            v.value = 2;
            writer->write( v );
        } else if (scenario == "onEdge") {
            wait( 10, SC_NS );
            wait( clk.posedge_event() );
            v.value = 1;
            writer->write( v );
        }
        wait( 42, SC_NS );
        std::cout << std::format( "final pin=0x{:x}\n", hdl.data.read() );
        sc_stop();
    }
};

int sc_main( int argc, char* argv[] )
{
    std::string scenario = argc > 1 ? argv[1] : "";
    if (scenario != "twoInOneClock" && scenario != "onEdge") {
        std::cout << "unknown scenario " << scenario << "\n";
        return 2;
    }
    bfmHarness harness( "harness", scenario );
    sc_start();
    return 0;
}
