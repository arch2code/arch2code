#!/usr/bin/env python3
"""Channels whose setTimed is fixed at construction take no delay and say so once.

Every channel passes interfaceBase a timedDelayRule. status and memory
channels pass TIMED_DELAY_FIXED_TIMING and never apply setTimed. rdy_vld and
axi4_stream channels take a channelBackpressure constructor argument, and
BACKPRESSURE_NONE maps to TIMED_DELAY_NO_BACKPRESSURE. push_ack passes
TIMED_DELAY_APPLIES. Both ends of a channel call
setTimed, so the probe calls it twice on each channel and expects:

- a BACKPRESSURE_ALLOWED rdy_vld channel and a push_ack channel deliver after
  the delay;
- a BACKPRESSURE_NONE rdy_vld channel, a BACKPRESSURE_NONE axi4_stream
  channel, a status channel and a memory channel deliver at time zero, and
  each logs the dropped delay exactly once;
- setTimed(0) logs nothing.

The probe also instantiates the rdy_vld and axi4_stream thunker constructors,
which take the same argument.
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
#include "rdy_vld_channel.h"
#include "status_channel.h"
#include "memory_channel.h"
#include "axi4_stream_channel.h"
#include "push_ack_channel.h"
#include "rdy_vld_port_thunker.h"
#include "axi4_stream_port_thunker.h"
#include <cstdint>
#include <cstdio>
#include <format>
#include <string>

struct wordSt {
    std::uint64_t w = 0;
    static constexpr std::uint16_t _bitWidth = 64;
    static constexpr std::uint16_t _byteWidth = 8;
    typedef std::uint64_t _packedSt;
    static const char* getValueType() { return ""; }
    std::uint64_t getStructValue() const { return w; }
    void pack( _packedSt& v ) const { v = w; }
    void unpack( const _packedSt& v ) { w = v; }
    sc_bv<64> sc_pack() const { sc_bv<64> p; p = w; return p; }
    void sc_unpack( sc_bv<64> p ) { w = p.to_uint64(); }
    std::string prt( bool = false ) const { return std::format( "0x{:016x}", w ); }
    bool operator==( const wordSt& o ) const { return w == o.w; }
};

using streamInfo = axi4StreamInfoSt<wordSt, wordSt, wordSt>;

template class rdy_vld_port_thunker<wordSt, wordSt>;
template class axi4_stream_port_thunker<wordSt, wordSt, wordSt, wordSt, wordSt, wordSt>;

SC_MODULE( probe )
{
    rdy_vld_channel<wordSt> allowedCh;
    rdy_vld_channel<wordSt> noneCh;
    axi4_stream_channel<wordSt, wordSt, wordSt> streamCh;
    status_channel<wordSt> statCh;
    memory_channel<wordSt, wordSt> memCh;
    push_ack_channel<wordSt> pushCh;
    rdy_vld_out<wordSt> allowedOut;
    rdy_vld_in<wordSt> allowedIn;
    rdy_vld_out<wordSt> noneOut;
    rdy_vld_in<wordSt> noneIn;
    axi4_stream_out<wordSt, wordSt, wordSt> streamOut;
    axi4_stream_in<wordSt, wordSt, wordSt> streamIn;
    status_out<wordSt> statOut;
    status_in<wordSt> statIn;
    memory_out<wordSt, wordSt> memOut;
    memory_in<wordSt, wordSt> memIn;
    push_ack_out<wordSt> pushOut;
    push_ack_in<wordSt> pushIn;
    sc_time allowedSeen, noneSeen, streamSeen, statSeen, memSeen, pushSeen;
    int failures = 0;

    SC_HAS_PROCESS( probe );
    probe( sc_module_name n )
      : sc_module( n ),
        allowedCh( "allowedCh", "tb", BACKPRESSURE_ALLOWED ), noneCh( "noneCh", "tb", BACKPRESSURE_NONE ),
        streamCh( "streamCh", "tb", BACKPRESSURE_NONE ), statCh( "statCh", "tb" ), memCh( "memCh", "tb" ), pushCh( "pushCh", "tb" ),
        allowedOut( "allowedOut" ), allowedIn( "allowedIn" ), noneOut( "noneOut" ), noneIn( "noneIn" ),
        streamOut( "streamOut" ), streamIn( "streamIn" ), statOut( "statOut" ), statIn( "statIn" ),
        memOut( "memOut" ), memIn( "memIn" ), pushOut( "pushOut" ), pushIn( "pushIn" )
    {
        allowedOut( allowedCh ); allowedIn( allowedCh );
        noneOut( noneCh ); noneIn( noneCh );
        streamOut( streamCh ); streamIn( streamCh );
        statOut( statCh ); statIn( statCh );
        memOut( memCh ); memIn( memCh );
        pushOut( pushCh ); pushIn( pushCh );
        for (int end = 0; end < 2; end++) {
            allowedCh.setTimed( 10, TIMED_DELAY_FIXED_INIT );
            noneCh.setTimed( 0, TIMED_DELAY_FIXED_INIT );
            noneCh.setTimed( 10, TIMED_DELAY_FIXED_INIT );
            streamCh.setTimed( 10, TIMED_DELAY_FIXED_INIT );
            statCh.setTimed( 10, TIMED_DELAY_FIXED_INIT );
            memCh.setTimed( 10, TIMED_DELAY_FIXED_INIT );
            pushCh.setTimed( 10, TIMED_DELAY_FIXED_INIT );
        }
        SC_THREAD( writeAllowed ); SC_THREAD( readAllowed );
        SC_THREAD( writeNone ); SC_THREAD( readNone );
        SC_THREAD( sendStream ); SC_THREAD( receiveStream );
        SC_THREAD( writeStat ); SC_THREAD( readStat );
        SC_THREAD( request ); SC_THREAD( receive );
        SC_THREAD( push ); SC_THREAD( pushReceive );
        SC_THREAD( report );
    }

    void writeAllowed() { wordSt v; v.w = 1; allowedOut->write( v ); }
    void readAllowed() { wordSt v; allowedIn->read( v ); allowedSeen = sc_time_stamp(); }
    void writeNone() { wordSt v; v.w = 2; noneOut->write( v ); }
    void readNone() { wordSt v; noneIn->read( v ); noneSeen = sc_time_stamp(); }
    void sendStream() { streamInfo i; i.tdata.w = 5; streamOut->sendInfo( i, std::nullopt ); }
    void receiveStream() { streamInfo i; streamIn->receiveInfo( i ); streamSeen = sc_time_stamp(); }
    void writeStat() { wordSt v; v.w = 6; statOut->write( v ); }
    void readStat() { statIn->read(); statSeen = sc_time_stamp(); }
    void request() { wordSt a, d; a.w = 4; d.w = 3; memOut->request( true, a, d ); }
    void receive() { bool isWrite; wordSt a, d; memIn->reqReceive( isWrite, a, d ); memSeen = sc_time_stamp(); }
    void push() { wordSt v; v.w = 7; pushOut->push( v ); }
    void pushReceive() { wordSt v; pushIn->pushReceive( v ); pushSeen = sc_time_stamp(); pushIn->ack(); }

    void expect( bool ok, const std::string &what )
    {
        std::printf( "%s: %s\\n", ok ? "PASS" : "FAIL", what.c_str() );
        if (!ok) { failures++; }
    }

    void report()
    {
        wait( 100, SC_NS );
        expect( allowedSeen == sc_time( 10, SC_NS ), std::format( "BACKPRESSURE_ALLOWED rdy_vld delivers at 10 ns (got {})", allowedSeen.to_string() ) );
        expect( noneSeen == SC_ZERO_TIME, std::format( "BACKPRESSURE_NONE rdy_vld delivers at 0 s (got {})", noneSeen.to_string() ) );
        expect( streamSeen == SC_ZERO_TIME, std::format( "BACKPRESSURE_NONE axi4_stream delivers at 0 s (got {})", streamSeen.to_string() ) );
        expect( statSeen == SC_ZERO_TIME, std::format( "status delivers at 0 s (got {})", statSeen.to_string() ) );
        expect( memSeen == SC_ZERO_TIME, std::format( "memory delivers at 0 s (got {})", memSeen.to_string() ) );
        expect( pushSeen == sc_time( 10, SC_NS ), std::format( "push_ack delivers at 10 ns (got {})", pushSeen.to_string() ) );
        std::printf( "failures=%d\\n", failures );
        sc_stop();
    }
};

int sc_main( int, char *[] )
{
    // A channel reads the default verbosity when it is built, as sc_main does in a real run.
    logging::GetInstance().setDefaultVerbosity( VERBOSITY_MEDIUM );
    probe p( "p" );
    sc_start( 1, SC_US );
    return p.failures ? 1 : 0;
}
"""

FAILURES = []


def check(condition, message):
    print(f"  {'PASS' if condition else 'FAIL'}: {message}")
    if not condition:
        FAILURES.append(message)


def test_set_timed_ignore_runtime():
    scLibdir = os.environ.get('SYSTEMC_LIBDIR', '')
    tmpdir = tempfile.mkdtemp(prefix='a2c_set_timed_fixed_')
    try:
        binPath = buildProbe(tmpdir, PROBE_SRC)
        if not os.path.isfile(binPath):
            check(False, f"setTimed probe must build and link: {binPath}")
            return
        try:
            run = subprocess.run([binPath], capture_output=True, text=True, timeout=60,
                                 env=dict(os.environ, LD_LIBRARY_PATH=scLibdir))
        except subprocess.TimeoutExpired:
            check(False, "probe finishes within 60 s")
            return
        output = run.stdout + run.stderr
        before = len(FAILURES)
        check(run.returncode == 0, f"probe exits with status 0 (got {run.returncode})")
        check(output.count('PASS: ') == 6 and 'failures=0' in output, "all six timing checks pass")
        for channel, reason in [('noneCh', 'no backpressure'), ('streamChtx', 'no backpressure'),
                                ('statCh', 'fixed timing'), ('memCh_req', 'fixed timing')]:
            line = f'{channel}:setTimed(10ns) ignored: {reason}'
            check(output.count(line) == 1, f"{channel} logs {reason!r} once, though both ends set the delay")
        check(output.count('ignored:') == 4, "no other channel logs a dropped delay")
        check('setTimed(0ns)' not in output, "setTimed(0) logs nothing")
        if len(FAILURES) > before:
            print(output)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == '__main__':
    test_set_timed_ignore_runtime()
    if FAILURES:
        print(f"\n  SOME TESTS FAILED ({len(FAILURES)})")
        sys.exit(1)
    print("\n  ALL TESTS PASSED!")
    sys.exit(0)
