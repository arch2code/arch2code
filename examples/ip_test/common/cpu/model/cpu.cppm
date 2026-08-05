//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=cpu --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=blockModuleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "bitTwiddling.h"
#include "q_assert.h"
#include <algorithm>
#include "instanceFactory.h"
#include "apb_channel.h"
// GENERATED_CODE_END
#include "asyncEvent.h"
#include "workerThread.h"
#include "modelComm.h"
// user #includes here
// GENERATED_CODE_BEGIN --template=moduleExport
export module common_cpu.block;
import common_cpu.base;
import common_shared_types;
// GENERATED_CODE_END
// user imports here
// GENERATED_CODE_BEGIN --template=classDecl
using namespace common_shared_types_ns;
export SC_MODULE(cpu), public blockBase, public cpuBase
{
private:

public:

    cpu(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~cpu() override = default;

    // GENERATED_CODE_END
    // block implementation members

    // Generic firmware register-access bridge. The firmware (running on a worker
    // thread) issues global regWrite32 / regRead32 (bsp/regRdWr.h), which marshal
    // accesses onto the cross-thread regAccessQueue. This listener drains that
    // queue and drives each access onto the apbReg master port (cpu_main), pushing
    // read responses back and waking the firmware worker. Mirrors the pro
    // gold-standard lmmi_m_drv::regWriteListener; carries no design-specific logic.
    void regWriteListener(void);

    // Cross-thread event the regRdWr queue notifies when firmware pushes a request
    // (shared by name with bsp/regRdWr.cpp via the ThreadSafeEvent factory).
    std::shared_ptr<ThreadSafeEvent> regWriteEvent;
    // Worker event used to wake the firmware ("fw") worker when a read response is
    // ready or its queue drained. Resolved lazily on first drain so a consumer that
    // registers no "fw" worker (e.g. a bus master with no firmware program) neither
    // faults nor hangs: with no firmware, nothing is ever enqueued and this stays
    // null.
    std::shared_ptr<workerEvent> fwEvent;
};

// GENERATED_CODE_BEGIN --template=constructor --section=init
SC_HAS_PROCESS(cpu);

// === Block factory registration (cpu) ===
void register_cpu_variants() {
    instanceFactory::registerBlock("cpu_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<cpu>(blockName, variant, bbMode)); }, "", "common");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _cpu_registered = (register_cpu_variants(), 0);
} // namespace
// === End block factory registration ===

cpu::cpu(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("cpu", name(), bbMode)
        ,cpuBase(name(), variant)
// GENERATED_CODE_END
        ,regWriteEvent(ThreadSafeEventFactory::newEvent("regWriteEvent"))
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
    SC_THREAD(regWriteListener);
};

void cpu::regWriteListener(void)
{
    log_.logPrint(std::format("SystemC Thread:{} started", __func__));
    while (true)
    {
        while (regAccessQueue.empty())
        {
            wait(regWriteEvent->default_event());
        }
        regAccessSt req;
        regAccessQueue.pop(req);

        // A dequeued request implies a firmware worker enqueued it, so the "fw"
        // worker event exists; resolve it here on first use (a consumer with no
        // firmware never reaches this point).
        if (!fwEvent)
        {
            fwEvent = workerFactory::getWorkerEvent("fw");
        }

        // Translate the firmware register access into an APB master transaction.
        apbAddrSt addr;
        apbDataSt data;
        addr.address = req.address;
        data.data = req.value;
        cpu_main->request(req.isWrite, addr, data);

        if (!req.isWrite)
        {
            regReadResponseSt resp;
            resp.value = (uint32_t)data.data;
            bool pushResult = regReadResponseQueue.push(resp);
            Q_ASSERT(pushResult, "regReadResponseQueue push failed");
            fwEvent->notify("regReadResponseQueue");
        }
        if (regAccessQueue.empty())
        {
            fwEvent->notify("regAccessQueueEmpty");
        }
    }
};

