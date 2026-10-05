#!/usr/bin/env python3
"""external_reg_dst_bfm delivers every command to the RTL, in order.

The dst BFM turns each reg_write_cmd from the model into a one-cycle `write`
pulse on the HDL side, then waits a further clock for the registered rdata.
Firmware may write the same register again before those two clocks are over.
The channel's read() only sees a command issued while a reader is waiting, so
the BFM keeps a reader on the channel at all times and queues what it reads.
Each command then reaches the RTL as its own pulse, in the order issued.

The probe drives back-to-back APB writes through the shipped registerHandler
and hwRegisterIf into the BFM, with a stub RTL register behind it that logs
every pulse. Two and three writes must each produce that many pulses with the
written values, leave the register holding the last one, and read it back.

A reset discards what the BFM has queued. In the reset case three writes are
queued and rst_n asserts for two clocks right after the first strobe. The RTL
must see only that first pulse and leave reset holding its reset value, and
firmware must read that value back. In the in-reset case rst_n starts low and
firmware writes twice before it rises, the second time in the last reset
cycle. Neither write may reach the RTL.
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
#include "hwRegister.h"
#include "external_reg_channel.h"
#include "external_reg_bfm.h"
#include <cstdint>
#include <cstdio>
#include <format>
#include <string>
#include <vector>

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
    std::uint32_t _getData() const { return value; }
    void _setData( std::uint32_t v ) { value = v; }
    std::string prt( bool = false ) const { return std::format( "data:0x{:x}", value ); }
    bool operator==( const dataSt& o ) const { return value == o.value; }
    std::uint32_t value = 0;
};

// A 32-bit register payload in a plain word, like a generated struct.
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
    std::string prt( bool = false ) const { return std::format( "0x{:08x}", w ); }
    bool operator==( const regSt& o ) const { return w == o.w; }
};

using regPort = external_reg_out<regSt>;

// CPU, APB channel, registerHandler and hwRegisterIf, up to the register's
// driver port. The CPU issues `count` back-to-back writes, then reads back.
// With inReset it writes at 30 ns and 92 ns instead, while rst_n is low.
SC_MODULE( driverSide )
{
    apb_channel<addrSt, dataSt> bus;
    sc_port<apb_out_if<addrSt, dataSt>> cpu;
    sc_port<apb_in_if<addrSt, dataSt>> apbIn;
    regPort port;
    logBlock log_;
    addressMap regs;
    hwRegisterIf<regSt, regPort, 4, false> ext;
    int count;
    bool inReset;
    std::uint32_t readBack = 0;
    bool done = false;

    SC_HAS_PROCESS( driverSide );
    driverSide( sc_module_name n, int count_, bool inReset_ )
      : sc_module( n ), bus( "bus", "tb" ), cpu( "cpu" ), apbIn( "apbIn" ), port( "port" ),
        log_( name() ), regs( log_ ), ext( &port ), count( count_ ), inReset( inReset_ )
    {
        cpu( bus );
        apbIn( bus );
        regs.addRegister( 0, 4, "ext", &ext );
        SC_THREAD( handler );
        SC_THREAD( drive );
    }

    void handler() { registerHandler( regs, apbIn, 0xff ); }

    void access( bool write, std::uint32_t &value )
    {
        addrSt a;
        dataSt d;
        d.value = value;
        cpu->request( write, a, d );
        value = d.value;
    }

    void drive()
    {
        if (inReset) {
            std::uint32_t v = 0x11111111u;
            wait( 30, SC_NS );
            access( true, v );
            v = 0x22222222u;
            wait( sc_time( 92, SC_NS ) - sc_time_stamp() );
            access( true, v );
        } else {
            wait( 100, SC_NS );
        }
        for (int i = 0; !inReset && i < count; i++) {
            std::uint32_t v = 0x11111111u * (i + 1);
            access( true, v );
        }
        wait( 300, SC_NS );
        access( false, readBack );
        done = true;
    }
};

// A stub RTL register: always_ff if (!rst_n) q <= 0; else if (|write) q <= wdata; assign rdata = q.
SC_MODULE( rtlOwner )
{
    sc_port<external_reg_hdl_if<sc_bv<32>>> hdl;
    sc_in<bool> clk;
    sc_in<bool> rst_n;
    sc_bv<32> q;
    std::vector<std::uint32_t> pulses;
    SC_HAS_PROCESS( rtlOwner );
    rtlOwner( sc_module_name n ) : sc_module( n ), hdl( "hdl" ), clk( "clk" ), rst_n( "rst_n" ) { SC_THREAD( run ); }
    void run()
    {
        while (true) {
            wait( clk.posedge_event() );
            if (!rst_n) {
                q = 0;
            } else if (hdl->write.read().or_reduce()) {
                q = hdl->wdata.read();
                pulses.push_back( (std::uint32_t)q.to_uint64() );
            }
            hdl->rdata = q;
        }
    }
};

struct hdlIf : external_reg_hdl_if<sc_bv<32>> {};

// Asserts reset for two clocks from the edge that samples the first strobe.
SC_MODULE( resetter )
{
    sc_port<external_reg_hdl_if<sc_bv<32>>> hdl;
    sc_in<bool> clk;
    sc_out<bool> rst_n;
    SC_HAS_PROCESS( resetter );
    resetter( sc_module_name n ) : sc_module( n ), hdl( "hdl" ), clk( "clk" ), rst_n( "rst_n" ) { SC_THREAD( run ); }
    void run()
    {
        do { wait( clk.posedge_event() ); } while (!hdl->write.read().or_reduce());
        rst_n = false;
        wait( clk.posedge_event() );
        wait( clk.posedge_event() );
        rst_n = true;
    }
};

// Releases reset at 95 ns, between the 90 ns and 100 ns clock edges.
SC_MODULE( releaser )
{
    sc_out<bool> rst_n;
    SC_HAS_PROCESS( releaser );
    releaser( sc_module_name n ) : sc_module( n ), rst_n( "rst_n" ) { SC_THREAD( run ); }
    void run() { wait( 95, SC_NS ); rst_n = true; }
};

static int failures = 0;

static void expect( bool ok, const std::string &what )
{
    std::printf( "%s: %s\\n", ok ? "PASS" : "FAIL", what.c_str() );
    if (!ok) { failures++; }
}

int sc_main( int argc, char *argv[] )
{
    int count = std::stoi( argv[1] );
    std::string mode = argc > 2 ? argv[2] : "";
    bool withReset = mode == "reset";
    bool inReset = mode == "inReset";
    driverSide drv( "drv", count, inReset );
    external_reg_channel<regSt> ch( "ch", "tb" );
    sc_clock clk( "clk", 10, SC_NS );
    sc_signal<bool> rst_n( "rst_n", !inReset );
    hdlIf hdl;
    external_reg_dst_bfm<regSt, sc_bv<32>> bfm( "bfm" );
    rtlOwner rtl( "rtl" );
    drv.port( ch );
    bfm.if_p( ch );
    bfm.hdl_if_p( hdl );
    bfm.clk( clk );
    bfm.rst_n( rst_n );
    rtl.hdl( hdl );
    rtl.clk( clk );
    rtl.rst_n( rst_n );
    resetter rst( "rst" );
    rst.hdl( hdl );
    rst.clk( clk );
    sc_signal<bool> unusedRst( "unusedRst", true );
    if (withReset) { rst.rst_n( rst_n ); } else { rst.rst_n( unusedRst ); }
    releaser rel( "rel" );
    sc_signal<bool> unusedRel( "unusedRel", true );
    if (inReset) { rel.rst_n( rst_n ); } else { rel.rst_n( unusedRel ); }
    sc_start( 1, SC_US );

    // after the reset only the first write has reached the RTL, and reset clears it;
    // a write issued during reset never reaches it
    int pulses = inReset ? 0 : withReset ? 1 : count;
    std::uint32_t last = (withReset || inReset) ? 0 : 0x11111111u * count;
    std::string got;
    for (auto p : rtl.pulses) { got += std::format( " 0x{:08x}", p ); }
    bool inOrder = (int)rtl.pulses.size() == pulses;
    for (int i = 0; inOrder && i < pulses; i++) {
        inOrder = rtl.pulses[i] == 0x11111111u * (i + 1);
    }
    expect( drv.done, "firmware accesses complete" );
    expect( inOrder, std::format( "the RTL sees {} write pulses in order (got{})", pulses, got ) );
    expect( (std::uint32_t)rtl.q.to_uint64() == last, std::format( "the RTL register holds 0x{:08x}", last ) );
    expect( drv.readBack == last, std::format( "firmware reads 0x{:08x} back (got 0x{:08x})", last, drv.readBack ) );
    std::printf( "failures=%d\\n", failures );
    return failures ? 1 : 0;
}
"""

CASES = (('1',), ('2',), ('3',), ('3', 'reset'), ('2', 'inReset'))

LABELS = {'reset': " with a reset after the first", 'inReset': " while rst_n is low"}

FAILURES = []


def check(condition, message):
    print(f"  {'PASS' if condition else 'FAIL'}: {message}")
    if not condition:
        FAILURES.append(message)


def test_external_reg_dst_bfm():
    scLibdir = os.environ.get('SYSTEMC_LIBDIR', '')
    tmpdir = tempfile.mkdtemp(prefix='a2c_external_reg_dst_bfm_')
    try:
        binPath = buildProbe(tmpdir, PROBE_SRC)
        if not os.path.isfile(binPath):
            check(False, f"external_reg_dst_bfm probe must build and link: {binPath}")
            return
        for case in CASES:
            label = f"{case[0]} writes" + (LABELS[case[1]] if len(case) > 1 else "")
            try:
                run = subprocess.run([binPath, *case], capture_output=True, text=True, timeout=60,
                                     env=dict(os.environ, LD_LIBRARY_PATH=scLibdir))
            except subprocess.TimeoutExpired:
                check(False, f"{label} finish within 60 s")
                continue
            output = run.stdout + run.stderr
            before = len(FAILURES)
            check(run.returncode == 0, f"{label}: exits with status 0 (got {run.returncode})")
            check(output.count('PASS: ') == 4 and 'failures=0' in output, f"{label}: all four checks pass")
            if len(FAILURES) > before:
                print(output)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == '__main__':
    test_external_reg_dst_bfm()
    if FAILURES:
        print(f"\n  SOME TESTS FAILED ({len(FAILURES)})")
        sys.exit(1)
    print("\n  ALL TESTS PASSED!")
    sys.exit(0)
