// Firmware access modes of hwMemory and hwMemoryPort: an ro memory drops a
// cpu_write and a wo memory returns 0 from cpu_read, each logged, while the
// block-side backdoor and an rw memory are unaffected. Prints one
// "checks:N failures:M" line.
#include "systemc.h"
#include "hwMemory.h"
#include "logging.h"
#include <iostream>

struct rowSt {
    static constexpr uint16_t _bitWidth = 32;
    static constexpr uint16_t _byteWidth = 4;
    typedef uint32_t _packedSt;
    uint32_t v = 0;
    sc_bv<32> sc_pack(void) const { sc_bv<32> b = v; return b; }
    void sc_unpack(sc_bv<32> b) { v = b.to_uint(); }
    std::string prt(bool all = false) const { return std::to_string(v); }
};

struct addrSt {
    static constexpr uint16_t _bitWidth = 2;
    static constexpr uint16_t _byteWidth = 1;
    typedef uint8_t _packedSt;
    uint8_t a = 0;
    void unpack(_packedSt p) { a = p; }
};

// q_assert.cpp needs the module build; an assert here is a harness failure.
void q_assert_body(bool dump, const char *file, int line, std::string ctx, std::string msg, std::string ctx_msg) {
    std::cout << "Q_ASSERT " << file << ":" << line << " " << msg << '\n';
    std::abort();
}

static int checks = 0, failures = 0;
static void check(bool ok, const char *what) {
    checks++;
    if (!ok) {
        failures++;
        std::cout << "FAIL: " << what << '\n';
    }
}

// hwMemoryPort's rw paths go through its port; the ro write and wo read
// return before touching it, so an unbound port suffices.
SC_MODULE(portHarness) {
    memory_out<addrSt, rowSt> port;
    hwMemoryPort<addrSt, rowSt> roPort;
    hwMemoryPort<addrSt, rowSt> woPort;
    SC_CTOR(portHarness)
        : port("port"),
          roPort(port, HWMEMORYFWACCESS_RO, "top.roPort"),
          woPort(port, HWMEMORYFWACCESS_WO, "top.woPort") {}
};

int sc_main(int argc, char *argv[]) {
    memories mems;
    hwMemory<rowSt> ro("top", "roMem", mems, 4, HWMEMORYTYPE_NORMAL, HWMEMORYFWACCESS_RO);
    hwMemory<rowSt> wo("top", "woMem", mems, 4, HWMEMORYTYPE_NORMAL, HWMEMORYFWACCESS_WO);
    hwMemory<rowSt> rw("top", "rwMem", mems, 4);

    ro[1].v = 0x11;
    ro.cpu_write(4, 0x99);
    check(ro[1].v == 0x11, "ro cpu_write leaves the row unchanged");
    check(ro.cpu_read(4) == 0x11, "ro cpu_read returns the row");

    wo.cpu_write(8, 0x55);
    check(wo[2].v == 0x55, "wo cpu_write stores the row");
    check(wo.cpu_read(8) == 0, "wo cpu_read returns 0");

    rw.cpu_write(12, 0x77);
    check(rw[3].v == 0x77, "rw cpu_write stores the row");
    check(rw.cpu_read(12) == 0x77, "rw cpu_read returns the row");

    portHarness harness("harness");
    harness.roPort.cpu_write(4, 0x99);
    check(harness.woPort.cpu_read(8) == 0, "wo hwMemoryPort cpu_read returns 0");

    std::cout << "checks:" << checks << " failures:" << failures << '\n';
    return 0;
}
