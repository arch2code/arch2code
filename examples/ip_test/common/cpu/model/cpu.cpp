//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

#include "modelComm.h"

// GENERATED_CODE_PARAM --block=cpu
// GENERATED_CODE_BEGIN --template=constructor --section=init
#include "cpu.h"
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

