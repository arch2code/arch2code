//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=subBlock --mode=module
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
export module nested_subBlock.block;
import nested_subBlock.base;
import nested;
// GENERATED_CODE_END
// user imports here
// GENERATED_CODE_BEGIN --template=classDecl
using namespace nested_ns;
export SC_MODULE(subBlock), public blockBase, public subBlockBase
{
private:

public:

    subBlock(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~subBlock() override = default;

    // GENERATED_CODE_END
    // block implementation members

    void forwarder(void);
};

// GENERATED_CODE_BEGIN --template=constructor --section=init
SC_HAS_PROCESS(subBlock);

// === Block factory registration (subBlock) ===
void register_subBlock_variants() {
    instanceFactory::registerBlock("subBlock_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<subBlock>(blockName, variant, bbMode)); }, "", "nested");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _subBlock_registered = (register_subBlock_variants(), 0);
} // namespace
// === End block factory registration ===

subBlock::subBlock(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("subBlock", name(), bbMode)
        ,subBlockBase(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
    SC_THREAD(forwarder)
};

// this module just takes data from the input and sends it to the output
void subBlock::forwarder()
{
    test_st data;
    data.a = 0;
    wait(SC_ZERO_TIME);
    while (true)
    {
        dst->read(data);
        std::cout << "write " << this->name() << " " << data.a << endl;
        src->write(data);
    }
}

