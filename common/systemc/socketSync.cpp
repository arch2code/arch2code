// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

#include "socketSync.h"

#include "asyncEvent.h"
#include "simController.h"
#include "socketFactory.h"

#include <atomic>
#include <cstdlib>
#include <cstring>
#include <functional>
#include <memory>
#include <mutex>
#include <strings.h>
#include <thread>
#include <vector>

namespace {

std::atomic<bool> g_lockstep{false};
sc_core::sc_time g_quantum{0, sc_core::SC_NS};
std::shared_ptr<ThreadSafeEvent> g_ack_event;
std::mutex g_ack_mutex;
bool g_have_ack = false;
uint64_t g_pending_ack_time_ns = 0;
bool g_python_ready = false;
std::shared_ptr<ThreadSafeEvent> g_ready_event;
bool g_configured = false;

uint64_t g_boundary_time_ns = 0;
bool g_at_boundary = false;
uint64_t g_lockstep_epoch_ns = 0;
bool g_lockstep_epoch_set = false;
std::mutex g_boundary_events_mutex;
std::vector<std::shared_ptr<ThreadSafeEvent>> g_boundary_events;

bool g_time_gated = false;

// Mid-sim ARESETn control (rst_n active-low sense via positive rst_n level).
bool g_rst_n = false; // held low until initial release / after MSG_RESET assert
std::mutex g_reset_mutex;
bool g_reset_pending = false;
uint16_t g_reset_assert_cycles = 0;
uint16_t g_reset_settle_cycles = 0;
std::function<void()> g_model_reset_cb;
std::function<void(uint8_t &, uint8_t &)> g_axi_valid_sample_cb;

// AXI slave back-pressure policy (MSG_BP_CFG).
std::mutex g_bp_mutex;
bool g_bp_pending = false;
socket_bp_cfg_st g_bp_pending_cfg{};
uint8_t g_bp_channel = 0;
uint8_t g_bp_mode = SOCKET_BP_MODE_CLEAR;
uint16_t g_bp_cycles = 0;
uint16_t g_bp_after_beat = 0;
uint16_t g_bp_after_burst = 0;
uint32_t g_bp_rng = 1;

sc_core::sc_event &edge_event()
{
    static sc_core::sc_event *ev = new sc_core::sc_event("pysocket_clk_edge");
    return *ev;
}

sc_core::sc_event &time_tick_event()
{
    static sc_core::sc_event *ev = new sc_core::sc_event("pysocket_time_tick");
    return *ev;
}

sc_core::sc_event &rst_n_event()
{
    static sc_core::sc_event *ev = new sc_core::sc_event("pysocket_rst_n");
    return *ev;
}

void set_rst_n(bool level)
{
    if (g_rst_n == level) {
        return;
    }
    g_rst_n = level;
    rst_n_event().notify(sc_core::SC_ZERO_TIME);
    // Also poke lockstep boundary waiters so AXI port sockets that only
    // waited on boundary_event can observe ARESETn and abandon mid-burst.
    if (!level) {
        std::vector<std::shared_ptr<ThreadSafeEvent>> events;
        {
            std::lock_guard<std::mutex> lock(g_boundary_events_mutex);
            events = g_boundary_events;
        }
        for (const auto &event : events) {
            if (event) {
                event->notify();
            }
        }
    }
}

bool env_truthy(const char *value)
{
    if (value == nullptr || value[0] == '\0') {
        return false;
    }
    return std::strcmp(value, "1") == 0 || strcasecmp(value, "true") == 0 || strcasecmp(value, "yes") == 0;
}

bool env_enabled_default_true(const char *value)
{
    if (value == nullptr || value[0] == '\0') {
        return true;
    }
    if (std::strcmp(value, "0") == 0 || strcasecmp(value, "false") == 0 || strcasecmp(value, "no") == 0) {
        return false;
    }
    return env_truthy(value);
}

void begin_boundary(uint64_t time_ns)
{
    g_boundary_time_ns = time_ns;
    g_at_boundary = true;

    std::vector<std::shared_ptr<ThreadSafeEvent>> events;
    {
        std::lock_guard<std::mutex> lock(g_boundary_events_mutex);
        events = g_boundary_events;
    }
    for (const auto &event : events) {
        if (event) {
            event->notify();
        }
    }
}

void end_boundary()
{
    g_at_boundary = false;
}

sc_core::sc_time effective_quantum()
{
    if (g_quantum > sc_core::SC_ZERO_TIME) {
        return g_quantum;
    }
    return sc_core::sc_time(1, sc_core::SC_NS);
}

void advance_n_clocks(uint16_t clocks)
{
    const sc_core::sc_time period = socketSyncClockHalfPeriod() + socketSyncClockHalfPeriod();
    for (uint16_t i = 0; i < clocks; ++i) {
        socketSyncAdvanceTime(period);
    }
}

void service_reset_pulse(int fd)
{
    uint16_t assert_cycles = 0;
    uint16_t settle_cycles = 0;
    {
        std::lock_guard<std::mutex> lock(g_reset_mutex);
        assert_cycles = g_reset_assert_cycles;
        settle_cycles = g_reset_settle_cycles;
        g_reset_pending = false;
    }
    if (assert_cycles == 0) {
        assert_cycles = 5;
    }
    if (settle_cycles == 0) {
        settle_cycles = 2;
    }

    set_rst_n(false);
    // Abandon in-flight model activity immediately (HDL uses physical rst_n).
    if (g_model_reset_cb) {
        g_model_reset_cb();
    }
    // One clock so DUT / BFMs see rst_n low before AxVALID sample.
    advance_n_clocks(1);
    socket_reset_ack_st ack{};
    if (g_axi_valid_sample_cb) {
        g_axi_valid_sample_cb(ack.arvalid, ack.awvalid);
    }
    if (assert_cycles > 1) {
        advance_n_clocks(static_cast<uint16_t>(assert_cycles - 1));
    }
    set_rst_n(true);
    advance_n_clocks(settle_cycles);
    // Re-apply soft reset after settle so late AXI replies during the pulse
    // cannot leave STATUS.ERR/DONE set on the model path.
    if (g_model_reset_cb) {
        g_model_reset_cb();
    }

    (void)socket_send_msg(fd, MSG_RESET_ACK, &ack, static_cast<uint16_t>(sizeof(ack)));
}

void apply_bp_cfg(const socket_bp_cfg_st &cfg)
{
    std::lock_guard<std::mutex> lock(g_bp_mutex);
    if (cfg.mode == SOCKET_BP_MODE_CLEAR || cfg.channel == 0) {
        g_bp_channel = 0;
        g_bp_mode = SOCKET_BP_MODE_CLEAR;
        g_bp_cycles = 0;
        g_bp_after_beat = 0;
        g_bp_after_burst = 0;
        g_bp_rng = 1;
        return;
    }
    g_bp_channel = cfg.channel;
    g_bp_mode = cfg.mode;
    g_bp_cycles = cfg.cycles;
    g_bp_after_beat = cfg.after_beat;
    g_bp_after_burst = cfg.after_burst;
    g_bp_rng = cfg.seed != 0 ? cfg.seed : 1u;
}

void service_bp_cfg(int fd)
{
    socket_bp_cfg_st cfg{};
    {
        std::lock_guard<std::mutex> lock(g_bp_mutex);
        cfg = g_bp_pending_cfg;
        g_bp_pending = false;
    }
    apply_bp_cfg(cfg);
    (void)socket_send_msg(fd, MSG_BP_CFG_ACK, nullptr, 0);
}

bool bp_burst_beat_match(uint16_t burst, uint16_t beat)
{
    if (g_bp_after_burst != SOCKET_BP_EVERY_BURST && burst != g_bp_after_burst) {
        return false;
    }
    // RANDOM ignores after_beat and may stall any beat of a matching burst.
    if (g_bp_mode == SOCKET_BP_MODE_RANDOM) {
        return true;
    }
    return beat == g_bp_after_beat;
}

bool bp_should_stall(uint8_t channel_bit, uint16_t burst, uint16_t beat)
{
    std::lock_guard<std::mutex> lock(g_bp_mutex);
    if (g_bp_cycles == 0) {
        return false;
    }
    if (g_bp_mode != SOCKET_BP_MODE_FIXED && g_bp_mode != SOCKET_BP_MODE_RANDOM) {
        return false;
    }
    if ((g_bp_channel & channel_bit) == 0) {
        return false;
    }
    if (!bp_burst_beat_match(burst, beat)) {
        return false;
    }
    if (g_bp_mode == SOCKET_BP_MODE_FIXED) {
        return true;
    }
    // LCG: stall roughly half of the matching beats.
    g_bp_rng = g_bp_rng * 1103515245u + 12345u;
    return ((g_bp_rng >> 16) & 1u) != 0;
}

// Wait for Python SYNC ack (or MSG_RESET / MSG_BP_CFG acting as ack) without advancing sc_time.
//
// This TB has no watchDog keep-alive. Under gated lockstep, DUT clocks stop
// issuing timed waits, so a pure wait(ack_event) can leave the SystemC event
// queue empty and sc_start() returns immediately. Delta-cycling here keeps the
// kernel alive until the OS rx thread sets g_have_ack (no sc_time advance).
void wait_for_ack(uint64_t expected_time_ns)
{
    while (true) {
        {
            std::lock_guard<std::mutex> lock(g_ack_mutex);
            if (g_have_ack) {
                if (g_pending_ack_time_ns == expected_time_ns) {
                    g_have_ack = false;
                    return;
                }
                // Stale / mismatched ack — discard and keep waiting.
                g_have_ack = false;
            }
        }
        sc_core::wait(sc_core::SC_ZERO_TIME);
    }
}

} // namespace

void socketSyncConfigureFromEnvironment()
{
    if (g_configured) {
        return;
    }
    g_configured = true;
    g_lockstep = env_enabled_default_true(std::getenv("PYSOCKET_LOCKSTEP"));
    bool quantum_from_env = false;
    if (const char *quantum_ns = std::getenv("PYSOCKET_SYNC_QUANTUM_NS")) {
        const auto ns = std::strtoull(quantum_ns, nullptr, 10);
        if (ns > 0) {
            g_quantum = sc_core::sc_time(static_cast<double>(ns), sc_core::SC_NS);
            quantum_from_env = true;
        }
    }
    if (!quantum_from_env) {
        g_quantum = sc_core::sc_time(static_cast<double>(simController::delayNSec), sc_core::SC_NS);
    }
}

bool socketSyncLockstepEnabled()
{
    socketSyncConfigureFromEnvironment();
    return g_lockstep.load(std::memory_order_acquire);
}

sc_core::sc_time socketSyncQuantum()
{
    socketSyncConfigureFromEnvironment();
    return effective_quantum();
}

uint64_t socketSyncScTimeNs()
{
    const sc_core::sc_time stamp = sc_core::sc_time_stamp();
    return static_cast<uint64_t>(stamp / sc_core::sc_time(1, sc_core::SC_NS));
}

uint64_t socketSyncRelativeTimeNs()
{
    const uint64_t now_ns = socketSyncScTimeNs();
    if (socketSyncLockstepEnabled() && g_lockstep_epoch_set) {
        return now_ns - g_lockstep_epoch_ns;
    }
    return now_ns;
}

uint64_t socketSyncObserveTimeNs()
{
    return socketSyncRelativeTimeNs();
}

bool socketSyncAtBoundary()
{
    return socketSyncLockstepEnabled() && g_at_boundary;
}

void socketSyncRegisterBoundaryEvent(const std::shared_ptr<ThreadSafeEvent> &event)
{
    if (!event) {
        return;
    }
    std::lock_guard<std::mutex> lock(g_boundary_events_mutex);
    g_boundary_events.push_back(event);
}

void socketSyncRegisterApbReqEvent(const std::shared_ptr<ThreadSafeEvent> &event)
{
    socketSyncRegisterBoundaryEvent(event);
}

bool socketSyncTimeGated()
{
    return socketSyncLockstepEnabled() && g_time_gated;
}

sc_core::sc_time socketSyncClockHalfPeriod()
{
    return sc_core::sc_time(0.5, sc_core::SC_NS);
}

void socketSyncAdvanceTime(sc_core::sc_time amount)
{
    if (amount <= sc_core::SC_ZERO_TIME) {
        return;
    }
    const sc_core::sc_time half = socketSyncClockHalfPeriod();
    sc_core::sc_time advanced = sc_core::SC_ZERO_TIME;
    while (advanced < amount) {
        sc_core::sc_time step = half;
        if (advanced + step > amount) {
            step = amount - advanced;
        }
        if (g_time_gated) {
            // Broadcast: every gated clock waiting on edge_event toggles once.
            edge_event().notify(sc_core::SC_ZERO_TIME);
        }
        sc_core::wait(step);
        advanced += step;
        time_tick_event().notify(sc_core::SC_ZERO_TIME);
    }
}

void socketSyncWaitClockEdge()
{
    sc_core::wait(edge_event());
}

void socketSyncNoteTimeAdvanced()
{
    time_tick_event().notify(sc_core::SC_ZERO_TIME);
}

const sc_core::sc_event &socketSyncTimeTickEvent()
{
    return time_tick_event();
}

bool socketSyncRstN()
{
    return g_rst_n;
}

const sc_core::sc_event &socketSyncRstNEvent()
{
    return rst_n_event();
}

void socketSyncRegisterModelReset(std::function<void()> cb)
{
    g_model_reset_cb = std::move(cb);
}

void socketSyncRegisterAxiValidSample(std::function<void(uint8_t &, uint8_t &)> cb)
{
    g_axi_valid_sample_cb = std::move(cb);
}

void socketSyncStallClocks(uint16_t clocks)
{
    if (clocks == 0) {
        return;
    }
    const sc_core::sc_time period =
        socketSyncClockHalfPeriod() + socketSyncClockHalfPeriod();
    // Under gated lockstep, drive clock edges so the DUT can progress while
    // WREADY/RVALID is held (plain wait() would advance sc_time without edges).
    if (g_time_gated) {
        socketSyncAdvanceTime(period * clocks);
        return;
    }
    sc_core::wait(period * clocks);
}

bool socketSyncBpShouldStallWready(uint16_t burst, uint16_t beat)
{
    return bp_should_stall(SOCKET_BP_CH_WREADY, burst, beat);
}

bool socketSyncBpShouldStallRvalid(uint16_t burst, uint16_t beat)
{
    return bp_should_stall(SOCKET_BP_CH_RVALID, burst, beat);
}

uint16_t socketSyncBpHoldCycles()
{
    std::lock_guard<std::mutex> lock(g_bp_mutex);
    if (g_bp_mode != SOCKET_BP_MODE_FIXED && g_bp_mode != SOCKET_BP_MODE_RANDOM) {
        return 0;
    }
    return g_bp_cycles;
}

void socketSyncStartRxThread()
{
    socketSyncConfigureFromEnvironment();
    if (!socketSyncLockstepEnabled()) {
        return;
    }

    const int fd = socketFactory::getFd(PYSOCKET_SYNC_IFC);
    if (fd < 0) {
        return;
    }

    g_ack_event = ThreadSafeEventFactory::newEvent("pysocket_sync_ack");
    g_ready_event = ThreadSafeEventFactory::newEvent("pysocket_sync_ready");
    auto running = std::make_shared<std::atomic<bool>>(true);

    constexpr size_t k_rx_buf =
        sizeof(socket_bp_cfg_st) > sizeof(socket_reset_st) ? sizeof(socket_bp_cfg_st)
                                                           : sizeof(socket_reset_st);

    std::thread rx_thread([running, fd]() {
        uint8_t msg_type = 0;
        uint16_t len = 0;
        alignas(8) uint8_t buf[k_rx_buf]{};
        while (running->load(std::memory_order_acquire)) {
            if (!socket_recv_msg(fd, msg_type, buf, len, static_cast<uint16_t>(sizeof(buf)))) {
                break;
            }
            if (msg_type == MSG_SHUTDOWN) {
                break;
            }
            if (msg_type == MSG_SYNC && len == 0) {
                g_python_ready = true;
                g_lockstep_epoch_ns = socketSyncScTimeNs();
                g_lockstep_epoch_set = true;
                g_ready_event->notify();
                continue;
            }
            if (msg_type == MSG_SYNC && len == sizeof(socket_sync_st)) {
                socket_sync_st sync{};
                std::memcpy(&sync, buf, sizeof(sync));
                {
                    std::lock_guard<std::mutex> lock(g_ack_mutex);
                    g_pending_ack_time_ns = sync.sc_time_ns;
                    g_have_ack = true;
                }
                g_ack_event->notify();
                continue;
            }
            if (msg_type == MSG_RESET && len == sizeof(socket_reset_st)) {
                socket_reset_st reset{};
                std::memcpy(&reset, buf, sizeof(reset));
                {
                    std::lock_guard<std::mutex> lock(g_reset_mutex);
                    g_reset_assert_cycles = reset.assert_cycles;
                    g_reset_settle_cycles = reset.settle_cycles;
                    g_reset_pending = true;
                }
                {
                    std::lock_guard<std::mutex> lock(g_ack_mutex);
                    g_pending_ack_time_ns = reset.sc_time_ns;
                    g_have_ack = true;
                }
                g_ack_event->notify();
                continue;
            }
            if (msg_type == MSG_BP_CFG && len == sizeof(socket_bp_cfg_st)) {
                socket_bp_cfg_st cfg{};
                std::memcpy(&cfg, buf, sizeof(cfg));
                {
                    std::lock_guard<std::mutex> lock(g_bp_mutex);
                    g_bp_pending_cfg = cfg;
                    g_bp_pending = true;
                }
                {
                    std::lock_guard<std::mutex> lock(g_ack_mutex);
                    g_pending_ack_time_ns = cfg.sc_time_ns;
                    g_have_ack = true;
                }
                g_ack_event->notify();
                continue;
            }
        }
        running->store(false, std::memory_order_release);
        g_ack_event->notify();
    });
    socketFactory::registerThread(PYSOCKET_SYNC_IFC, std::move(rx_thread));
}

void socketSyncQuantumThread()
{
    socketSyncConfigureFromEnvironment();

    if (!socketSyncLockstepEnabled()) {
        while (true) {
            wait(sc_core::sc_time(1, sc_core::SC_US));
        }
        return;
    }

    const int fd = socketFactory::getFd(PYSOCKET_SYNC_IFC);
    if (fd < 0 || !g_ack_event || !g_ready_event) {
        while (true) {
            wait(sc_core::sc_time(1, sc_core::SC_US));
        }
        return;
    }

    // Free-run clocks until Python is ready so reset and early DUT time can complete.
    while (!g_python_ready) {
        wait(g_ready_event->default_event());
    }

    // From here, only socketSyncAdvanceTime() may release DUT time.
    g_time_gated = true;
    // Match HDL reset_driver: come out of reset once Python is ready.
    set_rst_n(true);

    while (true) {
        const uint64_t boundary_ns = socketSyncRelativeTimeNs();
        begin_boundary(boundary_ns);

        socket_sync_st payload{};
        payload.sc_time_ns = boundary_ns;

        if (!socket_send_msg(fd, MSG_SYNC, &payload, static_cast<uint16_t>(sizeof(payload)))) {
            end_boundary();
            break;
        }

        wait_for_ack(payload.sc_time_ns);

        bool do_reset = false;
        bool do_bp = false;
        {
            std::lock_guard<std::mutex> lock(g_reset_mutex);
            do_reset = g_reset_pending;
        }
        {
            std::lock_guard<std::mutex> lock(g_bp_mutex);
            do_bp = g_bp_pending;
        }

        end_boundary();

        if (do_reset) {
            service_reset_pulse(fd);
            continue;
        }
        if (do_bp) {
            service_bp_cfg(fd);
            // Policy installed; advance this quantum like a normal SYNC ack.
        }

        // Sole timed waiter under lockstep: advances sc_time and drives clock edges.
        socketSyncAdvanceTime(effective_quantum());
    }
}
