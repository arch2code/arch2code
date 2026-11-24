#!/usr/bin/env python3
"""registerHandler maps a register only at the offsets the generated RTL decodes.

The generated register RTL (moduleRegs.py) has one `case` arm per 32-bit word
of a register: base, base + 4, and so on up to the register's width. Any other
offset inside the register falls to the default arm, which drops a write and
reads 0xBADDC0DE, with PSLVERR when the project sets regBusErrorResponses. The
model must decode the same offsets, or a read at base + 1 would read a
shifted word that the RTL never returns.

The probe serves a 1-byte register at 0x0, a 4-byte register at 0x4 and a
6-byte register (two words) at 0x8, response-aware with errorResponses. It
writes and reads every byte offset from 0x0 to 0xf. The word offsets 0x0, 0x4,
0x8 and 0xc complete without PSLVERR. Every other offset completes with PSLVERR
and reads 0xBADDC0DE. The unaligned writes leave the registers unchanged, and
the 6-byte register's cpu_read runs only for its two word reads.
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
#include "apb_channel.h"
#include "hwRegister.h"
#include "addressMap.h"
#include <cstdint>
#include <format>
#include <iostream>
#include <string>

struct wdAddrSt {
    static constexpr unsigned _bitWidth = 32;
    static const char* getValueType() { return ""; }
    std::uint64_t getStructValue() const { return value; }
    std::uint64_t _getAddress() const { return value; }
    std::string prt( bool = false ) const { return std::format( "addr:0x{:x}", value ); }
    bool operator==( const wdAddrSt& o ) const { return value == o.value; }
    std::uint32_t value = 0;
};

struct wdDataSt {
    static constexpr unsigned _bitWidth = 32;
    static const char* getValueType() { return ""; }
    std::uint64_t getStructValue() const { return value; }
    std::uint32_t _getData() const { return value; }
    void _setData( std::uint64_t v ) { value = static_cast<std::uint32_t>( v ); }
    std::string prt( bool = false ) const { return std::format( "data:0x{:x}", value ); }
    bool operator==( const wdDataSt& o ) const { return value == o.value; }
    std::uint32_t value = 0;
};

template <unsigned BITS>
struct bitsSt {
    std::uint64_t v = 0;
    static constexpr std::uint16_t _bitWidth = BITS;
    typedef std::uint64_t _packedSt;
    inline void unpack( const _packedSt &p ) { v = p; }
    inline sc_bv<BITS> sc_pack( void ) const { sc_bv<BITS> p; p = v; return p; }
    inline void sc_unpack( sc_bv<BITS> p ) { v = p.to_uint64(); }
};

template <class REG_DATA, int N>
struct countingRegister : public hwRegister<REG_DATA, N>
{
    int reads = 0;
    std::uint32_t cpu_read( std::uint64_t address ) override
    {
        reads++;
        return hwRegister<REG_DATA, N>::cpu_read( address );
    }
};

struct wdHarness : public sc_module
{
    apb_channel<wdAddrSt, wdDataSt> chan;
    sc_port<apb_in_if<wdAddrSt, wdDataSt>> in;
    logBlock log;
    addressMap regs;
    hwRegister<bitsSt<8>, 4> r1;
    hwRegister<bitsSt<32>, 4> r4;
    countingRegister<bitsSt<48>, 8> r6;

    SC_HAS_PROCESS( wdHarness );
    wdHarness( sc_module_name n )
      : sc_module( n ), chan( "chan", "tb" ), in( "in" ), log( "wdHarness" ), regs( log )
    {
        in( chan );
        regs.addRegister( 0x0, 1, "r1", &r1 );
        regs.addRegister( 0x4, 4, "r4", &r4 );
        regs.addRegister( 0x8, 6, "r6", &r6 );
        SC_THREAD( handle );
        SC_THREAD( drive );
    }

    void handle()
    {
        registerHandler<wdAddrSt, wdDataSt>( regs, in, 0xff, true );
    }

    void drive()
    {
        for (std::uint32_t a = 0; a < 0x10; a++) {
            wdAddrSt addr;
            wdDataSt data;
            addr.value = a;
            data.value = (a % 4 == 0) ? 0x11 * (a + 1) : 0xdead;
            const bool slverr = chan.requestWithResponse( true, addr, data );
            std::cout << std::format( "write 0x{:x} slverr={}\\n", a, slverr );
        }
        for (std::uint32_t a = 0; a < 0x10; a++) {
            wdAddrSt addr;
            wdDataSt data;
            addr.value = a;
            const bool slverr = chan.requestWithResponse( false, addr, data );
            std::cout << std::format( "read 0x{:x}=0x{:x} slverr={}\\n", a, data.value, slverr );
        }
        std::cout << std::format( "r6Reads={}\\n", r6.reads );
        sc_stop();
    }
};

int sc_main( int, char ** )
{
    wdHarness harness( "harness" );
    sc_start();
    int code = errorCode::getExitCode();
    std::cout << "exitCode=" << code << "\\n";
    return code > 0 ? code : 0;
}
"""

# Word offsets and the value each reads back after the writes. r1 keeps 8
# bits; r6's word at 0xc keeps 16.
WORDS = {0x0: 0x11, 0x4: 0x55, 0x8: 0x99, 0xc: 0xdd}

FAILURES = []


def check(condition, message):
    print(f"  {'PASS' if condition else 'FAIL'}: {message}")
    if not condition:
        FAILURES.append(message)


def test_register_handler_word_decode():
    scLibdir = os.environ.get('SYSTEMC_LIBDIR', '')
    tmpdir = tempfile.mkdtemp(prefix='a2c_reg_word_decode_')
    try:
        binPath = buildProbe(tmpdir, PROBE_SRC)
        if not os.path.isfile(binPath):
            check(False, f"registerHandler probe must build and link: {binPath}")
            return
        run = subprocess.run([binPath], capture_output=True, text=True, timeout=60,
                             env=dict(os.environ, LD_LIBRARY_PATH=scLibdir))
        output = run.stdout + run.stderr
        check(run.returncode == 0, f"probe exits with status 0 (got {run.returncode})")
        lines = set(output.splitlines())
        for a in range(0x10):
            if a in WORDS:
                check(f"write 0x{a:x} slverr=false" in lines, f"write at word offset 0x{a:x} completes without PSLVERR")
                check(f"read 0x{a:x}=0x{WORDS[a]:x} slverr=false" in lines,
                      f"read at word offset 0x{a:x} returns 0x{WORDS[a]:x} without PSLVERR")
            else:
                check(f"write 0x{a:x} slverr=true" in lines, f"write at byte offset 0x{a:x} is unmapped")
                check(f"read 0x{a:x}=0xbaddc0de slverr=true" in lines,
                      f"read at byte offset 0x{a:x} is unmapped and returns 0xBADDC0DE")
        check('r6Reads=2' in lines, "the 6-byte register's cpu_read runs only for its two word reads")
        if FAILURES:
            print(output)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == '__main__':
    test_register_handler_word_decode()
    if FAILURES:
        print(f"\n  SOME TESTS FAILED ({len(FAILURES)})")
        sys.exit(1)
    print("\n  ALL TESTS PASSED!")
    sys.exit(0)
