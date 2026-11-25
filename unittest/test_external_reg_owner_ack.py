#!/usr/bin/env python3
"""A firmware write to an ext register completes only after the owner has handled it.

In RTL the owner of an ext register reacts to the write strobe by the next
clock, so a firmware read-back after the write sees the owner's new value. The
model keeps that order with an ack: reg_write_cmd() returns only when the
owner, having taken the command with read(), calls read() again. Owners
publish the read-back value with update_mirror() before they return to read().

The probe checks four owners:
  * slow: takes 10 extra deltas and 5 ns before it publishes. The write
    returns 5 ns later, and the mirror then holds the owner's value.
  * same: publishes the value already in the mirror. update_mirror() raises
    no event for it, and the write still completes.
  * busy: does other work for 20 ns before its first read(). A write issued
    meanwhile stays pending, read() returns it, and the write completes then.
  * hw: the slow owner behind an hwRegisterIf, as the register handler drives
    it. cpu_write() returns after the owner publishes, so cpu_read() returns
    the owner's value.
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
#include "hwRegister.h"
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
    sc_bv<32> sc_pack() const { sc_bv<32> p; p = w; return p; }
    void sc_unpack( sc_bv<32> p ) { w = (std::uint32_t)p.to_uint64(); }
    std::string prt( bool = false ) const { return std::format( "0x{:x}", w ); }
    bool operator==( const regSt& o ) const { return w == o.w; }
};

static regSt val( std::uint32_t v ) { regSt r; r.w = v; return r; }

static int failures = 0;
static void check( bool ok, const std::string& what )
{
    std::printf( "%s: %s\n", ok ? "PASS" : "FAIL", what.c_str() );
    if ( !ok ) failures++;
}

SC_MODULE( probe )
{
    external_reg_channel<regSt> chSlow;
    external_reg_channel<regSt> chSame;
    external_reg_channel<regSt> chBusy;
    external_reg_channel<regSt> chHw;
    external_reg_out<regSt> hwPort;
    hwRegisterIf<regSt, external_reg_out<regSt>, 4, false> hwReg;
    int sameMirrorEvents = 0;
    int busyCommands = 0;
    bool done = false;

    SC_CTOR( probe ) : chSlow( "chSlow", "tb" ), chSame( "chSame", "tb", 0x77 ), chBusy( "chBusy", "tb" ),
                       chHw( "chHw", "tb" ), hwPort( "hwPort" ), hwReg( &hwPort )
    {
        hwPort( chHw );
        sc_spawn( [this]() { slowOwner( chSlow ); } );
        sc_spawn( [this]() { slowOwner( chHw ); } );
        SC_THREAD( sameOwner );
        SC_THREAD( sameMirror );
        SC_THREAD( busyOwner );
        SC_THREAD( script );
    }

    // Takes each command, spends 10 deltas and 5 ns on it, publishes wdata + 1.
    void slowOwner( external_reg_channel<regSt>& ch )
    {
        while ( true ) {
            regSt w;
            ch.read( w );
            for ( int i = 0; i < 10; i++ ) {
                wait( SC_ZERO_TIME );
            }
            wait( 5, SC_NS );
            ch.update_mirror( val( w.w + 1 ) );
        }
    }

    // Publishes 0x77 at start, then again after each command. The first
    // publish raises a mirror event, the later ones do not.
    void sameOwner()
    {
        chSame.update_mirror( val( 0x77 ) );
        while ( true ) {
            regSt w;
            chSame.read( w );
            chSame.update_mirror( val( 0x77 ) );
        }
    }
    void sameMirror() { while ( true ) { chSame.wait_mirror(); sameMirrorEvents++; } }

    // Busy for 20 ns before it first waits for a command.
    void busyOwner()
    {
        wait( 20, SC_NS );
        while ( true ) {
            regSt w;
            chBusy.read( w );
            busyCommands++;
            chBusy.update_mirror( val( w.w + 1 ) );
        }
    }

    void script()
    {
        wait( 10, SC_NS );
        // busy: the owner reaches read() at 20 ns
        sc_time t0 = sc_time_stamp();
        chBusy.reg_write_cmd( val( 3 ) );
        check( busyCommands == 1, std::format( "busy: the write issued before the owner reached read() is delivered ({} command(s))", busyCommands ) );
        check( sc_time_stamp() == sc_time( 20, SC_NS ), std::format( "busy: the write completes when the owner takes it (at {})", sc_time_stamp().to_string() ) );
        check( chBusy.readNonBlocking().w == 4, std::format( "busy: the read-back after the write is the owner's value (0x{:x})", chBusy.readNonBlocking().w ) );

        // slow
        wait( 10, SC_NS );
        t0 = sc_time_stamp();
        chSlow.reg_write_cmd( val( 5 ) );
        check( sc_time_stamp() == t0 + sc_time( 5, SC_NS ), std::format( "slow: the write completes after the owner's 5 ns (took {})", ( sc_time_stamp() - t0 ).to_string() ) );
        check( chSlow.readNonBlocking().w == 6, std::format( "slow: the read-back after the write is the owner's value 0x6 (got 0x{:x})", chSlow.readNonBlocking().w ) );
        chSlow.reg_write_cmd( val( 7 ) );
        check( chSlow.readNonBlocking().w == 8, std::format( "slow: a second write reads back 0x8 (got 0x{:x})", chSlow.readNonBlocking().w ) );

        // same
        wait( 10, SC_NS );
        int eventsBefore = sameMirrorEvents;
        chSame.reg_write_cmd( val( 1 ) );
        chSame.reg_write_cmd( val( 2 ) );
        check( true, "same: writes whose published value is unchanged complete" );
        wait( 1, SC_NS );
        check( sameMirrorEvents == eventsBefore, std::format( "same: the unchanged publishes raise no mirror event ({})", sameMirrorEvents - eventsBefore ) );

        // hw
        wait( 10, SC_NS );
        t0 = sc_time_stamp();
        hwReg.cpu_write( 0, 0x10 );
        check( sc_time_stamp() == t0 + sc_time( 5, SC_NS ), std::format( "hw: cpu_write() returns after the owner's 5 ns (took {})", ( sc_time_stamp() - t0 ).to_string() ) );
        check( hwReg.cpu_read( 0 ) == 0x11, std::format( "hw: cpu_read() after cpu_write() returns the owner's value 0x11 (got 0x{:x})", hwReg.cpu_read( 0 ) ) );

        done = true;
        sc_stop();
    }
};

int sc_main( int, char *[] )
{
    probe p( "probe" );
    sc_start( 1, SC_US );
    check( p.done, "every write completes" );
    std::printf( "failures=%d\n", failures );
    return failures == 0 ? 0 : 1;
}
"""

FAILURES = []


def check(condition, message):
    print(f"  {'PASS' if condition else 'FAIL'}: {message}")
    if not condition:
        FAILURES.append(message)


def test_external_reg_owner_ack():
    tmpdir = tempfile.mkdtemp(prefix='a2c_external_reg_owner_ack_')
    try:
        binPath = buildProbe(tmpdir, PROBE_SRC)
        if not os.path.isfile(binPath):
            check(False, f"external_reg owner ack probe must build and link: {binPath}")
            return
        run = subprocess.run([binPath], capture_output=True, text=True, timeout=60,
                             env=dict(os.environ, LD_LIBRARY_PATH=os.environ['SYSTEMC_LIBDIR']))
        output = run.stdout + run.stderr
        for line in output.splitlines():
            if line.startswith(('PASS: ', 'FAIL: ')):
                check(line.startswith('PASS: '), line[6:])
        check(run.returncode == 0 and 'failures=0' in output, f"the probe exits with status 0 (got {run.returncode})")
        if FAILURES:
            print(output)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == '__main__':
    print("=" * 72)
    print("TESTING EXTERNAL_REG OWNER ACK")
    print("=" * 72)
    test_external_reg_owner_ack()
    if FAILURES:
        print(f"\nRESULT: {len(FAILURES)} check(s) FAILED")
        sys.exit(1)
    print("\nRESULT: all external_reg owner ack checks passed")
    sys.exit(0)
