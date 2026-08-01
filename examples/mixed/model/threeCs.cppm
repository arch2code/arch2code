//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=threeCs --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=blockModuleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "bitTwiddling.h"
#include "q_assert.h"
#include <algorithm>
#include "instanceFactory.h"
#include "rdy_vld_channel.h"
// GENERATED_CODE_END
// user #includes here
// GENERATED_CODE_BEGIN --template=moduleExport
export module mixed_threeCs.block;
import mixed_threeCs.base;
import mixed_blockC.base;
import mixed_mixedBlockC;
using namespace mixed_mixedBlockC_ns;
// GENERATED_CODE_END
// user imports here
// GENERATED_CODE_BEGIN --template=classDecl
export SC_MODULE(threeCs), public blockBase, public threeCsBase
{
private:

public:
    //instances contained in block
    std::shared_ptr<blockCBase> uBlockC0;
    std::shared_ptr<blockCBase> uBlockC1;
    std::shared_ptr<blockCBase> uBlockC2;

    threeCs(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~threeCs() override = default;

    // GENERATED_CODE_END
    // block implementation members

};

// GENERATED_CODE_BEGIN --template=constructor --section=init
SC_HAS_PROCESS(threeCs);

// === Block factory registration (threeCs) ===
void register_threeCs_variants() {
    instanceFactory::registerBlock("threeCs_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<threeCs>(blockName, variant, bbMode)); }, "", "mixed");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _threeCs_registered = (register_threeCs_variants(), 0);
} // namespace
// === End block factory registration ===

threeCs::threeCs(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("threeCs", name(), bbMode)
        ,threeCsBase(name(), variant)
        ,uBlockC0(std::dynamic_pointer_cast<blockCBase>(instanceFactory::createInstance(name(), "uBlockC0", "blockC", "", "mixed")))
        ,uBlockC1(std::dynamic_pointer_cast<blockCBase>(instanceFactory::createInstance(name(), "uBlockC1", "blockC", "", "mixed")))
        ,uBlockC2(std::dynamic_pointer_cast<blockCBase>(instanceFactory::createInstance(name(), "uBlockC2", "blockC", "", "mixed")))
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
// hierarchical connections: instance port->parent port (dst->dst, src-src without channels)
    uBlockC0->see(see0);
    uBlockC1->see(see1);
    uBlockC2->see(see2);
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
};

