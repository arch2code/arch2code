// AHB-Lite BFM and channel runtime check, built and run by unittest/test_ahb_bfm.py.
//
// The scenarios share one pin-level protocol monitor (ahbPinMonitor) that
// samples the pins at every clock edge:
//
//   loopback     model manager -> ahb_dst_bfm -> pins -> ahb_src_bfm -> model subordinate
//   srcBfm       scripted pin manager (IDLE, BUSY, bursts) -> ahb_src_bfm -> model subordinate
//   dstBfm       model manager -> ahb_dst_bfm -> scripted pin subordinate
//   slowMgr      slow single-thread model manager (locked and wrapping bursts,
//                an INCR ending at a 1KB boundary) -> ahb_dst_bfm -> scripted pin subordinate
//   selfTest     scripted illegal pin traffic, to show the monitor reports each rule
//   errCancel    an ERROR inside a burst, after which the manager cancels the burst
//   errContinue  the same ERROR, after which the manager finishes the burst
//   docWrites    the documented two-thread manager -> ahb_dst_bfm -> zero-wait pin subordinate
//   docMixed     the same with two writes then two reads
//
// `ahb_bfm_runtime resetAssert` runs only resetMidTransfer, reset during a
// write's wait states, which ends the simulation with an assert.
//
// The script tables below are the pinned expectations. Every check goes through
// expect(), and the summary line carries the check count so a skipped scenario
// shows up as a changed total.
#include "ahb_bfm.h"
#include <cstdio>
#include <cstring>
#include <format>
#include <map>
#include <new>
#include <string>
#include <systemc.h>
#include <vector>

template <unsigned W>
struct pl
{
    static constexpr unsigned _bitWidth = W;
    static constexpr unsigned _byteWidth = (W + 7) / 8;
    static constexpr unsigned _packedSize = (_byteWidth + 7) >> 3;
    typedef uint64_t _packedSt[_packedSize];
    uint64_t value = 0;
    void pack(_packedSt &v) const { v[0] = value; }
    void unpack(const _packedSt &v) { value = v[0]; }
    static const char *getValueType() { return ""; }
    uint64_t getStructValue() const { return value; }
    std::string prt(bool = false) const { return std::to_string(value); }
    bool operator==(const pl &o) const { return value == o.value; }
    sc_bv<W> sc_pack() const { return sc_bv<W>(value); }
    void sc_unpack(const sc_bv<W> &v) { value = v.to_uint64(); }
};
using A = pl<32>;
using D = pl<32>;
using VA = sc_bv<32>;
using VD = sc_bv<32>;
using pins_t = ahb_hdl_if<VA, VD>;

static int g_checks = 0, g_fail = 0;
static void expect(const std::string &what, uint64_t got, uint64_t want)
{
    ++g_checks;
    if (got != want) {
        ++g_fail;
        std::printf("FAIL %s got 0x%llx want 0x%llx at %s\n", what.c_str(), (unsigned long long)got,
                    (unsigned long long)want, sc_time_stamp().to_string().c_str());
    }
}

// Every transfer is 4 bytes with these protection bits.
static constexpr _ahbSizeT SIZE = 2;
static constexpr _ahbProtT PROT = 0x3;

static bool isXferTrans(unsigned trans) { return trans == AHBTRANS_NONSEQ || trans == AHBTRANS_SEQ; }

static unsigned burstBeats(unsigned burst)
{
    switch (burst) {
        case AHBBURST_SINGLE: return 1;
        case AHBBURST_INCR: return 0;
        case AHBBURST_WRAP4:
        case AHBBURST_INCR4: return 4;
        case AHBBURST_WRAP8:
        case AHBBURST_INCR8: return 8;
        default: return 16;
    }
}

// The address of the beat after `addr` in a burst.
static bool isWrapBurst(unsigned burst)
{
    return burst == AHBBURST_WRAP4 || burst == AHBBURST_WRAP8 || burst == AHBBURST_WRAP16;
}

static uint64_t nextAddr(uint64_t addr, unsigned size, unsigned burst)
{
    const uint64_t bytes = 1u << size;
    if (!isWrapBurst(burst)) return addr + bytes;
    const uint64_t span = burstBeats(burst) * bytes;
    const uint64_t base = addr & ~(span - 1);
    return base + ((addr - base + bytes) % span);
}

// One address phase. For a transfer, `data` is the write data or the expected
// read data, `waits` is the number of hready-low cycles the subordinate adds,
// and `error` makes the subordinate answer ERROR.
struct beat
{
    uint32_t addr = 0;
    bool write = false;
    uint32_t data = 0;
    _ahbTransT trans = AHBTRANS_IDLE;
    _ahbBurstT burst = AHBBURST_SINGLE;
    unsigned waits = 0;
    bool error = false;
    bool sel = true;
    bool lock = false;
};

static bool isXfer(const beat &b) { return b.sel && isXferTrans(b.trans); }

// Cycles the data phase of this address phase occupies: IDLE and BUSY take one.
static unsigned dataPhaseCycles(const beat &b) { return isXfer(b) ? 1 + b.waits + (b.error ? 1 : 0) : 1; }

static beat wr(uint32_t a, uint32_t d, _ahbTransT t, _ahbBurstT bu, unsigned waits = 0, bool err = false)
{
    return beat{a, true, d, t, bu, waits, err, true};
}
static beat rd(uint32_t a, uint32_t d, _ahbTransT t, _ahbBurstT bu, unsigned waits = 0, bool err = false)
{
    return beat{a, false, d, t, bu, waits, err, true};
}
static beat busy(uint32_t a, bool w, _ahbBurstT bu) { return beat{a, w, 0, AHBTRANS_BUSY, bu, 0, false, true}; }
static beat idle(bool sel) { return beat{0, false, 0, AHBTRANS_IDLE, AHBBURST_SINGLE, 0, false, sel}; }

// 23 transfers: single write and read, INCR4 write and read, WRAP4 write and
// read (0x238 -> 0x23c -> 0x230 -> 0x234), two back-to-back ERROR responses
// (the second after two wait states), a read after the ERROR, and a write that
// holds the bus for three wait states in front of a read of the same address.
static std::vector<beat> xferScript()
{
    return {
        wr(0x100, 0x10000001, AHBTRANS_NONSEQ, AHBBURST_SINGLE),
        rd(0x100, 0x10000001, AHBTRANS_NONSEQ, AHBBURST_SINGLE, 1),
        wr(0x200, 0x20000000, AHBTRANS_NONSEQ, AHBBURST_INCR4),
        wr(0x204, 0x20000001, AHBTRANS_SEQ, AHBBURST_INCR4, 2),
        wr(0x208, 0x20000002, AHBTRANS_SEQ, AHBBURST_INCR4),
        wr(0x20c, 0x20000003, AHBTRANS_SEQ, AHBBURST_INCR4),
        rd(0x200, 0x20000000, AHBTRANS_NONSEQ, AHBBURST_INCR4),
        rd(0x204, 0x20000001, AHBTRANS_SEQ, AHBBURST_INCR4),
        rd(0x208, 0x20000002, AHBTRANS_SEQ, AHBBURST_INCR4, 1),
        rd(0x20c, 0x20000003, AHBTRANS_SEQ, AHBBURST_INCR4),
        wr(0x238, 0x30000000, AHBTRANS_NONSEQ, AHBBURST_WRAP4),
        wr(0x23c, 0x30000001, AHBTRANS_SEQ, AHBBURST_WRAP4, 1),
        wr(0x230, 0x30000002, AHBTRANS_SEQ, AHBBURST_WRAP4),
        wr(0x234, 0x30000003, AHBTRANS_SEQ, AHBBURST_WRAP4),
        rd(0x238, 0x30000000, AHBTRANS_NONSEQ, AHBBURST_WRAP4),
        rd(0x23c, 0x30000001, AHBTRANS_SEQ, AHBBURST_WRAP4),
        rd(0x230, 0x30000002, AHBTRANS_SEQ, AHBBURST_WRAP4),
        rd(0x234, 0x30000003, AHBTRANS_SEQ, AHBBURST_WRAP4),
        wr(0x300, 0xDEAD0000, AHBTRANS_NONSEQ, AHBBURST_SINGLE, 0, true),
        rd(0x300, 0, AHBTRANS_NONSEQ, AHBBURST_SINGLE, 2, true),
        rd(0x100, 0x10000001, AHBTRANS_NONSEQ, AHBBURST_SINGLE),
        wr(0x400, 0x40000001, AHBTRANS_NONSEQ, AHBBURST_SINGLE, 3),
        rd(0x400, 0x40000001, AHBTRANS_NONSEQ, AHBBURST_SINGLE),
    };
}
static constexpr unsigned XFERS = 23;
// Wait states in xferScript() and ERROR responses, each ERROR adding one
// hready-low cycle.
static constexpr unsigned SCRIPT_WAITS = 10;
static constexpr unsigned SCRIPT_ERRORS = 2;

// xferScript() with IDLE and BUSY cycles around the transfers: IDLE with hsel
// high after the first write and with hsel low after the read, BUSY inside the
// INCR4 write twice, and IDLE after the last. The first write is on the bus at
// the edge that releases reset.
static std::vector<beat> pinMgrScript()
{
    const std::vector<beat> base = xferScript();
    std::vector<beat> items;
    for (size_t i = 0; i < base.size(); ++i) {
        items.push_back(base[i]);
        if (i == 0) items.push_back(idle(true));
        if (i == 1) items.push_back(idle(false));
        if (i == 2) items.push_back(busy(0x204, true, AHBBURST_INCR4));
        if (i == 3) items.push_back(busy(0x208, true, AHBBURST_INCR4));
    }
    for (int i = 0; i < 3; ++i) items.push_back(idle(true));
    return items;
}

// Transfers for a manager that issues one beat at a time: a locked INCR4
// write, a WRAP4 read, a two-beat INCR write, a single write, two locked
// single reads of what the INCR4 wrote, a two-beat INCR write whose last beat
// ends at the 1KB boundary 0x400, and a read of that beat. Reads of unwritten
// addresses return 0.
static std::vector<beat> slowScript()
{
    std::vector<beat> items = {
        wr(0x500, 0x50000000, AHBTRANS_NONSEQ, AHBBURST_INCR4),
        wr(0x504, 0x50000001, AHBTRANS_SEQ, AHBBURST_INCR4),
        wr(0x508, 0x50000002, AHBTRANS_SEQ, AHBBURST_INCR4),
        wr(0x50c, 0x50000003, AHBTRANS_SEQ, AHBBURST_INCR4),
        rd(0x538, 0, AHBTRANS_NONSEQ, AHBBURST_WRAP4),
        rd(0x53c, 0, AHBTRANS_SEQ, AHBBURST_WRAP4),
        rd(0x530, 0, AHBTRANS_SEQ, AHBBURST_WRAP4),
        rd(0x534, 0, AHBTRANS_SEQ, AHBBURST_WRAP4),
        wr(0x600, 0x60000000, AHBTRANS_NONSEQ, AHBBURST_INCR),
        wr(0x604, 0x60000001, AHBTRANS_SEQ, AHBBURST_INCR),
        wr(0x700, 0x70000000, AHBTRANS_NONSEQ, AHBBURST_SINGLE),
        rd(0x500, 0x50000000, AHBTRANS_NONSEQ, AHBBURST_SINGLE),
        rd(0x504, 0x50000001, AHBTRANS_NONSEQ, AHBBURST_SINGLE),
        wr(0x3f8, 0x3f000000, AHBTRANS_NONSEQ, AHBBURST_INCR),
        wr(0x3fc, 0x3f000001, AHBTRANS_SEQ, AHBBURST_INCR),
        rd(0x3fc, 0x3f000001, AHBTRANS_NONSEQ, AHBBURST_SINGLE),
    };
    for (size_t i = 0; i < 4; ++i) items[i].lock = true;
    items[11].lock = true;
    items[12].lock = true;
    return items;
}
static constexpr unsigned SLOW_XFERS = 16;

// Samples the pins at each clock edge, after reset, and records what AHB-Lite
// allows and requires. It reads the values that held in the cycle the edge ends.
class ahbPinMonitor : public sc_module
{
public:
    sc_in<bool> clk;
    sc_in<bool> rst_n;

    struct accepted
    {
        uint64_t edge;
        bool sel;
        unsigned trans;
        uint64_t addr;
        bool write;
        unsigned size, burst, prot;
    };
    struct completed
    {
        uint64_t edge;
        bool write, resp;
        uint64_t rdata, wdata;
    };

    std::vector<accepted> acc;      // every address phase taken at a hready-high edge
    std::vector<completed> dn;      // every NONSEQ/SEQ data phase, at its last cycle
    std::vector<std::string> tags;  // rule tag of each violation, in order
    std::vector<std::string> notes; // full text of each violation
    unsigned waitCycles = 0;        // cycles with hready low
    unsigned errorResponses = 0;    // two-cycle ERROR responses
    unsigned pipelined = 0;         // address phase taken as the previous transfer's data phase ends
    unsigned busyAccepted = 0, busyZeroWait = 0;
    unsigned idleAccepted = 0, idleZeroWait = 0; // IDLE with hsel high
    unsigned unselNotIdle = 0;                   // cycles with hsel low and htrans not IDLE
    unsigned unselIdle = 0;                      // cycles with hsel low and htrans IDLE
    bool quiet = false;

    SC_HAS_PROCESS(ahbPinMonitor);
    ahbPinMonitor(sc_module_name n, pins_t &p) : sc_module(n), pins(p) { SC_THREAD(run); }

private:
    pins_t &pins;
    static constexpr size_t MAX_RECORDS = 256;

    struct snap
    {
        bool sel, write, lock, rdy, resp;
        unsigned trans, size, burst, prot;
        uint64_t addr, wdata, rdata;
    };
    enum dpKind { DP_NONE, DP_XFER, DP_BUSY, DP_IDLE };
    struct burstState
    {
        bool active = false;
        unsigned burst = 0, size = 0, prot = 0;
        bool write = false, lock = false;
        int left = 0; // beats still allowed after the last one, -1 for INCR
        uint64_t next = 0;

        // A burst never crosses a 1KB boundary, so an incrementing burst whose
        // next beat would start a new 1KB block has no beats left.
        void endAtBoundary()
        {
            if (next % 1024 == 0) left = 0;
        }
    };

    snap sample() const
    {
        snap s;
        s.sel = pins.hsel.read();
        s.trans = pins.htrans.read().to_uint();
        s.addr = pins.haddr.read().to_uint64();
        s.write = pins.hwrite.read();
        s.size = pins.hsize.read().to_uint();
        s.burst = pins.hburst.read().to_uint();
        s.prot = pins.hprot.read().to_uint();
        s.lock = pins.hmastlock.read();
        s.wdata = pins.hwdata.read().to_uint64();
        s.rdy = pins.hready.read();
        s.rdata = pins.hrdata.read().to_uint64();
        s.resp = pins.hresp.read();
        return s;
    }

    void flag(const char *tag, const std::string &detail, uint64_t edge)
    {
        tags.push_back(tag);
        notes.push_back(std::format("{} {} (edge {}, {})", tag, detail, edge, sc_time_stamp().to_string()));
        if (!quiet) std::printf("VIOLATION %s %s\n", name(), notes.back().c_str());
    }

    static bool sameAddrPhase(const snap &a, const snap &b)
    {
        return a.sel == b.sel && a.trans == b.trans && a.addr == b.addr && a.write == b.write && a.size == b.size &&
               a.burst == b.burst && a.prot == b.prot && a.lock == b.lock;
    }

    // Burst rules for the address phase taken at this edge.
    void burstRules(const snap &s, burstState &b, uint64_t edge)
    {
        if (s.sel && s.trans == AHBTRANS_NONSEQ) {
            const unsigned beats = burstBeats(s.burst);
            b = burstState{true, s.burst, s.size, s.prot, s.write, s.lock, beats ? int(beats) - 1 : -1,
                           nextAddr(s.addr, s.size, s.burst)};
            if (!isWrapBurst(s.burst)) b.endAtBoundary();
            return;
        }
        if (s.sel && (s.trans == AHBTRANS_SEQ || s.trans == AHBTRANS_BUSY)) {
            const char *kind = s.trans == AHBTRANS_SEQ ? "SEQ" : "BUSY";
            if (!b.active) {
                flag(s.trans == AHBTRANS_SEQ ? "SEQ" : "BUSY", std::format("{} outside a burst", kind), edge);
                return;
            }
            if (b.left == 0) {
                flag("LEN", std::format("{} after the last beat of the burst", kind), edge);
            }
            if (s.addr != b.next) {
                flag("WRAP", std::format("{} address 0x{:x}, expected 0x{:x}", kind, s.addr, b.next), edge);
            }
            if (s.write != b.write || s.size != b.size || s.burst != b.burst || s.prot != b.prot || s.lock != b.lock) {
                flag("CTRL", std::format("{} control differs from the burst's NONSEQ", kind), edge);
            }
            if (s.trans == AHBTRANS_SEQ) {
                if (b.left > 0) --b.left;
                b.next = nextAddr(b.next, b.size, b.burst);
                if (!isWrapBurst(b.burst)) b.endAtBoundary();
            }
            return;
        }
        // A manager may cancel the rest of a burst with IDLE in the second
        // cycle of an ERROR response.
        if (b.active && b.left > 0 && !s.resp) {
            flag("BURSTIDLE", std::format("IDLE with {} beats of a fixed-length burst left", b.left), edge);
        }
        b.active = false;
    }

    // Consecutive locked transfers are one locked sequence, so hmastlock stays
    // high on the IDLE cycles between them.
    void lockRules(const snap &s, bool &lastLock, bool &lockDropped, uint64_t edge)
    {
        if (s.sel && isXferTrans(s.trans)) {
            if (s.lock && lockDropped) flag("LOCK", "hmastlock dropped between two locked transfers", edge);
            lastLock = s.lock;
            lockDropped = false;
        } else if (lastLock && !s.lock) {
            lockDropped = true;
        }
    }

    void run()
    {
        snap prev{};
        bool havePrev = false;
        bool prevWriteDp = false;
        dpKind dp = DP_NONE;
        bool dpWrite = false;
        bool errSecond = false;
        burstState b;
        bool lastLock = false, lockDropped = false;
        uint64_t edge = 0;
        while (true) {
            wait(clk.posedge_event());
            if (!rst_n.read()) {
                havePrev = false;
                dp = DP_NONE;
                errSecond = false;
                b.active = false;
                lastLock = lockDropped = false;
                continue;
            }
            ++edge;
            const snap s = sample();
            if (!s.rdy) ++waitCycles;
            if (!s.sel) (s.trans == AHBTRANS_IDLE ? unselIdle : unselNotIdle)++;

            // ERROR is two cycles: hready low with hresp, then hready high with hresp.
            if (errSecond) {
                if (s.rdy && s.resp) {
                    ++errorResponses;
                } else {
                    flag("ERR2", "second ERROR cycle needs hready high and hresp high", edge);
                }
                errSecond = false;
            } else if (s.resp) {
                if (dp != DP_XFER) flag("ERRIDLE", "hresp ERROR with no transfer in its data phase", edge);
                if (s.rdy) {
                    flag("ERR1", "hresp ERROR with hready high and no hready-low cycle before it", edge);
                } else {
                    errSecond = true;
                }
            }
            // Nothing in a data phase, or IDLE/BUSY there, means hready high and OKAY.
            // ERRIDLE above covers hresp.
            if (dp != DP_XFER && !s.rdy) flag("ZEROWAIT", "hready low with no transfer in its data phase", edge);

            // While hready is low a NONSEQ/SEQ address phase and the write data
            // hold, except that the manager may change htrans to IDLE in the
            // second ERROR cycle.
            if (havePrev && !prev.rdy) {
                const bool errorCancel = prev.resp && s.trans == AHBTRANS_IDLE;
                if (prev.sel && isXferTrans(prev.trans) && !sameAddrPhase(prev, s) && !errorCancel) {
                    flag("STABLE", std::format("address phase changed while hready was low: haddr 0x{:x} -> 0x{:x}",
                                               prev.addr, s.addr),
                         edge);
                }
                if (prevWriteDp && s.wdata != prev.wdata) {
                    flag("WDATA", std::format("hwdata changed while hready was low: 0x{:x} -> 0x{:x}", prev.wdata, s.wdata),
                         edge);
                }
            }

            prevWriteDp = dp == DP_XFER && dpWrite;
            if (s.rdy) {
                const bool wasXfer = dp == DP_XFER;
                if (wasXfer) {
                    dn.push_back({edge, dpWrite, s.resp, s.rdata, s.wdata});
                } else if (dp == DP_BUSY && !s.resp) {
                    ++busyZeroWait;
                } else if (dp == DP_IDLE && !s.resp) {
                    ++idleZeroWait;
                }
                const bool xfer = s.sel && isXferTrans(s.trans);
                if (wasXfer && xfer) ++pipelined;
                if (s.sel && s.trans == AHBTRANS_BUSY) ++busyAccepted;
                if (s.sel && s.trans == AHBTRANS_IDLE) ++idleAccepted;
                if (acc.size() < MAX_RECORDS) {
                    acc.push_back({edge, s.sel, s.trans, s.addr, s.write, s.size, s.burst, s.prot});
                }
                burstRules(s, b, edge);
                lockRules(s, lastLock, lockDropped, edge);
                dp = xfer ? DP_XFER : (s.sel && s.trans == AHBTRANS_BUSY) ? DP_BUSY : (s.sel ? DP_IDLE : DP_NONE);
                dpWrite = s.write;
            }
            prev = s;
            havePrev = true;
        }
    }
};

// Every address phase in `items` appears on the pins, in order, one per
// data-phase length, so a bubble between transfers or a lost wait state
// moves an edge and fails here.
static void checkTrace(const std::string &name, const ahbPinMonitor &mon, const std::vector<beat> &items)
{
    size_t f = 0;
    while (!isXfer(items[f])) ++f;
    size_t r = 0;
    while (r < mon.acc.size() && !(mon.acc[r].sel && isXferTrans(mon.acc[r].trans))) ++r;
    const size_t span = items.size() - f;
    expect(name + " address phases recorded", mon.acc.size() >= r + span + 1, 1);
    if (mon.acc.size() < r + span + 1) return;

    unsigned xfer = 0;
    for (size_t k = 0; k < span; ++k) {
        const beat &it = items[f + k];
        const ahbPinMonitor::accepted &rec = mon.acc[r + k];
        const std::string at = std::format("{} item {}", name, f + k);
        expect(at + " hsel", rec.sel, it.sel);
        expect(at + " htrans", rec.trans, it.trans);
        if (it.sel && it.trans != AHBTRANS_IDLE) {
            expect(at + " haddr", rec.addr, it.addr);
            expect(at + " hwrite", rec.write, it.write);
            expect(at + " hsize", rec.size, SIZE);
            expect(at + " hburst", rec.burst, it.burst);
            expect(at + " hprot", rec.prot, PROT);
        }
        expect(at + " cycles to the next address phase", mon.acc[r + k + 1].edge - rec.edge, dataPhaseCycles(it));
        if (isXfer(it)) {
            expect(at + " data phase recorded", xfer < mon.dn.size(), 1);
            if (xfer < mon.dn.size()) {
                const ahbPinMonitor::completed &c = mon.dn[xfer];
                expect(at + " data phase ends after its wait states", c.edge - rec.edge, dataPhaseCycles(it));
                expect(at + " hresp", c.resp, it.error);
                expect(at + " data phase direction", c.write, it.write);
                if (it.write) expect(at + " hwdata at the last cycle", c.wdata, it.data);
                if (!it.write && !it.error) expect(at + " hrdata at the last cycle", c.rdata, it.data);
            }
            ++xfer;
        }
    }
    expect(name + " data phases", mon.dn.size(), xfer);
}

static void checkMonitorClean(const std::string &name, const ahbPinMonitor &mon)
{
    for (const std::string &note : mon.notes) std::printf("  %s: %s\n", name.c_str(), note.c_str());
    expect(name + " protocol violations", mon.tags.size(), 0);
}

// Model manager with one thread per phase, so the address of the next
// transfer goes out while the current one is in its data phase. The data
// thread is registered first, so its first sendData() waits in the channel
// for the write's address.
class modelMgr : public sc_module
{
public:
    unsigned responses = 0;
    SC_HAS_PROCESS(modelMgr);
    modelMgr(sc_module_name n, ahb_channel<A, D> &c, std::vector<beat> s)
        : sc_module(n), chan(c), script(std::move(s))
    {
        SC_THREAD(dataPhase);
        SC_THREAD(addrPhase);
        SC_THREAD(respPhase);
    }

private:
    ahb_channel<A, D> &chan;
    const std::vector<beat> script;

    void addrPhase()
    {
        for (const beat &b : script) {
            ahbAddrSt<A> a;
            a.haddr.value = b.addr;
            a.hwrite = b.write;
            a.hsize = SIZE;
            a.hburst = b.burst;
            a.hprot = PROT;
            a.htrans = b.trans;
            a.hmastlock = b.lock;
            chan.sendAddr(a, std::nullopt);
        }
    }
    void dataPhase()
    {
        for (const beat &b : script) {
            if (!b.write) continue;
            D d;
            d.value = b.data;
            chan.sendData(d);
        }
    }
    void respPhase()
    {
        for (size_t i = 0; i < script.size(); ++i) {
            ahbRespSt<D> r;
            chan.receiveResp(r);
            const std::string at = std::format("{} response {}", name(), i);
            expect(at + " hresp", r.hresp, script[i].error);
            // A read returns what the writes before it stored, and a read that
            // answers ERROR carries no data to compare.
            if (!script[i].write && !script[i].error) expect(at + " hrdata", r.hrdata.value, script[i].data);
            ++responses;
        }
    }
};

// Model manager with one thread that finishes each beat before it starts the
// next and pauses two cycles in between, so ahb_dst_bfm has nothing to send
// inside a burst.
class slowMgr : public sc_module
{
public:
    unsigned responses = 0;
    SC_HAS_PROCESS(slowMgr);
    slowMgr(sc_module_name n, ahb_channel<A, D> &c, std::vector<beat> s) : sc_module(n), chan(c), script(std::move(s))
    {
        SC_THREAD(run);
    }

private:
    ahb_channel<A, D> &chan;
    const std::vector<beat> script;

    void run()
    {
        for (size_t i = 0; i < script.size(); ++i) {
            const beat &b = script[i];
            ahbAddrSt<A> a;
            a.haddr.value = b.addr;
            a.hwrite = b.write;
            a.hsize = SIZE;
            a.hburst = b.burst;
            a.hprot = PROT;
            a.htrans = b.trans;
            a.hmastlock = b.lock;
            chan.sendAddr(a, std::nullopt);
            if (b.write) {
                D d;
                d.value = b.data;
                chan.sendData(d);
            }
            ahbRespSt<D> r;
            chan.receiveResp(r);
            const std::string at = std::format("{} response {}", name(), i);
            expect(at + " hresp", r.hresp, 0);
            if (!b.write) expect(at + " hrdata", r.hrdata.value, b.data);
            ++responses;
            wait(20, SC_NS);
        }
    }
};

// Model subordinate behind ahb_src_bfm. It serves one transfer at a time,
// checks each address phase and write data against the script, holds the
// response for the scripted wait cycles and answers ERROR where scripted.
class modelSub : public sc_module
{
public:
    sc_in<bool> clk;
    unsigned served = 0;
    SC_HAS_PROCESS(modelSub);
    modelSub(sc_module_name n, ahb_channel<A, D> &c, std::vector<beat> s)
        : sc_module(n), chan(c), script(std::move(s))
    {
        SC_THREAD(serve);
    }

private:
    ahb_channel<A, D> &chan;
    const std::vector<beat> script;
    std::map<uint32_t, uint32_t> mem;

    void serve()
    {
        for (size_t i = 0; i < script.size(); ++i) {
            const beat &b = script[i];
            const std::string at = std::format("{} transfer {}", name(), i);
            ahbAddrSt<A> a;
            chan.receiveAddr(a);
            expect(at + " haddr", a.haddr.value, b.addr);
            expect(at + " hwrite", a.hwrite, b.write);
            expect(at + " hsize", a.hsize, SIZE);
            expect(at + " hburst", a.hburst, b.burst);
            expect(at + " hprot", a.hprot, PROT);
            expect(at + " htrans", a.htrans, b.trans);
            ahbRespSt<D> r;
            r.hresp = b.error;
            if (a.hwrite) {
                D d;
                chan.receiveData(d);
                expect(at + " hwdata", d.value, b.data);
                if (!b.error) mem[b.addr] = uint32_t(d.value);
            } else {
                r.hrdata.value = mem[b.addr];
            }
            for (unsigned w = 0; w < b.waits; ++w) wait(clk.posedge_event());
            chan.sendResp(r);
            ++served;
        }
    }
};

// Pin-level manager for ahb_src_bfm. It presents one script item per accepted
// cycle and holds every output while hready is low.
class pinMgr : public sc_module
{
public:
    sc_in<bool> clk;
    sc_in<bool> rst_n;
    SC_HAS_PROCESS(pinMgr);
    pinMgr(sc_module_name n, pins_t &p, std::vector<beat> s) : sc_module(n), pins(p), script(std::move(s))
    {
        SC_THREAD(run);
    }

private:
    pins_t &pins;
    const std::vector<beat> script;
    const beat idleBeat = idle(false);
    size_t next = 0;

    const beat *pick() { return next < script.size() ? &script[next++] : &idleBeat; }

    void drive(const beat &b)
    {
        pins.hsel = b.sel;
        if (!b.sel || b.trans == AHBTRANS_IDLE) {
            pins.htrans = AHBTRANS_IDLE;
            pins.haddr = VA(0);
            pins.hwrite = false;
            pins.hsize = 0;
            pins.hburst = 0;
            pins.hprot = 0;
        } else {
            pins.htrans = b.trans;
            pins.haddr = VA(b.addr);
            pins.hwrite = b.write;
            pins.hsize = SIZE;
            pins.hburst = b.burst;
            pins.hprot = PROT;
        }
        pins.hmastlock = false;
    }

    void run()
    {
        drive(idleBeat);
        pins.hwdata = VD(0);
        // The first address phase is on the bus at the edge that releases reset.
        while (!rst_n.read()) wait(rst_n.value_changed_event());
        const beat *ap = pick();
        const beat *dp = nullptr;
        drive(*ap);
        while (true) {
            wait(clk.posedge_event());
            if (!pins.hready.read()) continue;
            dp = ap;
            ap = pick();
            drive(*ap);
            pins.hwdata = VD(isXfer(*dp) && dp->write ? dp->data : 0);
        }
    }
};

// Pin-level subordinate for ahb_dst_bfm. Each accepted transfer gets its
// scripted wait cycles, then OKAY or the two-cycle ERROR. A read returns what
// the completed writes before it stored.
class pinSub : public sc_module
{
public:
    sc_in<bool> clk;
    sc_in<bool> rst_n;
    struct served
    {
        uint32_t addr, wdata;
        bool write, error;
    };
    std::vector<served> log;

    SC_HAS_PROCESS(pinSub);
    pinSub(sc_module_name n, pins_t &p, std::vector<beat> s) : sc_module(n), pins(p), script(std::move(s))
    {
        SC_THREAD(run);
    }

private:
    pins_t &pins;
    const std::vector<beat> script;
    std::map<uint32_t, uint32_t> mem;

    void drive(bool rdy, bool resp, uint32_t rdata)
    {
        pins.hready = rdy;
        pins.hresp = resp;
        pins.hrdata = VD(rdata);
    }

    void run()
    {
        drive(true, false, 0);
        bool curReady = true;
        bool dpValid = false, dpWrite = false, dpError = false, errFirstDone = false;
        uint32_t dpAddr = 0;
        unsigned dpWaits = 0;
        size_t taken = 0;
        do { wait(clk.posedge_event()); } while (!rst_n);
        while (true) {
            wait(clk.posedge_event());
            if (dpValid && curReady) {
                const uint32_t wdata = uint32_t(pins.hwdata.read().to_uint64());
                if (dpWrite && !dpError) mem[dpAddr] = wdata;
                log.push_back({dpAddr, dpWrite ? wdata : 0, dpWrite, dpError});
                dpValid = false;
            }
            if (curReady && pins.hsel.read() && isXferTrans(pins.htrans.read().to_uint())) {
                dpValid = true;
                dpWrite = pins.hwrite.read();
                dpAddr = uint32_t(pins.haddr.read().to_uint64());
                const beat &b = taken < script.size() ? script[taken] : script.back();
                dpWaits = b.waits;
                dpError = b.error;
                errFirstDone = false;
                ++taken;
            }
            if (!dpValid) {
                drive(true, false, 0);
                curReady = true;
            } else if (dpWaits > 0) {
                --dpWaits;
                drive(false, false, 0);
                curReady = false;
            } else if (dpError && !errFirstDone) {
                errFirstDone = true;
                drive(false, true, 0);
                curReady = false;
            } else if (dpError) {
                drive(true, true, 0);
                curReady = true;
            } else {
                drive(true, false, dpWrite ? 0 : mem[dpAddr]);
                curReady = true;
            }
        }
    }
};

class loopback : public sc_module
{
public:
    sc_clock clk{"clk", 10, SC_NS};
    sc_signal<bool> rst_n{"rst_n"};
    ahb_channel<A, D> chanM{"chanM", "tb"};
    ahb_channel<A, D> chanS{"chanS", "tb"};
    pins_t pins;
    ahb_dst_bfm<A, D, VA, VD> mgrBfm{"mgrBfm"};
    ahb_src_bfm<A, D, VA, VD> subBfm{"subBfm"};
    modelMgr mgr{"mgr", chanM, xferScript()};
    modelSub sub{"sub", chanS, xferScript()};
    ahbPinMonitor mon{"mon", pins};

    SC_CTOR(loopback)
    {
        mgrBfm.if_p(chanM);
        mgrBfm.hdl_if_p(pins);
        mgrBfm.clk(clk);
        mgrBfm.rst_n(rst_n);
        subBfm.if_p(chanS);
        subBfm.hdl_if_p(pins);
        subBfm.clk(clk);
        subBfm.rst_n(rst_n);
        sub.clk(clk);
        mon.clk(clk);
        mon.rst_n(rst_n);
        SC_THREAD(reset);
    }
    void reset()
    {
        rst_n = false;
        wait(35, SC_NS);
        rst_n = true;
    }
    void verify()
    {
        expect("loopback manager responses", mgr.responses, XFERS);
        expect("loopback subordinate transfers", sub.served, XFERS);
        checkTrace("loopback", mon, xferScript());
        checkMonitorClean("loopback", mon);
        expect("loopback hready-low cycles", mon.waitCycles, SCRIPT_WAITS + SCRIPT_ERRORS);
        expect("loopback ERROR responses", mon.errorResponses, SCRIPT_ERRORS);
        expect("loopback transfers pipelined", mon.pipelined, XFERS - 1);
        expect("loopback IDLE with hsel low between transfers", mon.unselNotIdle, 0);
        std::printf("scenario loopback transfers:%zu pipelined:%u waitCycles:%u errors:%u violations:%zu\n", mon.dn.size(),
                    mon.pipelined, mon.waitCycles, mon.errorResponses, mon.tags.size());
    }
};

class srcBfmScenario : public sc_module
{
public:
    sc_clock clk{"clk", 10, SC_NS};
    sc_signal<bool> rst_n{"rst_n"};
    ahb_channel<A, D> chan{"chan", "tb"};
    pins_t pins;
    ahb_src_bfm<A, D, VA, VD> bfm{"bfm"};
    pinMgr mgr{"mgr", pins, pinMgrScript()};
    modelSub sub{"sub", chan, xferScript()};
    ahbPinMonitor mon{"mon", pins};

    SC_CTOR(srcBfmScenario)
    {
        bfm.if_p(chan);
        bfm.hdl_if_p(pins);
        bfm.clk(clk);
        bfm.rst_n(rst_n);
        mgr.clk(clk);
        mgr.rst_n(rst_n);
        sub.clk(clk);
        mon.clk(clk);
        mon.rst_n(rst_n);
        SC_THREAD(reset);
    }
    void reset()
    {
        rst_n = false;
        wait(35, SC_NS);
        rst_n = true;
    }
    void verify()
    {
        expect("srcBfm subordinate transfers", sub.served, XFERS);
        checkTrace("srcBfm", mon, pinMgrScript());
        checkMonitorClean("srcBfm", mon);
        expect("srcBfm hready-low cycles", mon.waitCycles, SCRIPT_WAITS + SCRIPT_ERRORS);
        expect("srcBfm ERROR responses", mon.errorResponses, SCRIPT_ERRORS);
        // Four of the 22 neighbouring transfer pairs have an IDLE or BUSY between them.
        expect("srcBfm transfers pipelined", mon.pipelined, XFERS - 1 - 4);
        expect("srcBfm BUSY cycles accepted", mon.busyAccepted, 2);
        expect("srcBfm BUSY data phases zero-wait OKAY", mon.busyZeroWait, 2);
        expect("srcBfm IDLE (hsel high) data phases zero-wait OKAY, at least the scripted ones",
               mon.idleZeroWait >= 4, 1);
        expect("srcBfm IDLE (hsel high) cycles all zero-wait", mon.idleZeroWait + 1 >= mon.idleAccepted, 1);
        std::printf("scenario srcBfm transfers:%zu pipelined:%u waitCycles:%u errors:%u busy:%u violations:%zu\n",
                    mon.dn.size(), mon.pipelined, mon.waitCycles, mon.errorResponses, mon.busyZeroWait, mon.tags.size());
    }
};

class dstBfmScenario : public sc_module
{
public:
    sc_clock clk{"clk", 10, SC_NS};
    sc_signal<bool> rst_n{"rst_n"};
    ahb_channel<A, D> chan{"chan", "tb"};
    pins_t pins;
    ahb_dst_bfm<A, D, VA, VD> bfm{"bfm"};
    modelMgr mgr{"mgr", chan, xferScript()};
    pinSub sub{"sub", pins, xferScript()};
    ahbPinMonitor mon{"mon", pins};

    SC_CTOR(dstBfmScenario)
    {
        bfm.if_p(chan);
        bfm.hdl_if_p(pins);
        bfm.clk(clk);
        bfm.rst_n(rst_n);
        sub.clk(clk);
        sub.rst_n(rst_n);
        mon.clk(clk);
        mon.rst_n(rst_n);
        SC_THREAD(reset);
    }
    void reset()
    {
        rst_n = false;
        wait(35, SC_NS);
        rst_n = true;
    }
    void verify()
    {
        const std::vector<beat> script = xferScript();
        expect("dstBfm manager responses", mgr.responses, XFERS);
        expect("dstBfm subordinate transfers", sub.log.size(), XFERS);
        for (size_t i = 0; i < sub.log.size() && i < script.size(); ++i) {
            const std::string at = std::format("dstBfm subordinate transfer {}", i);
            expect(at + " haddr", sub.log[i].addr, script[i].addr);
            expect(at + " write", sub.log[i].write, script[i].write);
            if (script[i].write) expect(at + " hwdata", sub.log[i].wdata, script[i].data);
            expect(at + " error", sub.log[i].error, script[i].error);
        }
        checkTrace("dstBfm", mon, script);
        checkMonitorClean("dstBfm", mon);
        expect("dstBfm hready-low cycles", mon.waitCycles, SCRIPT_WAITS + SCRIPT_ERRORS);
        expect("dstBfm ERROR responses", mon.errorResponses, SCRIPT_ERRORS);
        expect("dstBfm transfers pipelined", mon.pipelined, XFERS - 1);
        // With nothing left to send the manager drives IDLE and hsel low.
        expect("dstBfm IDLE cycles with hsel low", mon.unselIdle >= 3, 1);
        expect("dstBfm hsel low with htrans not IDLE", mon.unselNotIdle, 0);
        std::printf("scenario dstBfm transfers:%zu pipelined:%u waitCycles:%u errors:%u violations:%zu\n", mon.dn.size(),
                    mon.pipelined, mon.waitCycles, mon.errorResponses, mon.tags.size());
    }
};

class slowMgrScenario : public sc_module
{
public:
    sc_clock clk{"clk", 10, SC_NS};
    sc_signal<bool> rst_n{"rst_n"};
    ahb_channel<A, D> chan{"chan", "tb"};
    pins_t pins;
    ahb_dst_bfm<A, D, VA, VD> bfm{"bfm"};
    slowMgr mgr{"mgr", chan, slowScript()};
    pinSub sub{"sub", pins, slowScript()};
    ahbPinMonitor mon{"mon", pins};

    SC_CTOR(slowMgrScenario)
    {
        bfm.if_p(chan);
        bfm.hdl_if_p(pins);
        bfm.clk(clk);
        bfm.rst_n(rst_n);
        sub.clk(clk);
        sub.rst_n(rst_n);
        mon.clk(clk);
        mon.rst_n(rst_n);
        SC_THREAD(reset);
    }
    void reset()
    {
        rst_n = false;
        wait(35, SC_NS);
        rst_n = true;
    }
    void verify()
    {
        const std::vector<beat> script = slowScript();
        expect("slowMgr manager responses", mgr.responses, SLOW_XFERS);
        expect("slowMgr subordinate transfers", sub.log.size(), SLOW_XFERS);
        for (size_t i = 0; i < sub.log.size() && i < script.size(); ++i) {
            const std::string at = std::format("slowMgr subordinate transfer {}", i);
            expect(at + " haddr", sub.log[i].addr, script[i].addr);
            expect(at + " write", sub.log[i].write, script[i].write);
            if (script[i].write) expect(at + " hwdata", sub.log[i].wdata, script[i].data);
        }
        expect("slowMgr data phases", mon.dn.size(), SLOW_XFERS);
        checkMonitorClean("slowMgr", mon);
        expect("slowMgr hsel low with htrans not IDLE", mon.unselNotIdle, 0);
        std::printf("scenario slowMgr transfers:%zu busy:%u busyZeroWait:%u violations:%zu\n", mon.dn.size(),
                    mon.busyAccepted, mon.busyZeroWait, mon.tags.size());
    }
};

// One cycle of pin values.
struct pinRow
{
    bool sel;
    _ahbTransT trans;
    uint32_t addr;
    bool write;
    _ahbBurstT burst;
    uint32_t wdata;
    bool rdy, resp;
    _ahbProtT prot;
    bool lock = false;
};

static constexpr auto N = AHBTRANS_NONSEQ;
static constexpr auto S = AHBTRANS_SEQ;
static constexpr auto I = AHBTRANS_IDLE;
static constexpr auto B = AHBTRANS_BUSY;
static constexpr auto SG = AHBBURST_SINGLE;
static constexpr auto WR = AHBBURST_WRAP4;
static constexpr auto I4 = AHBBURST_INCR4;
static const pinRow idleRow{false, I, 0, false, SG, 0, true, false, 0};

// Drives one row of pin values per clock cycle after reset, with the monitor
// watching. The scenarios below use it for illegal traffic and for ERROR
// responses inside a burst.
class pinScript : public sc_module
{
public:
    sc_clock clk{"clk", 10, SC_NS};
    sc_signal<bool> rst_n{"rst_n"};
    pins_t pins;
    ahbPinMonitor mon{"mon", pins};

    SC_HAS_PROCESS(pinScript);
    pinScript(sc_module_name n, std::vector<pinRow> r) : sc_module(n), rows(std::move(r))
    {
        mon.clk(clk);
        mon.rst_n(rst_n);
        mon.quiet = true;
        SC_THREAD(reset);
        SC_THREAD(drive);
    }

    std::string tagList() const
    {
        std::string all;
        for (const std::string &t : mon.tags) all += (all.empty() ? "" : ",") + t;
        return all;
    }

private:
    const std::vector<pinRow> rows;

    void reset()
    {
        rst_n = false;
        wait(35, SC_NS);
        rst_n = true;
    }
    void put(const pinRow &r)
    {
        pins.hsel = r.sel;
        pins.htrans = r.trans;
        pins.haddr = VA(r.addr);
        pins.hwrite = r.write;
        pins.hsize = SIZE;
        pins.hburst = r.burst;
        pins.hprot = r.prot;
        pins.hmastlock = r.lock;
        pins.hwdata = VD(r.wdata);
        pins.hready = r.rdy;
        pins.hrdata = VD(0);
        pins.hresp = r.resp;
    }
    void drive()
    {
        put(idleRow);
        do { wait(clk.posedge_event()); } while (!rst_n);
        for (const pinRow &r : rows) {
            put(r);
            wait(clk.posedge_event());
        }
        put(idleRow);
    }
};

// Illegal pin traffic, one violation per row group. The monitor must report
// each, and nothing else, so a monitor that went quiet fails here.
static std::vector<pinRow> selfTestRows()
{
    // sel, trans, addr, write, burst, wdata, hready, hresp, prot
    return {
        {true, N, 0x100, true, SG, 0, true, false, 0},      // write accepted
        {true, N, 0x200, false, SG, 0xAA, false, false, 0}, // wait state
        {true, N, 0x204, false, SG, 0xAA, true, false, 0},  // STABLE: haddr moved while hready was low
        idleRow,
        {true, N, 0x300, true, SG, 0, true, false, 0},
        {false, I, 0, false, SG, 0x55, false, false, 0},    // wait state
        {false, I, 0, false, SG, 0x56, true, false, 0},     // WDATA: hwdata moved while hready was low
        {true, N, 0x400, false, SG, 0, true, false, 0},
        {false, I, 0, false, SG, 0, true, true, 0},         // ERR1: one-cycle ERROR
        {true, S, 0x500, false, SG, 0, true, false, 0},     // SEQ: no burst in progress
        {true, N, 0x608, false, WR, 0, true, false, 0},
        {true, S, 0x60c, false, WR, 0, true, false, 0},
        {true, S, 0x610, false, WR, 0, true, false, 0},     // WRAP: should be 0x600
        {true, S, 0x604, false, WR, 0, true, false, 7},     // CTRL: hprot differs from the NONSEQ
        {true, S, 0x608, false, WR, 0, true, false, 0},     // LEN: fifth beat of a four-beat burst
        idleRow,
        {true, N, 0x700, false, I4, 0, true, false, 0},
        {true, I, 0, false, SG, 0, true, false, 0},         // BURSTIDLE: IDLE with three beats left
        idleRow,
        {true, N, 0x800, false, SG, 0, true, false, 0, true},
        idleRow,                                            // hmastlock dropped
        {true, N, 0x804, false, SG, 0, true, false, 0, true}, // LOCK: locked again
        idleRow,
        {true, N, 0x900, false, SG, 0, true, false, 0},
        {false, I, 0, false, SG, 0, false, true, 0},        // first ERROR cycle
        {false, I, 0, false, SG, 0, false, false, 0},       // ERR2: second ERROR cycle with hready and hresp low
        idleRow,                                            // the read ends OKAY
        {false, I, 0, false, SG, 0, false, true, 0},        // ERRIDLE and ZEROWAIT: ERROR with no transfer
        {false, I, 0, false, SG, 0, true, true, 0},         // its second cycle
        idleRow,
        {true, B, 0xa00, false, SG, 0, true, false, 0},     // BUSY: no burst in progress
        idleRow,
        {true, N, 0xb00, false, I4, 0, true, false, 0},
        {true, S, 0xb04, false, I4, 0, false, true, 0},     // first ERROR cycle
        {true, S, 0xb08, false, I4, 0, true, true, 0},      // STABLE: only IDLE may replace the pending SEQ,
                                                            // and WRAP: the beat after 0xb00 is 0xb04
        {true, S, 0xb08, false, I4, 0, true, false, 0},     // the monitor counts on from 0xb04
        {true, S, 0xb0c, false, I4, 0, true, false, 0},
        {true, I, 0, false, SG, 0, true, false, 0},
        idleRow,
    };
}
static const std::vector<std::string> SELF_TEST_TAGS = {"STABLE", "WDATA", "ERR1",  "SEQ",     "WRAP",
                                                        "CTRL",   "LEN",   "BURSTIDLE", "LOCK", "ERR2",
                                                        "ERRIDLE", "ZEROWAIT", "BUSY", "STABLE", "WRAP"};

// An INCR4 read whose first beat answers ERROR. The manager drives the second
// beat during the first ERROR cycle, then cancels it with IDLE in the second.
static std::vector<pinRow> errorCancelRows()
{
    return {
        {true, N, 0x200, false, I4, 0, true, false, PROT},
        {true, S, 0x204, false, I4, 0, false, true, PROT}, // first ERROR cycle
        {true, I, 0x204, false, I4, 0, true, true, PROT},  // second ERROR cycle, burst cancelled
        {true, I, 0x204, false, I4, 0, true, false, PROT},
    };
}

// The same ERROR, after which the manager carries on with the rest of the burst.
static std::vector<pinRow> errorContinueRows()
{
    return {
        {true, N, 0x200, false, I4, 0, true, false, PROT},
        {true, S, 0x204, false, I4, 0, false, true, PROT}, // first ERROR cycle
        {true, S, 0x204, false, I4, 0, true, true, PROT},  // second ERROR cycle, 0x204 accepted
        {true, S, 0x208, false, I4, 0, true, false, PROT},
        {true, S, 0x20c, false, I4, 0, true, false, PROT},
        {true, I, 0, false, SG, 0, true, false, PROT},
    };
}

static void verifySelfTest(const pinScript &st)
{
    for (const std::string &note : st.mon.notes) std::printf("  selfTest reported: %s\n", note.c_str());
    expect("selfTest violations reported", st.mon.tags.size(), SELF_TEST_TAGS.size());
    for (size_t i = 0; i < SELF_TEST_TAGS.size() && i < st.mon.tags.size(); ++i) {
        ++g_checks;
        if (st.mon.tags[i] != SELF_TEST_TAGS[i]) {
            ++g_fail;
            std::printf("FAIL selfTest violation %zu is %s, want %s\n", i, st.mon.tags[i].c_str(),
                        SELF_TEST_TAGS[i].c_str());
        }
    }
    std::printf("scenario selfTest violations:%s\n", st.tagList().c_str());
}

// A legal ERROR inside a burst: one two-cycle ERROR, `xfers` completed data
// phases and no violation.
static void verifyBurstError(const std::string &name, const pinScript &sc, size_t xfers)
{
    checkMonitorClean(name, sc.mon);
    expect(name + " ERROR responses", sc.mon.errorResponses, 1);
    expect(name + " data phases", sc.mon.dn.size(), xfers);
    std::printf("scenario %s transfers:%zu errors:%u violations:%zu\n", name.c_str(), sc.mon.dn.size(),
                sc.mon.errorResponses, sc.mon.tags.size());
}

// A model manager written exactly as the two-thread example in
// rules/skills/systemc-interfaces.md: the address thread sends each address
// and, for a write, its data, and the second thread takes the responses. The
// first `writes` of the four transfers are writes.
class docMgr : public sc_module
{
public:
    ahb_out<A, D> ahbOut;
    unsigned responses = 0;
    SC_HAS_PROCESS(docMgr);
    docMgr(sc_module_name n, unsigned w) : sc_module(n), writes(w)
    {
        SC_THREAD(addrThread);
        SC_THREAD(respThread);
    }

private:
    const unsigned writes;

    void addrThread()
    {
        ahbAddrSt<A> a;
        a.htrans = AHBTRANS_NONSEQ;
        a.hsize = SIZE;
        a.hprot = PROT;
        for (uint32_t i = 0; i < 4; i++) {
            a.haddr.value = 0x100 + 4 * i;
            a.hwrite = (i < writes);
            ahbOut->sendAddr(a);
            if (a.hwrite) {
                D d;
                d.value = 0xA5000000 + i;
                ahbOut->sendData(d);
            }
        }
    }
    void respThread()
    {
        while (true) {
            ahbRespSt<D> r;
            ahbOut->receiveResp(r);
            expect(std::format("{} response {} hresp", name(), responses), r.hresp, 0);
            ++responses;
        }
    }
};

// docMgr through ahb_dst_bfm into a zero-wait pin subordinate. Each address
// phase must be taken at the edge after the one before, while the previous
// transfer is in its data phase.
class docMgrScenario : public sc_module
{
public:
    sc_clock clk{"clk", 10, SC_NS};
    sc_signal<bool> rst_n{"rst_n"};
    ahb_channel<A, D> chan{"chan", "tb"};
    pins_t pins;
    ahb_dst_bfm<A, D, VA, VD> bfm{"bfm"};
    docMgr mgr;
    pinSub sub;
    ahbPinMonitor mon{"mon", pins};

    SC_HAS_PROCESS(docMgrScenario);
    docMgrScenario(sc_module_name n, unsigned writes)
        : sc_module(n), mgr("mgr", writes), sub("sub", pins, script(writes)), nWrites(writes)
    {
        mgr.ahbOut(chan);
        bfm.if_p(chan);
        bfm.hdl_if_p(pins);
        bfm.clk(clk);
        bfm.rst_n(rst_n);
        sub.clk(clk);
        sub.rst_n(rst_n);
        mon.clk(clk);
        mon.rst_n(rst_n);
        SC_THREAD(reset);
    }
    void reset()
    {
        rst_n = false;
        wait(35, SC_NS);
        rst_n = true;
    }
    void verify()
    {
        const std::string nm = name();
        expect(nm + " manager responses", mgr.responses, 4);
        expect(nm + " subordinate transfers", sub.log.size(), 4);
        for (size_t i = 0; i < sub.log.size(); ++i) {
            expect(std::format("{} transfer {} haddr", nm, i), sub.log[i].addr, 0x100 + 4 * i);
            expect(std::format("{} transfer {} write", nm, i), sub.log[i].write, i < nWrites);
            if (i < nWrites) expect(std::format("{} transfer {} hwdata", nm, i), sub.log[i].wdata, 0xA5000000 + i);
        }
        std::vector<uint64_t> edges;
        for (const ahbPinMonitor::accepted &a : mon.acc) {
            if (a.sel && isXferTrans(a.trans)) edges.push_back(a.edge);
        }
        expect(nm + " address phases", edges.size(), 4);
        std::string list;
        for (size_t i = 0; i < edges.size(); ++i) {
            list += (i ? "," : "") + std::to_string(edges[i]);
            if (i) expect(std::format("{} address phase {} one edge after the one before", nm, i), edges[i] - edges[i - 1], 1);
        }
        checkMonitorClean(nm, mon);
        std::printf("scenario %s edges:%s violations:%zu\n", nm.c_str(), list.c_str(), mon.tags.size());
    }

private:
    const unsigned nWrites;

    static std::vector<beat> script(unsigned writes)
    {
        std::vector<beat> s;
        for (unsigned i = 0; i < 4; ++i) {
            s.push_back(i < writes ? wr(0x100 + 4 * i, 0xA5000000 + i, N, SG) : rd(0x100 + 4 * i, 0, N, SG));
        }
        return s;
    }
};

// Generated structures have an empty constructor, so a field starts with
// whatever its storage held. These two mimic them, one with the array
// _packedSt of a structure over 64 bits and one with a scalar _packedSt.
struct genArrayPayload
{
    static constexpr unsigned _bitWidth = 32;
    typedef uint64_t _packedSt[1];
    uint64_t value;
    genArrayPayload() {}
    void pack(_packedSt &v) const { v[0] = value; }
    void unpack(const _packedSt &v) { value = v[0]; }
    static uint64_t word(const _packedSt &v) { return v[0]; }
};
struct genScalarPayload
{
    static constexpr unsigned _bitWidth = 32;
    typedef uint64_t _packedSt;
    uint64_t value;
    genScalarPayload() {}
    void pack(_packedSt &v) const { v = value; }
    void unpack(const _packedSt &v) { value = v; }
    static uint64_t word(const _packedSt &v) { return v; }
};

// A response built in storage full of 0xff has hrdata zero, so a write
// response logs and converts a defined value.
template <typename P>
static void checkRespDataDefined(const std::string &what)
{
    alignas(ahbRespSt<P>) unsigned char storage[sizeof(ahbRespSt<P>)];
    std::memset(storage, 0xff, sizeof(storage));
    const ahbRespSt<P> *r = new (storage) ahbRespSt<P>();
    typename P::_packedSt packed{};
    r->hrdata.pack(packed);
    expect(what + " response hrdata packs to zero", P::word(packed), 0);
    expect(what + " response hresp OKAY", r->hresp, 0);
    r->~ahbRespSt<P>();
}

// A subordinate that holds hready low for ten cycles after it takes a write,
// with reset asserted during those cycles. The subordinate drives hready high
// in reset, so ahb_dst_bfm must assert rather than complete the write.
class resetMidTransfer : public sc_module
{
public:
    sc_clock clk{"clk", 10, SC_NS};
    sc_signal<bool> rst_n{"rst_n"};
    ahb_channel<A, D> chan{"chan", "tb"};
    pins_t pins;
    ahb_dst_bfm<A, D, VA, VD> bfm{"bfm"};
    unsigned responses = 0;

    SC_CTOR(resetMidTransfer)
    {
        bfm.if_p(chan);
        bfm.hdl_if_p(pins);
        bfm.clk(clk);
        bfm.rst_n(rst_n);
        SC_THREAD(reset);
        SC_THREAD(manager);
        SC_THREAD(subordinate);
    }
    void verify()
    {
        expect("resetAssert responses", responses, 0);
        expect("resetAssert exit code", errorCode::getExitCode(), 1);
        expect("resetAssert message",
               errorCode::getErrorString().find("reset during a transfer is not supported") != std::string::npos, 1);
        std::printf("scenario resetAssert responses:%u exitCode:%d\n", responses, errorCode::getExitCode());
    }

private:
    sc_event accepted;

    void reset()
    {
        rst_n = false;
        wait(35, SC_NS);
        rst_n = true;
        wait(accepted);
        wait(clk.negedge_event());
        rst_n = false;
        wait(30, SC_NS);
        rst_n = true;
    }
    void manager()
    {
        ahbAddrSt<A> a;
        a.haddr.value = 0x100;
        a.hsize = SIZE;
        a.hwrite = true;
        chan.sendAddr(a, std::nullopt);
        D d;
        d.value = 0x12345678;
        chan.sendData(d);
        ahbRespSt<D> r;
        chan.receiveResp(r);
        ++responses;
        std::printf("resetAssert response at %s rst_n=%d hresp=%d\n", sc_time_stamp().to_string().c_str(),
                    int(rst_n.read()), int(r.hresp));
    }
    void subordinate()
    {
        pins.hready = true;
        pins.hresp = false;
        pins.hrdata = VD(0);
        bool pending = false;
        unsigned waits = 0;
        while (true) {
            wait(clk.posedge_event());
            if (!rst_n.read()) {
                pending = false;
                pins.hready = true;
                continue;
            }
            if (pending && ++waits == 10) {
                pins.hready = true;
                pending = false;
            } else if (!pending && pins.hsel.read() && isXferTrans(pins.htrans.read().to_uint())) {
                pending = true;
                waits = 0;
                pins.hready = false;
                accepted.notify(SC_ZERO_TIME);
            }
        }
    }
};

int sc_main(int argc, char *argv[])
{
    if (argc > 1 && std::string(argv[1]) == "resetAssert") {
        resetMidTransfer rm("reset");
        sc_start(1, SC_US);
        rm.verify();
        std::printf("checks:%d failures:%d\n", g_checks, g_fail);
        return g_fail ? 1 : 0;
    }
    checkRespDataDefined<genArrayPayload>("array _packedSt");
    checkRespDataDefined<genScalarPayload>("scalar _packedSt");
    loopback lb("lb");
    srcBfmScenario src("src");
    dstBfmScenario dst("dst");
    slowMgrScenario slow("slow");
    pinScript st("st", selfTestRows());
    pinScript cancel("errCancel", errorCancelRows());
    pinScript cont("errContinue", errorContinueRows());
    docMgrScenario docWrites("docWrites", 4);
    docMgrScenario docMixed("docMixed", 2);
    sc_start(5, SC_US);
    lb.verify();
    src.verify();
    dst.verify();
    slow.verify();
    verifySelfTest(st);
    verifyBurstError("errCancel", cancel, 1);
    verifyBurstError("errContinue", cont, 4);
    docWrites.verify();
    docMixed.verify();
    std::printf("checks:%d failures:%d\n", g_checks, g_fail);
    return g_fail ? 1 : 0;
}
