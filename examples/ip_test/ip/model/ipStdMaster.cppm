//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=ipStdMaster --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=blockModuleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "instanceFactory.h"
#include "apb_channel.h"
// GENERATED_CODE_END
// user #includes here
// GENERATED_CODE_BEGIN --template=moduleExport
export module ip_ipStdMaster.block;
import ip_ipStdMaster.base;
import ip;
// GENERATED_CODE_END
// user imports here
// GENERATED_CODE_BEGIN --template=classDecl
using namespace ip_ns;
export SC_MODULE(ipStdMaster), public blockBase, public ipStdMasterBase
{
private:

public:

    ipStdMaster(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~ipStdMaster() override = default;

    // GENERATED_CODE_END
    // block implementation members

};

// GENERATED_CODE_BEGIN --template=constructor --section=init
SC_HAS_PROCESS(ipStdMaster);

// === Block factory registration (ipStdMaster) ===
void register_ipStdMaster_variants() {
    instanceFactory::registerBlock("ipStdMaster_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<ipStdMaster>(blockName, variant, bbMode)); }, "", "ip");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _ipStdMaster_registered = (register_ipStdMaster_variants(), 0);
} // namespace
// === End block factory registration ===

ipStdMaster::ipStdMaster(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("ipStdMaster", name(), bbMode)
        ,ipStdMasterBase(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
};

