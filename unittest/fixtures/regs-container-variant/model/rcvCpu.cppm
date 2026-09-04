//

// GENERATED_CODE_PARAM --block=rcvCpu --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=blockModuleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "instanceFactory.h"
#include "apb_channel.h"
// GENERATED_CODE_END
// user #includes here (global module fragment - attaches to the global module)
// Plain non-modular headers, including any whose definitions live in a .cpp.
#include "q_assert.h"
#include "rcvRegAddresses.h"
// GENERATED_CODE_BEGIN --template=moduleExport
export module rcvTest_rcvCpu.block;
import rcvTest_rcvCpu.base;
import rcvTest_rcvTop;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
import a2c.endOfTest;
// GENERATED_CODE_BEGIN --template=classDecl
using namespace rcvTest_rcvTop_ns;
export SC_MODULE(rcvCpu), public blockBase, public rcvCpuBase
{
private:

public:

    rcvCpu(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~rcvCpu() override = default;

    // GENERATED_CODE_END
    // block implementation members
private:
    static constexpr uint32_t CFG_VALUE = 0xABC;
    void fwTest(void);
    endOfTest m_eot;
};

// GENERATED_CODE_BEGIN --template=constructor --section=init
SC_HAS_PROCESS(rcvCpu);

// === Block factory registration (rcvCpu) ===
void register_rcvCpu_variants() {
    instanceFactory::registerBlock("rcvCpu_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<rcvCpu>(blockName, variant, bbMode)); }, "", "rcvTest");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _rcvCpu_registered = (register_rcvCpu_variants(), 0);
} // namespace
// === End block factory registration ===

rcvCpu::rcvCpu(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("rcvCpu", name(), bbMode)
        ,rcvCpuBase(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
    SC_THREAD(fwTest);
};

// Writes cfg over APB and reads it back, so the run only passes when the
// synthesised handler decoded the access.
void rcvCpu::fwTest(void)
{
    m_eot.registerVoter();
    apbAddrSt addr;
    apbDataSt data;

    addr.address = BASE_ADDR_URCVLEAF + REG_RCVLEAF_CFG;
    data.data = CFG_VALUE;
    cpu_main->request(true, addr, data);

    addr.address = BASE_ADDR_URCVLEAF + REG_RCVLEAF_CFG;
    data.data = 0;
    cpu_main->request(false, addr, data);

    const uint64_t readback = (uint64_t)data.data;
    log_.logPrint(std::format("cfg readback 0x{:x}", readback), LOG_IMPORTANT);
    Q_ASSERT(readback == CFG_VALUE,
             "cfg did not read back what firmware wrote, so the register "
             "handler did not serve the access");
    m_eot.setEndOfTest(true);
}
