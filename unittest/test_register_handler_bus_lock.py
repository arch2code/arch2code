#!/usr/bin/env python3
"""registerHandler takes the block's register lock around each bus access.

A block whose own threads change registers the bus reads gives its addressMap a
synchLock (setSynchLock) and takes it around those changes. registerHandler
then takes the same lock around each read and write, so a bus access cannot
fall between the parts of a block update, and tandem replays the order of the
two (keystone's FAC OP_STATUS: a poll raced the operation's completion, and the
two tandem copies read different values).

The probe's block thread takes the lock at 0 ns, changes the register at 5 ns
and releases it. The firmware reads at 1 ns. With the lock in the handler the
read waits and returns the new value; the same probe without setSynchLock reads
the old value, which is the run the test does second, as its control.
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
#include "addressMap.h"
#include "synchLock.h"
#include <cstdint>
#include <cstring>
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
    void _setData( std::uint64_t v ) { value = static_cast< std::uint32_t >( v ); }
    std::string prt( bool = false ) const { return std::format( "data:0x{:x}", value ); }
    bool operator==( const dataSt& o ) const { return value == o.value; }
    std::uint32_t value = 0;
};

struct plainReg : addressBase {
    std::uint32_t v = 0x0;
    void cpu_write( uint64_t, uint32_t val ) override { v = val; }
    uint32_t cpu_read( uint64_t ) override { return v; }
};

SC_MODULE( harness )
{
    apb_channel<addrSt, dataSt> chan;
    sc_port<apb_in_if<addrSt, dataSt>> regsIn;
    logBlock log_;
    addressMap regs;
    plainReg reg;
    std::shared_ptr<synchLock<>> lock;
    bool useLock;

    SC_HAS_PROCESS( harness );
    harness( sc_module_name n, bool useLock_ )
      : sc_module( n ), chan( "chan", "tb" ), regsIn( "regsIn" ), log_( "harness" ), regs( log_ ),
        useLock( useLock_ )
    {
        regsIn( chan );
        regs.addRegister( 0x0, 4, "reg", &reg );
        lock = synchLockFactory<>::getInstance().newLock( std::string( name() ), "regs" );
        if (useLock) regs.setSynchLock( lock );
        SC_THREAD( handler );
        SC_THREAD( block );
        SC_THREAD( firmware );
    }

    void handler() { registerHandler< addrSt, dataSt >( regs, regsIn, 0xff ); }

    void block()
    {
        lock->lock( 1 );
        wait( 5, SC_NS );
        reg.v = 0xd0e;
        lock->unlock();
    }

    void firmware()
    {
        wait( 1, SC_NS );
        addrSt a;
        dataSt d;
        chan.request( false, a, d );
        std::cout << std::format( "readData=0x{:x} at {}\\n", d.value, sc_time_stamp().to_string() );
        sc_stop();
    }
};

int sc_main( int argc, char* argv[] )
{
    const bool useLock = argc > 1 && std::string( argv[1] ) == "locked";
    harness h( "h", useLock );
    sc_start();
    return 0;
}
"""

FAILURES = []


def check(condition, message):
    print(f"  {'PASS' if condition else 'FAIL'}: {message}")
    if not condition:
        FAILURES.append(message)


def test_register_handler_bus_lock():
    scLibdir = os.environ.get('SYSTEMC_LIBDIR', '')
    tmpdir = tempfile.mkdtemp(prefix='a2c_reg_bus_lock_')
    try:
        binPath = buildProbe(tmpdir, PROBE_SRC)
        if not os.path.isfile(binPath):
            check(False, f"probe must build and link: {binPath}")
            return
        out = {}
        for mode in ('locked', 'unlocked'):
            run = subprocess.run([binPath, mode], capture_output=True, text=True, timeout=60,
                                 env=dict(os.environ, LD_LIBRARY_PATH=scLibdir))
            out[mode] = run.stdout + run.stderr
            check(run.returncode == 0, f"{mode} probe exits with status 0 (got {run.returncode})")
        seen = {m: [l for l in out[m].splitlines() if l.startswith('readData=')] for m in out}
        check('readData=0xd0e' in out['locked'],
              f"with setSynchLock the read waits for the block's update ({seen['locked']})")
        check('readData=0x0 ' in out['unlocked'],
              f"without it the read lands inside the update and returns the old value "
              f"({seen['unlocked']})")
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == '__main__':
    test_register_handler_bus_lock()
    if FAILURES:
        print(f"\n  SOME TESTS FAILED ({len(FAILURES)})")
        sys.exit(1)
    print("\n  ALL TESTS PASSED!")
    sys.exit(0)
