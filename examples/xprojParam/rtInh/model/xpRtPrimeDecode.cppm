//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=xpRtPrimeDecode --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=blockModuleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "instanceFactory.h"
#include "apb_channel.h"
#include "apbBusDecode.h"
// GENERATED_CODE_END
// user #includes here (global module fragment - attaches to the global module)
// Plain non-modular headers, including any whose definitions live in a .cpp.
// GENERATED_CODE_BEGIN --template=moduleExport
export module xpRtInh_xpRtPrimeDecode.block;
import xpRtInh_xpRtPrimeDecode.base;
import common_shared_types;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=classDecl
using namespace common_shared_types_ns;
export SC_MODULE(xpRtPrimeDecode), public blockBase, public xpRtPrimeDecodeBase
{
private:
    void routerDecode(void);
    abpBusDecode< apbAddrSt, apbDataSt > decoder;

public:

    xpRtPrimeDecode(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~xpRtPrimeDecode() override = default;

    // GENERATED_CODE_END
    // block implementation members

};

// GENERATED_CODE_BEGIN --template=constructor --section=init
SC_HAS_PROCESS(xpRtPrimeDecode);

// === Block factory registration (xpRtPrimeDecode) ===
void register_xpRtPrimeDecode_variants() {
    instanceFactory::registerBlock("xpRtPrimeDecode_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<xpRtPrimeDecode>(blockName, variant, bbMode)); }, "", "xpRtInh");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _xpRtPrimeDecode_registered = (register_xpRtPrimeDecode_variants(), 0);
} // namespace
// === End block factory registration ===

void xpRtPrimeDecode::routerDecode(void) //handle apb routing for register
{
    log_.logPrint(std::format("SystemC Thread:{} started", __func__));
    decoder.decodeThread();
}

xpRtPrimeDecode::xpRtPrimeDecode(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("xpRtPrimeDecode", name(), bbMode)
        ,xpRtPrimeDecodeBase(name(), variant)
        ,decoder(16, 24, cpu_main, {
            &apbReg_uWrap})
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    SC_THREAD(routerDecode);
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
};

