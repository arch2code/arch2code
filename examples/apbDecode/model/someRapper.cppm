//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=someRapper --mode=module
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
// user #includes here
// GENERATED_CODE_BEGIN --template=moduleExport
export module apbDecode_someRapper.block;
import apbDecode_someRapper.base;
import apbDecode;
import apbDecode.base;
import apbDecode_blockA.base;
import apbDecode_blockB.base;
// GENERATED_CODE_END
// user imports here
// GENERATED_CODE_BEGIN --template=classDecl
using namespace apbDecode_ns;

export SC_MODULE(someRapper), public blockBase, public someRapperBase
{
private:

public:
    // channels
    // CPU access to SoC registers in the design
    apb_channel< apbAddrSt, apbDataSt > apbReg_uBlockA;
    // CPU access to SoC registers in the design
    apb_channel< apbAddrSt, apbDataSt > apbReg_uBlockB;

    //instances contained in block
    std::shared_ptr<apbDecodeBase> uAPBDecode;
    std::shared_ptr<blockABase> uBlockA;
    std::shared_ptr<blockBBase> uBlockB;

    someRapper(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~someRapper() override = default;

    // GENERATED_CODE_END
    // block implementation members

};

// GENERATED_CODE_BEGIN --template=constructor --section=init
SC_HAS_PROCESS(someRapper);

// === Block factory registration (someRapper) ===
void register_someRapper_variants() {
    instanceFactory::registerBlock("someRapper_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<someRapper>(blockName, variant, bbMode)); }, "", "apbDecode");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _someRapper_registered = (register_someRapper_variants(), 0);
} // namespace
// === End block factory registration ===

someRapper::someRapper(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("someRapper", name(), bbMode)
        ,someRapperBase(name(), variant)
        ,apbReg_uBlockA("blockA_apbReg_uBlockA", "apbDecode")
        ,apbReg_uBlockB("blockB_apbReg_uBlockB", "apbDecode")
        ,uAPBDecode(std::dynamic_pointer_cast<apbDecodeBase>(instanceFactory::createInstance(name(), "uAPBDecode", "apbDecode", "", "apbDecode")))
        ,uBlockA(std::dynamic_pointer_cast<blockABase>(instanceFactory::createInstance(name(), "uBlockA", "blockA", "", "apbDecode")))
        ,uBlockB(std::dynamic_pointer_cast<blockBBase>(instanceFactory::createInstance(name(), "uBlockB", "blockB", "", "apbDecode")))
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
// hierarchical connections: instance port->parent port (dst->dst, src-src without channels)
    uAPBDecode->apbReg(apbReg);
    // instance to instance connections via channel
    uAPBDecode->apbReg_uBlockA(apbReg_uBlockA);
    uBlockA->apbReg(apbReg_uBlockA);
    uAPBDecode->apbReg_uBlockB(apbReg_uBlockB);
    uBlockB->apbReg(apbReg_uBlockB);
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
};

