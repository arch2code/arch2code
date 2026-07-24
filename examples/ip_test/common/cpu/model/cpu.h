#ifndef CPU_H
#define CPU_H

//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

#include "systemc.h"
#include "asyncEvent.h"
#include "workerThread.h"

// GENERATED_CODE_PARAM --block=cpu
// GENERATED_CODE_BEGIN --template=classDecl
#include "logging.h"
#include "instanceFactory.h"
import cpu.base;
#include "apb_channel.h"
import shared_types;
using namespace shared_types_ns;

SC_MODULE(cpu), public blockBase, public cpuBase
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

#endif //CPU_H
