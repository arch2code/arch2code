//

// GENERATED_CODE_PARAM --block=rdvDrv --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=blockModuleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "instanceFactory.h"
#include "push_ack_channel.h"
// GENERATED_CODE_END
// user #includes here (global module fragment - attaches to the global module)
// Plain non-modular headers, including any whose definitions live in a .cpp.
// GENERATED_CODE_BEGIN --template=moduleExport
export module rdvTest_rdvDrv.block;
import rdvTest_rdvDrv.base;
import rdvTest_rdvTop;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=classDecl
using namespace rdvTest_rdvTop_ns;
export SC_MODULE(rdvDrv), public blockBase, public rdvDrvBase
{
private:

public:

    rdvDrv(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~rdvDrv() override = default;

    // GENERATED_CODE_END
    // block implementation members
private:
    static constexpr uint32_t SAMPLE_COUNT = 4;
    static constexpr uint32_t FIRST_DATA = 0x31;
    void drive(void);
};

// GENERATED_CODE_BEGIN --template=constructor --section=init
SC_HAS_PROCESS(rdvDrv);

// === Block factory registration (rdvDrv) ===
void register_rdvDrv_variants() {
    instanceFactory::registerBlock("rdvDrv_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<rdvDrv>(blockName, variant, bbMode)); }, "", "rdvTest");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _rdvDrv_registered = (register_rdvDrv_variants(), 0);
} // namespace
// === End block factory registration ===

rdvDrv::rdvDrv(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("rdvDrv", name(), bbMode)
        ,rdvDrvBase(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
    SC_THREAD(drive);
};

// Drives the same four samples into both leaf sites.
void rdvDrv::drive(void)
{
    for (uint32_t i = 0; i < SAMPLE_COUNT; i++) {
        rdvSt sample{};
        sample.data = FIRST_DATA + i;
        out->push(sample);
        out2->push(sample);
    }
}

