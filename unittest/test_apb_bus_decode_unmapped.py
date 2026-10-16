#!/usr/bin/env python3
"""abpBusDecode routes each address space to its port; an empty one reads 0xBADDC0DE.

abpBusDecode is built with a number of address spaces and the ports of the
blocks that fill them, and a design may leave the top spaces empty, so there can
be fewer ports than spaces. An access to an empty space, past the end of the
port list or a null slot inside it, behaves as the generated RTL decoder does:
a read returns 0xBADDC0DE, a write is dropped and leaves every block
unchanged, and the run carries on. The model also prints a warning naming the
decoder instance and the address. Reading a port past the end of the port list
is undefined behaviour, which shows up as a crash or a hang instead.

The slot mask must cover every space. With 24 spaces a read of slot 16 reaches
the block there instead of aliasing to slot 0, and a read of slot 24 is out of
range. projectCreate rejects a design whose maxAddressSpaces is not a power of
two, so the 24-space scenarios harden the library class against input no
generated design now passes it.

The probe builds the shipped decoder with eight spaces and two ports, or with 24
spaces and ports at slots 0 and 16. Each scenario issues an optional write, then
one read. Each port answers a read with the last value written to it.
"""

import os
import shutil
import subprocess
import sys
import tempfile

from test_watchdog_no_terminator import buildProbe

PROBE_SRC = """
// libstdc++ bounds-checks operator[], so a read past the port list aborts
#define _GLIBCXX_ASSERTIONS 1
#include "systemc.h"
#include "logging.h"
#include "q_assert.h"
#include "apbBusDecode.h"
#include <cstdint>
#include <format>
#include <iostream>
#include <map>
#include <string>
#include <tuple>

struct decodeAddrSt {
    static constexpr unsigned _bitWidth = 32;
    static const char* getValueType() { return ""; }
    std::uint64_t getStructValue() const { return value; }
    std::uint64_t _getAddress() const { return value; }
    std::string prt( bool = false ) const { return std::format( "addr:0x{:x}", value ); }
    bool operator==( const decodeAddrSt& o ) const { return value == o.value; }
    std::uint32_t value = 0;
};

struct decodeDataSt {
    static constexpr unsigned _bitWidth = 32;
    static const char* getValueType() { return ""; }
    std::uint64_t getStructValue() const { return value; }
    void _setData( std::uint32_t v ) { value = v; }
    std::string prt( bool = false ) const { return std::format( "data:0x{:x}", value ); }
    bool operator==( const decodeDataSt& o ) const { return value == o.value; }
    std::uint32_t value = 0;
};

static constexpr std::uint32_t ADDRESS_SHIFT = 8;

using decodePort = sc_port<apb_out_if<decodeAddrSt, decodeDataSt>>;

SC_MODULE( decodeHarness )
{
    apb_channel<decodeAddrSt, decodeDataSt> upChan;
    apb_channel<decodeAddrSt, decodeDataSt> chan0;
    apb_channel<decodeAddrSt, decodeDataSt> chan1;
    sc_port<apb_in_if<decodeAddrSt, decodeDataSt>> in;
    sc_port<apb_out_if<decodeAddrSt, decodeDataSt>> out0;
    sc_port<apb_out_if<decodeAddrSt, decodeDataSt>> out1;
    abpBusDecode<decodeAddrSt, decodeDataSt> decoder;
    std::uint32_t slot;
    std::int32_t writeSlot;

    SC_HAS_PROCESS( decodeHarness );
    // sparse puts out1 at slot 16 of the address spaces instead of slot 1
    decodeHarness( sc_module_name n, std::uint32_t spaces, bool sparse, std::int32_t writeSlot_, std::uint32_t slot_ )
      : sc_module( n ), upChan( "upChan", "tb" ), chan0( "chan0", "tb" ), chan1( "chan1", "tb" ),
        in( "in" ), out0( "out0" ), out1( "out1" ),
        decoder( spaces, ADDRESS_SHIFT, in,
                 sparse ? std::initializer_list<decodePort*>{ &out0, nullptr, nullptr, nullptr, nullptr, nullptr,
                                                              nullptr, nullptr, nullptr, nullptr, nullptr, nullptr,
                                                              nullptr, nullptr, nullptr, nullptr, &out1 }
                        : std::initializer_list<decodePort*>{ &out0, &out1 } ),
        slot( slot_ ), writeSlot( writeSlot_ )
    {
        in( upChan );
        out0( chan0 );
        out1( chan1 );
        SC_THREAD( decode );
        SC_THREAD( drive );
        SC_THREAD( respond0 );
        SC_THREAD( respond1 );
    }

    void decode() { decoder.decodeThread(); }

    void drive()
    {
        decodeAddrSt addr;
        decodeDataSt data;
        if (writeSlot >= 0) {
            addr.value = writeSlot << ADDRESS_SHIFT;
            data.value = 0xdead;
            upChan.request( true, addr, data );
        }
        addr.value = slot << ADDRESS_SHIFT;
        data.value = 0xffff;
        upChan.request( false, addr, data );
        std::cout << std::format( "readData=0x{:x}\\n", data.value );
        sc_stop();
    }

    void respond( apb_channel<decodeAddrSt, decodeDataSt>& chan, std::uint32_t value )
    {
        while (true) {
            bool isWrite = false;
            decodeAddrSt addr;
            decodeDataSt data;
            chan.reqReceive( isWrite, addr, data );
            if (isWrite) {
                value = data.value;
            } else {
                decodeDataSt resp;
                resp.value = value;
                chan.complete( resp );
            }
        }
    }

    void respond0() { respond( chan0, 0x100 ); }
    void respond1() { respond( chan1, 0x101 ); }
};

int sc_main( int argc, char* argv[] )
{
    // scenario -> address spaces, sparse port list, slot written (-1 for none), slot read
    const std::map<std::string, std::tuple<std::uint32_t, bool, std::int32_t, std::uint32_t>> scenarios = {
        { "mapped", { 8, false, -1, 1 } },
        { "pastLastPort", { 8, false, -1, 7 } },
        { "writePastLastPort", { 8, false, 7, 1 } },
        { "nullSlot", { 24, true, -1, 5 } },
        { "writeNullSlot", { 24, true, 5, 16 } },
        { "slotPastPowerOfTwo", { 24, true, -1, 16 } },
        { "pastLastSpace", { 24, true, -1, 24 } },
    };
    auto [spaces, sparse, writeSlot, slot] = scenarios.at( argv[1] );
    decodeHarness harness( "harness", spaces, sparse, writeSlot, slot );
    sc_start();
    int code = errorCode::getExitCode();
    std::cout << "exitCode=" << code << "\\n";
    return code > 0 ? code : 0;
}
"""

# scenario -> (process exit status, output that must be present, output that must be absent)
SCENARIOS = {
    'mapped': (0, ('readData=0x101',), ('unmapped',)),
    'pastLastPort': (0, ('harness: firmware read of unmapped address 0x700 returns 0xBADDC0DE', 'readData=0xbaddc0de'), ()),
    'writePastLastPort': (0, ('harness: firmware write to unmapped address 0x700 dropped', 'readData=0x101'),
                          ('readData=0xdead',)),
    'nullSlot': (0, ('harness: firmware read of unmapped address 0x500 returns 0xBADDC0DE', 'readData=0xbaddc0de'), ()),
    'writeNullSlot': (0, ('harness: firmware write to unmapped address 0x500 dropped', 'readData=0x101'),
                      ('readData=0xdead',)),
    'slotPastPowerOfTwo': (0, ('readData=0x101',), ('readData=0x100', 'unmapped')),
    'pastLastSpace': (1, ('out of range, block 18', 'exitCode=1'), ('readData=',)),
}

FAILURES = []


def check(condition, message):
    print(f"  {'PASS' if condition else 'FAIL'}: {message}")
    if not condition:
        FAILURES.append(message)


def test_apb_bus_decode_slot_routing():
    scLibdir = os.environ.get('SYSTEMC_LIBDIR', '')
    tmpdir = tempfile.mkdtemp(prefix='a2c_apb_bus_decode_')
    try:
        binPath = buildProbe(tmpdir, PROBE_SRC)
        if not os.path.isfile(binPath):
            check(False, f"decode probe must build and link: {binPath}")
            return
        for scenario, (status, present, absent) in SCENARIOS.items():
            try:
                run = subprocess.run([binPath, scenario], capture_output=True, text=True, timeout=60,
                                     env=dict(os.environ, LD_LIBRARY_PATH=scLibdir))
            except subprocess.TimeoutExpired:
                check(False, f"{scenario} finishes within 60 s")
                continue
            output = run.stdout + run.stderr
            before = len(FAILURES)
            check(run.returncode == status, f"{scenario} exits with status {status} (got {run.returncode})")
            for needle in present:
                check(needle in output, f"{scenario} prints {needle!r}")
            for needle in absent:
                check(needle not in output, f"{scenario} does not print {needle!r}")
            if len(FAILURES) > before:
                print(output)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == '__main__':
    test_apb_bus_decode_slot_routing()
    if FAILURES:
        print(f"\n  SOME TESTS FAILED ({len(FAILURES)})")
        sys.exit(1)
    print("\n  ALL TESTS PASSED!")
    sys.exit(0)
