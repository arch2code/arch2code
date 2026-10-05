#!/usr/bin/env python3
"""registerHandler answers an address gap inside a register block with 0xBADDC0DE.

A gap is an address in the block's decoded range that no register or memory
claims. A read there returns 0xBADDC0DE, the value an empty decoder slot reads.
An address past the decoded range aliases through the address mask onto an
address in the range, so it is no gap. The value is truncated to a
data bus narrower than 32 bits. A write to a gap is dropped and leaves every
register unchanged. The model prints a warning naming the block and the address
for each, as the decoder does for an empty slot.

The probe serves two 4-byte registers at offsets 0x0 and 0x8, so 0x4 is a gap
between them and 0xc is a gap past the last one. It writes both registers,
writes both gaps, then reads all four addresses. The 16-bit scenario runs the
same sequence over a 16-bit data bus.
"""

import os
import shutil
import subprocess
import sys
import tempfile

from test_watchdog_no_terminator import buildProbe

PROBE_SRC = """
#include "systemc.h"
#include "logging.h"
#include "q_assert.h"
#include "addressMap.h"
#include <cstdint>
#include <format>
#include <iostream>
#include <string>

struct gapAddrSt {
    static constexpr unsigned _bitWidth = 32;
    static const char* getValueType() { return ""; }
    std::uint64_t getStructValue() const { return value; }
    std::uint64_t _getAddress() const { return value; }
    std::string prt( bool = false ) const { return std::format( "addr:0x{:x}", value ); }
    bool operator==( const gapAddrSt& o ) const { return value == o.value; }
    std::uint32_t value = 0;
};

template <unsigned WIDTH>
struct gapDataSt {
    static constexpr unsigned _bitWidth = WIDTH;
    static const char* getValueType() { return ""; }
    std::uint64_t getStructValue() const { return value; }
    std::uint32_t _getData() const { return value; }
    void _setData( std::uint64_t v ) { value = static_cast<std::uint32_t>( v ); }
    std::string prt( bool = false ) const { return std::format( "data:0x{:x}", value ); }
    bool operator==( const gapDataSt& o ) const { return value == o.value; }
    std::uint32_t value = 0;
};

struct stubReg : public addressBase {
    void cpu_write( std::uint64_t, std::uint32_t val ) override { value = val; }
    std::uint32_t cpu_read( std::uint64_t ) override { return value; }
    std::uint32_t value = 0;
};

template <unsigned WIDTH>
struct gapHarness : public sc_module
{
    using dataT = gapDataSt<WIDTH>;
    apb_channel<gapAddrSt, dataT> chan;
    sc_port<apb_in_if<gapAddrSt, dataT>> in;
    logBlock log;
    addressMap regs;
    stubReg r0, r2;

    SC_HAS_PROCESS( gapHarness );
    gapHarness( sc_module_name n )
      : sc_module( n ), chan( "chan", "tb" ), in( "in" ), log( "gapHarness" ), regs( log )
    {
        in( chan );
        regs.addRegister( 0x0, 4, "r0", &r0 );
        regs.addRegister( 0x8, 4, "r2", &r2 );
        SC_THREAD( handle );
        SC_THREAD( drive );
    }

    void handle() { registerHandler<gapAddrSt, dataT>( regs, in, 0xff ); }

    void write( std::uint32_t address, std::uint32_t value )
    {
        gapAddrSt addr;
        dataT data;
        addr.value = address;
        data.value = value;
        chan.request( true, addr, data );
    }

    void read( std::uint32_t address )
    {
        gapAddrSt addr;
        dataT data;
        addr.value = address;
        data.value = 0x5555;
        chan.request( false, addr, data );
        std::cout << std::format( "read 0x{:x}=0x{:x}\\n", address, data.value );
    }

    void drive()
    {
        write( 0x0, 0x1111 );
        write( 0x8, 0x2222 );
        write( 0x4, 0xdead );
        write( 0xc, 0xbeef );
        read( 0x4 );
        read( 0xc );
        read( 0x0 );
        read( 0x8 );
        sc_stop();
    }
};

int sc_main( int argc, char* argv[] )
{
    if (std::string( argv[1] ) == "wide") {
        gapHarness<32> harness( "harness" );
        sc_start();
    } else {
        gapHarness<16> harness( "harness" );
        sc_start();
    }
    int code = errorCode::getExitCode();
    std::cout << "exitCode=" << code << "\\n";
    return code > 0 ? code : 0;
}
"""

# scenario -> output that must be present, output that must be absent
SCENARIOS = {
    'wide': (('read 0x4=0xbaddc0de', 'read 0xc=0xbaddc0de', 'read 0x0=0x1111', 'read 0x8=0x2222',
              'harness: firmware read of unmapped address 0x4 returns 0xBADDC0DE',
              'harness: firmware write to unmapped address 0xc dropped'),
             ('0xdead', '0xbeef')),
    'narrow': (('read 0x4=0xc0de', 'read 0xc=0xc0de', 'read 0x0=0x1111', 'read 0x8=0x2222'),
               ('0xdead', '0xbeef')),
}

FAILURES = []


def check(condition, message):
    print(f"  {'PASS' if condition else 'FAIL'}: {message}")
    if not condition:
        FAILURES.append(message)


def test_register_handler_gap():
    scLibdir = os.environ.get('SYSTEMC_LIBDIR', '')
    tmpdir = tempfile.mkdtemp(prefix='a2c_reg_handler_gap_')
    try:
        binPath = buildProbe(tmpdir, PROBE_SRC)
        if not os.path.isfile(binPath):
            check(False, f"register handler probe must build and link: {binPath}")
            return
        for scenario, (present, absent) in SCENARIOS.items():
            try:
                run = subprocess.run([binPath, scenario], capture_output=True, text=True, timeout=60,
                                     env=dict(os.environ, LD_LIBRARY_PATH=scLibdir))
            except subprocess.TimeoutExpired:
                check(False, f"{scenario} finishes within 60 s")
                continue
            output = run.stdout + run.stderr
            before = len(FAILURES)
            check(run.returncode == 0, f"{scenario} exits with status 0 (got {run.returncode})")
            for needle in present:
                check(needle in output, f"{scenario} prints {needle!r}")
            for needle in absent:
                check(needle not in output, f"{scenario} does not print {needle!r}")
            if len(FAILURES) > before:
                print(output)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == '__main__':
    test_register_handler_gap()
    if FAILURES:
        print(f"\n  SOME TESTS FAILED ({len(FAILURES)})")
        sys.exit(1)
    print("\n  ALL TESTS PASSED!")
    sys.exit(0)
