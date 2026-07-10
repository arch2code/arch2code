// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

#include "socketSync.h"

#include "asyncEvent.h"
#include "simController.h"
#include "socketFactory.h"

#include <atomic>
#include <cstdlib>
#include <cstring>
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

    std::lock_guard<std::mutex> lock(g_boundary_events_mutex);
    for (const auto &event : g_boundary_events) {
        if (event) {
            event->notify();
        }
    }
}

void end_boundary()
{
    g_at_boundary = false;
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
    return g_quantum;
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

    std::thread rx_thread([running, fd]() {
        uint8_t msg_type = 0;
        uint16_t len = 0;
        socket_sync_st sync{};
        while (running->load(std::memory_order_acquire)) {
            if (!socket_recv_msg(fd, msg_type, &sync, len, static_cast<uint16_t>(sizeof(socket_sync_st)))) {
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
                {
                    std::lock_guard<std::mutex> lock(g_ack_mutex);
                    g_pending_ack_time_ns = sync.sc_time_ns;
                    g_have_ack = true;
                }
                g_ack_event->notify();
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

    while (!g_python_ready) {
        wait(g_ready_event->default_event());
    }

    while (true) {
        const uint64_t boundary_ns = socketSyncRelativeTimeNs();
        begin_boundary(boundary_ns);

        socket_sync_st payload{};
        payload.sc_time_ns = boundary_ns;

        if (!socket_send_msg(fd, MSG_SYNC, &payload, static_cast<uint16_t>(sizeof(payload)))) {
            end_boundary();
            break;
        }

        const uint64_t expected_time_ns = payload.sc_time_ns;
        while (true) {
            wait(g_ack_event->default_event());

            bool got_ack = false;
            {
                std::lock_guard<std::mutex> lock(g_ack_mutex);
                if (g_have_ack) {
                    if (g_pending_ack_time_ns != expected_time_ns) {
                        continue;
                    }
                    g_have_ack = false;
                    got_ack = true;
                }
            }
            if (got_ack) {
                break;
            }
        }

        end_boundary();
        wait(g_quantum);
    }
}
