#!/usr/bin/env python3
"""external_reg_channel delivers each leg at a fixed delta, with fixed values.

The channel carries three legs between a driver and the register owner:
  * command: reg_write_cmd() wakes read() one delta later, and returns one
    delta after the owner calls read() again.
  * mirror: update_mirror() changes readNonBlocking() in the same delta and
    wakes wait_mirror() one delta later.
  * status: write() wakes reg_read() one delta later.
A Tandem tee sets a command hook, a mirror hook and a done hook, which run
inside the call that makes the change, in the caller's delta, and change no
wakeup. It posts commands with post_cmd() and completes the ones it takes
through the hook with complete_cmd().

The Tandem tees and the BFMs rely on these timings, so this pins them.
"""

import os
import shutil
import subprocess
import sys
import tempfile

from test_watchdog_no_terminator import buildProbe

PROBE_SRC = r"""
#include "systemc.h"
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

static int failures = 0;
static void check( bool ok, const std::string& what )
{
    std::printf( "%s: %s\n", ok ? "PASS" : "FAIL", what.c_str() );
    if ( !ok ) failures++;
}

// Counts the wakeups of one blocking call and keeps the last value and delta.
struct waiter {
    int wakes = 0;
    std::uint32_t value = 0;
    std::uint64_t delta = 0;
    void woke( std::uint32_t v ) { wakes++; value = v; delta = sc_delta_count(); }
};

SC_MODULE( probe )
{
    external_reg_channel<regSt> ch;      // initial value 0x11
    external_reg_channel<regSt> chInit;  // initial value 0x42
    external_reg_channel<regSt> chExt;   // status leg redirected to extEvent
    external_reg_channel<regSt> chHook;  // both hooks set
    external_reg_channel<regSt> chFwd;   // takes chHook's commands through its command hook
    external_reg_channel<regSt> chTee;   // completed by complete_cmd() alone, nothing reads it
    external_reg_channel<regSt> chCopy;  // takes chHook's mirror through its mirror hook
    sc_event extEvent;
    waiter cmd, mirror, status, initMirror, ext, hookCmd, hookMirror, hookRead, fwdRead, hookStatus, done;
    std::string hookCmdValues;

    SC_CTOR( probe ) : ch( "ch", "tb", 0x11 ), chInit( "chInit", "tb", 0x42 ), chExt( "chExt", "tb" ),
                       chHook( "chHook", "tb" ), chFwd( "chFwd", "tb" ), chTee( "chTee", "tb" ), chCopy( "chCopy", "tb" )
    {
        chExt.setExternalEvent( &extEvent );
        chHook.setCommandHook( [this]( const regSt& v ) {
            hookCmd.woke( v.w );
            hookCmdValues += std::format( "{:x}", v.w );
            chFwd.post_cmd( v ); } );
        chFwd.setDoneHook( [this]() { done.woke( 0 ); } );
        chHook.setMirrorHook( [this]( const regSt& v ) {
            hookMirror.woke( v.w );
            chCopy.update_mirror( v ); } );
        SC_THREAD( hookReader );
        SC_THREAD( fwdReader );
        SC_THREAD( hookStatusReader );
        SC_THREAD( commandReader );
        SC_THREAD( mirrorWaiter );
        SC_THREAD( statusReader );
        SC_THREAD( initMirrorWaiter );
        SC_THREAD( extWaiter );
        SC_THREAD( script );
    }

    void commandReader() { while ( true ) { regSt v; ch.read( v ); cmd.woke( v.w ); } }
    void mirrorWaiter() { while ( true ) { ch.wait_mirror(); mirror.woke( ch.readNonBlocking().w ); } }
    void statusReader() { while ( true ) { regSt v; ch.reg_read( v ); status.woke( v.w ); } }
    void initMirrorWaiter() { while ( true ) { chInit.wait_mirror(); initMirror.woke( chInit.readNonBlocking().w ); } }
    void extWaiter() { while ( true ) { wait( extEvent ); ext.woke( 0 ); } }
    void hookReader() { while ( true ) { regSt v; chHook.read( v ); hookRead.woke( v.w ); } }
    void fwdReader() { while ( true ) { regSt v; chFwd.read( v ); fwdRead.woke( v.w ); } }
    void hookStatusReader() { while ( true ) { regSt v; chHook.reg_read( v ); hookStatus.woke( v.w ); } }

    void script()
    {
        check( ch.readNonBlocking().w == 0x11, "readNonBlocking() returns the initial value before any publish" );
        check( chInit.readNonBlocking().w == 0x42, "a channel built at 0x42 reads 0x42 before any publish" );

        // command leg
        wait( 10, SC_NS );
        std::uint64_t d = sc_delta_count();
        ch.reg_write_cmd( val( 5 ) );
        check( sc_delta_count() == d + 2, std::format( "reg_write_cmd() returns one delta after the owner is back in read() (delta +{})", sc_delta_count() - d ) );
        check( ch.readNonBlocking().w == 0x11, "reg_write_cmd() leaves the mirror alone" );
        wait( 1, SC_NS );
        check( cmd.wakes == 1 && cmd.value == 5, std::format( "read() wakes once with the command (wakes {}, value 0x{:x})", cmd.wakes, cmd.value ) );
        check( cmd.delta == d + 1, std::format( "read() wakes one delta after reg_write_cmd() (delta +{})", cmd.delta - d ) );
        check( mirror.wakes == 0, "reg_write_cmd() raises no mirror event" );

        wait( 9, SC_NS );
        ch.reg_write_cmd( val( 6 ) );
        check( cmd.wakes == 2 && cmd.value == 6, "back-to-back commands: read() has the first when the first returns" );
        ch.reg_write_cmd( val( 7 ) );
        check( cmd.wakes == 3 && cmd.value == 7, std::format( "back-to-back commands wake read() once each, in order (wakes {}, value 0x{:x})", cmd.wakes, cmd.value ) );

        // mirror leg
        wait( 9, SC_NS );
        d = sc_delta_count();
        ch.update_mirror( val( 9 ) );
        check( ch.readNonBlocking().w == 9, "update_mirror() changes readNonBlocking() in the same delta" );
        wait( 1, SC_NS );
        check( mirror.wakes == 1 && mirror.value == 9, std::format( "wait_mirror() wakes once with the new value (wakes {}, value 0x{:x})", mirror.wakes, mirror.value ) );
        check( mirror.delta == d + 1, std::format( "wait_mirror() wakes one delta after update_mirror() (delta +{})", mirror.delta - d ) );
        check( cmd.wakes == 3, "update_mirror() does not wake read()" );

        wait( 9, SC_NS );
        ch.update_mirror( val( 9 ) );
        wait( 1, SC_NS );
        check( mirror.wakes == 1, "publishing the value already there raises no mirror event" );

        wait( 9, SC_NS );
        chInit.update_mirror( val( 0x42 ) );
        wait( 1, SC_NS );
        check( initMirror.wakes == 1 && initMirror.value == 0x42, "the first publish raises a mirror event even when it equals the initial value" );

        // reg_write sets both
        wait( 9, SC_NS );
        d = sc_delta_count();
        ch.reg_write( val( 0x20 ) );
        check( ch.readNonBlocking().w == 0x20, "reg_write() changes readNonBlocking() in the same delta" );
        wait( 1, SC_NS );
        check( cmd.wakes == 4 && cmd.value == 0x20 && cmd.delta == d + 1, "reg_write() wakes read() one delta later with the value" );
        check( mirror.wakes == 2 && mirror.value == 0x20 && mirror.delta == d + 1, "reg_write() wakes wait_mirror() one delta later" );

        wait( 9, SC_NS );
        ch.reg_write( val( 0x20 ) );
        wait( 1, SC_NS );
        check( cmd.wakes == 5 && mirror.wakes == 2, "reg_write() of the same value wakes read() but raises no mirror event" );

        // status leg
        wait( 9, SC_NS );
        d = sc_delta_count();
        ch.write( val( 3 ) );
        wait( 1, SC_NS );
        check( status.wakes == 1 && status.value == 3 && status.delta == d + 1, std::format( "reg_read() wakes one delta after write() with the value (wakes {}, delta +{})", status.wakes, status.delta - d ) );
        check( cmd.wakes == 5 && mirror.wakes == 2 && ch.readNonBlocking().w == 0x20, "write() touches neither the command nor the mirror" );

        wait( 9, SC_NS );
        ch.write( val( 3 ) );
        wait( 1, SC_NS );
        check( status.wakes == 1, "write() of the same value raises no status event" );

        wait( 9, SC_NS );
        d = sc_delta_count();
        chExt.write( val( 4 ) );
        wait( 1, SC_NS );
        check( ext.wakes == 1 && ext.delta == d + 1, "setExternalEvent() moves the status wakeup to the given event" );

        // hooks
        wait( 9, SC_NS );
        d = sc_delta_count();
        chHook.reg_write_cmd( val( 1 ) );
        check( hookCmd.wakes == 1 && hookCmd.delta == d,
               std::format( "the command hook runs in the delta of reg_write_cmd() (delta +{})", hookCmd.delta - d ) );
        check( hookRead.wakes == 1 && hookRead.value == 1 && hookRead.delta == d + 1, "with the hook set, read() still wakes one delta later with the command" );
        check( fwdRead.wakes == 1 && fwdRead.value == 1 && fwdRead.delta == d + 1,
               std::format( "a command the hook posts wakes the next channel's read() in the same delta as a direct one (delta +{})", fwdRead.delta - d ) );
        check( done.wakes == 1 && done.delta == d + 1,
               std::format( "the done hook runs in the delta the owner returns to read() (calls {}, delta +{})", done.wakes, done.delta - d ) );
        chHook.reg_write_cmd( val( 2 ) );
        check( hookCmd.wakes == 2 && hookCmdValues == "12", std::format( "the command hook runs once per command (values {})", hookCmdValues ) );
        check( hookMirror.wakes == 0, "reg_write_cmd() does not run the mirror hook" );

        // a command taken through the hook, completed by complete_cmd()
        wait( 9, SC_NS );
        d = sc_delta_count();
        chTee.post_cmd( val( 3 ) );
        check( sc_delta_count() == d, "post_cmd() returns at once" );
        chTee.complete_cmd();
        sc_time t0 = sc_time_stamp();
        sc_spawn( [this]() { wait( 2, SC_NS ); chTee.complete_cmd(); } );
        chTee.reg_write_cmd( val( 4 ) );
        check( sc_time_stamp() == t0 + sc_time( 2, SC_NS ), "a command nothing reads completes when complete_cmd() is called" );

        wait( 9, SC_NS );
        d = sc_delta_count();
        chHook.update_mirror( val( 5 ) );
        check( hookMirror.wakes == 1 && hookMirror.value == 5 && hookMirror.delta == d, "update_mirror() runs the mirror hook in its delta" );
        check( chCopy.readNonBlocking().w == 5, "a mirror copied by the hook is visible in the same delta" );
        chHook.update_mirror( val( 5 ) );
        check( hookMirror.wakes == 1, "a publish of the value already there does not run the mirror hook" );
        chHook.reg_write( val( 6 ) );
        check( hookMirror.wakes == 2 && hookMirror.value == 6, "reg_write() runs the mirror hook on a change" );
        check( hookCmd.wakes == 2, "reg_write() does not run the command hook" );
        chHook.reg_write( val( 6 ) );
        check( hookMirror.wakes == 2, "reg_write() of the value already there does not run the mirror hook" );
        chHook.write( val( 7 ) );
        check( hookCmd.wakes == 2 && hookMirror.wakes == 2, "write() runs neither hook" );
        wait( 1, SC_NS );
        check( hookStatus.wakes == 1 && hookStatus.value == 7, "with the hooks set, reg_read() still wakes with write()'s value" );

        std::printf( "failures=%d\n", failures );
        sc_stop();
    }
};

int sc_main( int, char *[] )
{
    probe p( "probe" );
    sc_start();
    return failures == 0 ? 0 : 1;
}
"""

FAILURES = []


def check(condition, message):
    print(f"  {'PASS' if condition else 'FAIL'}: {message}")
    if not condition:
        FAILURES.append(message)


def test_external_reg_channel():
    tmpdir = tempfile.mkdtemp(prefix='a2c_external_reg_channel_')
    try:
        binPath = buildProbe(tmpdir, PROBE_SRC)
        if not os.path.isfile(binPath):
            check(False, f"external_reg_channel probe must build and link: {binPath}")
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
    print("TESTING EXTERNAL_REG CHANNEL LEGS")
    print("=" * 72)
    test_external_reg_channel()
    if FAILURES:
        print(f"\nRESULT: {len(FAILURES)} check(s) FAILED")
        sys.exit(1)
    print("\nRESULT: all external_reg channel checks passed")
    sys.exit(0)
