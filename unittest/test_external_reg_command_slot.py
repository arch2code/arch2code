#!/usr/bin/env python3
"""external_reg reg_write() and reg_write_cmd() share one command slot, and the hang status names what holds it.

A firmware write (reg_write_cmd) stays open until the owner takes it with
read() and calls read() again. reg_write() fills the same slot, so a
reg_write() while a firmware write is open would replace that write. The
channel asserts on it. Two reg_write() calls with no firmware write open merge,
as on a status channel, and read() returns the second value once.

When a run hangs, the channel's status names the register and what holds the
slot: a firmware write the owner has not taken, one it took without returning
to read(), a firmware write a Tandem tee holds, or a reg_write() value the
owner has not taken.

Each mode runs in its own process, because an assert ends the run:
  * fwOpen: reg_write() while a firmware write waits for read(). Asserts.
  * merge: two reg_write() calls in one delta, then the owner starts reading.
    read() returns 0x2 once, and the mirror holds 0x2.
  * statusPending, statusTaken, statusTee, statusRegWrite: print the status
    for each state of the slot.
"""

import os
import shutil
import subprocess
import sys
import tempfile

from test_watchdog_no_terminator import buildProbe

PROBE_SRC = r"""
#include "systemc.h"
#include "logging.h"
#include "q_assert.h"
#include "external_reg_channel.h"
#include <cstdint>
#include <cstdio>
#include <format>
#include <string>

struct regSt {
    std::uint32_t w = 0;
    static constexpr std::uint16_t _bitWidth = 32;
    typedef std::uint32_t _packedSt;
    static const char* getValueType() { return ""; }
    std::uint64_t getStructValue() const { return w; }
    void pack( _packedSt& v ) const { v = w; }
    void unpack( const _packedSt& v ) { w = v; }
    std::string prt( bool = false ) const { return std::format( "0x{:x}", w ); }
    bool operator==( const regSt& o ) const { return w == o.w; }
};

static regSt val( std::uint32_t v ) { regSt r; r.w = v; return r; }

static std::string mode;

SC_MODULE( probe )
{
    external_reg_channel<regSt> ch;
    sc_event never;

    SC_CTOR( probe ) : ch( "ch", "tb" )
    {
        if ( mode == "statusTee" ) {
            ch.setCommandHook( []( const regSt& ) {} );
        }
        SC_THREAD( script );
    }

    void reader( bool hold )
    {
        while ( true ) {
            regSt w;
            ch.read( w );
            std::printf( "read=%s@%s\n", w.prt().c_str(), sc_time_stamp().to_string().c_str() );
            if ( hold ) {
                wait( never );
            }
        }
    }

    void script()
    {
        if ( mode == "fwOpen" ) {
            sc_spawn( [this]() { ch.reg_write_cmd( val( 5 ) ); } );
            wait( 5, SC_NS );
            ch.reg_write( val( 6 ) );
            std::printf( "regWriteReturned=1\n" );
        } else if ( mode == "merge" ) {
            ch.reg_write( val( 1 ) );
            ch.reg_write( val( 2 ) );
            wait( 5, SC_NS );
            sc_spawn( [this]() { reader( false ); } );
            wait( 5, SC_NS );
            std::printf( "mirror=%s\n", ch.readNonBlocking().prt().c_str() );
        } else {
            if ( mode == "statusRegWrite" ) {
                ch.reg_write( val( 7 ) );
            } else {
                sc_spawn( [this]() { ch.reg_write_cmd( val( 5 ) ); } );
            }
            if ( mode == "statusTaken" ) {
                sc_spawn( [this]() { reader( true ); } );
            }
            wait( 5, SC_NS );
            ch.status();
        }
        std::printf( "end=%s\n", mode.c_str() );
        sc_stop();
    }
};

int sc_main( int argc, char* argv[] )
{
    mode = argv[1];
    logging::GetInstance().setDefaultVerbosity( VERBOSITY_MEDIUM );
    probe p( "probe" );
    sc_start( 1, SC_US );
    return 0;
}
"""

# mode -> (output that must be present, output that must be absent)
SCENARIOS = {
    'fwOpen': (('[Q_ASSERT][probe.ch] external_reg reg_write() while a firmware write is open',),
               ('regWriteReturned=1', 'end=fwOpen')),
    'merge': (('read=0x2@5 ns', 'mirror=0x2', 'end=merge'), ('[Q_ASSERT]', 'read=0x1')),
    'statusPending': (("probe.ch has firmware write 0x5 waiting for the owner's read() to take it",),
                      ('[Q_ASSERT]', 'Tandem')),
    'statusTaken': (('read=0x5@0 s', "probe.ch has firmware write 0x5 taken by the owner, which has not returned to read()"),
                    ('[Q_ASSERT]', 'Tandem')),
    'statusTee': (('probe.ch has firmware write 0x5 open, waiting for the Tandem tee to complete it',),
                  ('[Q_ASSERT]', "owner's read()")),
    'statusRegWrite': (("probe.ch has reg_write() value 0x7 waiting for the owner's read() to take it",),
                       ('[Q_ASSERT]', 'firmware write')),
}

FAILURES = []


def check(condition, message):
    print(f"  {'PASS' if condition else 'FAIL'}: {message}")
    if not condition:
        FAILURES.append(message)


def test_external_reg_command_slot():
    tmpdir = tempfile.mkdtemp(prefix='a2c_external_reg_command_slot_')
    try:
        binPath = buildProbe(tmpdir, PROBE_SRC)
        if not os.path.isfile(binPath):
            check(False, f"external_reg command slot probe must build and link: {binPath}")
            return
        for mode, (present, absent) in SCENARIOS.items():
            run = subprocess.run([binPath, mode], capture_output=True, text=True, timeout=60,
                                 env=dict(os.environ, LD_LIBRARY_PATH=os.environ['SYSTEMC_LIBDIR']))
            output = run.stdout + run.stderr
            before = len(FAILURES)
            for needle in present:
                check(needle in output, f"{mode} prints {needle!r}")
            for needle in absent:
                check(needle not in output, f"{mode} does not print {needle!r}")
            if len(FAILURES) > before:
                print(output)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == '__main__':
    print("=" * 72)
    print("TESTING EXTERNAL_REG COMMAND SLOT")
    print("=" * 72)
    test_external_reg_command_slot()
    if FAILURES:
        print(f"\nRESULT: {len(FAILURES)} check(s) FAILED")
        sys.exit(1)
    print("\nRESULT: all external_reg command slot checks passed")
    sys.exit(0)
