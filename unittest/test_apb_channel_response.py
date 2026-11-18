#!/usr/bin/env python3
"""apb_channel keeps posted writes posted and carries PSLVERR on request.

A plain request() write is posted: reqReceive() acknowledges it, and the
requester may issue its next request at once. A completer such as
registerHandler still calls complete() for every write. That call belongs to
the write already acknowledged, so it must not complete the read the requester
has issued since. The probe's completer waits 1 ns before completing each write,
so the read is already pending when the write's complete() arrives; the read
must still return the completer's read data, not the write data.

requestWithResponse() and the requestNonBlockingWithResponse() /
waitCompleteWithResponse() pair are not posted: each waits for complete() and
returns its PSLVERR, for writes and reads. receivedWantsResponse() tells the
completer which kind it received.
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
#include <cstdint>
#include <format>
#include <iostream>
#include <string>

struct addrSt {
    static constexpr unsigned _bitWidth = 32;
    static const char* getValueType() { return ""; }
    std::uint64_t getStructValue() const { return value; }
    std::uint64_t _getAddress() const { return value; }
    std::string prt( bool = false ) const { return std::format( "addr:0x{:x}", value ); }
    bool operator==( const addrSt& o ) const { return value == o.value; }
    std::uint32_t value = 0;
};

struct dataSt {
    static constexpr unsigned _bitWidth = 32;
    static const char* getValueType() { return ""; }
    std::uint64_t getStructValue() const { return value; }
    std::uint64_t _getData() const { return value; }
    void _setData( std::uint32_t v ) { value = v; }
    std::string prt( bool = false ) const { return std::format( "data:0x{:x}", value ); }
    bool operator==( const dataSt& o ) const { return value == o.value; }
    std::uint32_t value = 0;
};

static int g_failures = 0;
static void check( bool ok, const std::string& what )
{
    std::cout << ( ok ? "PASS: " : "FAIL: " ) << what << "\\n";
    if (!ok) ++g_failures;
}

static constexpr std::uint32_t READ_DATA = 0x1234;
static constexpr std::uint32_t ERR_ADDR = 0xE0;

SC_MODULE( harness )
{
    apb_channel<addrSt, dataSt> chan;
    int received = 0;
    int wantsResponse = 0;

    SC_HAS_PROCESS( harness );
    harness( sc_module_name n ) : sc_module( n ), chan( "chan", "tb" )
    {
        SC_THREAD( requester );
        SC_THREAD( completer );
    }

    void completer()
    {
        while (true) {
            bool isWrite = false;
            addrSt addr;
            dataSt data;
            chan.reqReceive( isWrite, addr, data );
            ++received;
            if (chan.receivedWantsResponse()) ++wantsResponse;
            const bool err = addr.value == ERR_ADDR;
            if (isWrite) {
                // as registerHandler does, complete every write, here late
                wait( 1, SC_NS );
                chan.complete( data, err );
            } else {
                dataSt resp;
                resp.value = READ_DATA;
                chan.complete( resp, err );
            }
        }
    }

    void requester()
    {
        addrSt a;
        dataSt d;

        // posted write, then a read issued before the write's complete()
        a.value = 0x10; d.value = 0xdead;
        chan.request( true, a, d );
        check( sc_time_stamp() == SC_ZERO_TIME, "a posted write returns without waiting for complete()" );
        dataSt rd;
        a.value = 0x14;
        chan.request( false, a, rd );
        check( rd.value == READ_DATA,
               std::format( "the read after a posted write returns read data 0x{:x} (got 0x{:x})", READ_DATA, rd.value ) );

        // response-aware write and read, with and without PSLVERR
        a.value = ERR_ADDR; d.value = 0xbeef;
        const sc_time before = sc_time_stamp();
        check( chan.requestWithResponse( true, a, d ), "a response-aware write returns PSLVERR 1" );
        check( sc_time_stamp() > before, "a response-aware write waits for complete()" );
        a.value = 0x18;
        check( !chan.requestWithResponse( true, a, d ), "a response-aware write returns PSLVERR 0" );
        dataSt rd2;
        a.value = ERR_ADDR;
        check( chan.requestWithResponse( false, a, rd2 ), "a response-aware read returns PSLVERR 1" );
        check( rd2.value == READ_DATA, "a response-aware read returns its data" );

        // non-blocking response-aware pair, as a tee uses it
        a.value = ERR_ADDR; d.value = 0xcafe;
        chan.requestNonBlockingWithResponse( true, a, d );
        dataSt unused;
        check( chan.waitCompleteWithResponse( unused ), "the non-blocking pair returns a write's PSLVERR" );
        dataSt rd3;
        a.value = 0x1c;
        chan.requestNonBlockingWithResponse( false, a, rd3 );
        check( !chan.waitCompleteWithResponse( rd3 ) && rd3.value == READ_DATA,
               "the non-blocking pair returns a read's data and PSLVERR 0" );

        wait( 2, SC_NS );
        check( received == 7, std::format( "the completer received 7 requests (got {})", received ) );
        check( wantsResponse == 5, std::format( "receivedWantsResponse() is set on the 5 response-aware requests (got {})", wantsResponse ) );
        std::cout << "failures=" << g_failures << "\\n";
        sc_stop();
    }
};

int sc_main( int, char*[] )
{
    harness h( "h" );
    sc_start();
    return g_failures == 0 ? 0 : 1;
}
"""

EXPECTED_PASSES = 11

FAILURES = []


def check(condition, message):
    print(f"  {'PASS' if condition else 'FAIL'}: {message}")
    if not condition:
        FAILURES.append(message)


def test_apb_channel_response():
    scLibdir = os.environ.get('SYSTEMC_LIBDIR', '')
    tmpdir = tempfile.mkdtemp(prefix='a2c_apb_channel_response_')
    try:
        binPath = buildProbe(tmpdir, PROBE_SRC)
        if not os.path.isfile(binPath):
            check(False, f"apb_channel probe must build and link: {binPath}")
            return
        try:
            run = subprocess.run([binPath], capture_output=True, text=True, timeout=60,
                                 env=dict(os.environ, LD_LIBRARY_PATH=scLibdir))
        except subprocess.TimeoutExpired:
            check(False, "the apb_channel probe finishes within 60 s")
            return
        output = run.stdout + run.stderr
        check(run.returncode == 0, f"the probe exits with status 0 (got {run.returncode})")
        check(output.count('PASS: ') == EXPECTED_PASSES and 'failures=0' in output,
              f"all {EXPECTED_PASSES} channel checks pass")
        if FAILURES:
            print(output)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == '__main__':
    test_apb_channel_response()
    if FAILURES:
        print(f"\n  SOME TESTS FAILED ({len(FAILURES)})")
        sys.exit(1)
    print("\n  ALL TESTS PASSED!")
    sys.exit(0)
