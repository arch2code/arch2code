//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=ipStdDecode --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=blockModuleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "bitTwiddling.h"
#include "q_assert.h"
#include <algorithm>
#include "instanceFactory.h"
#include "apb_channel.h"
#include "apbBusDecode.h"
// GENERATED_CODE_END
// user #includes here
// GENERATED_CODE_BEGIN --template=moduleExport
export module ip_ipStdDecode.block;
import ip_ipStdDecode.base;
import ip;
// GENERATED_CODE_END
// user imports here
// GENERATED_CODE_BEGIN --template=classDecl
using namespace ip_ns;
export SC_MODULE(ipStdDecode), public blockBase, public ipStdDecodeBase
{
private:
    void routerDecode(void);
    abpBusDecode< ipRegAddrSt, ipRegDataSt > decoder;

public:

    ipStdDecode(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~ipStdDecode() override = default;

    // GENERATED_CODE_END
    // block implementation members

};

// GENERATED_CODE_BEGIN --template=constructor --section=init
SC_HAS_PROCESS(ipStdDecode);

// === Block factory registration (ipStdDecode) ===
void register_ipStdDecode_variants() {
    instanceFactory::registerBlock("ipStdDecode_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<ipStdDecode>(blockName, variant, bbMode)); }, "", "ip");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _ipStdDecode_registered = (register_ipStdDecode_variants(), 0);
} // namespace
// === End block factory registration ===

void ipStdDecode::routerDecode(void) //handle apb routing for register
{
    log_.logPrint(std::format("SystemC Thread:{} started", __func__));
    decoder.decodeThread();
}

ipStdDecode::ipStdDecode(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("ipStdDecode", name(), bbMode)
        ,ipStdDecodeBase(name(), variant)
        ,decoder(16, 24, ipReg, {
            &ipReg_uIp})
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    SC_THREAD(routerDecode);
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
};

