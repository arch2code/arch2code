//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=dataGen --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=blockModuleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "bitTwiddling.h"
#include "q_assert.h"
#include <algorithm>
#include "instanceFactory.h"
#include "push_ack_channel.h"
// GENERATED_CODE_END
// user #includes here
// GENERATED_CODE_BEGIN --template=moduleExport
export module simple_ip_dataGen.block;
import simple_ip_dataGen.base;
import simple_ip;
// GENERATED_CODE_END
// user imports here
// GENERATED_CODE_BEGIN --template=classDecl
using namespace simple_ip_ns;
export SC_MODULE(dataGen), public blockBase, public dataGenBase
{
private:

public:

    dataGen(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~dataGen() override = default;

    // GENERATED_CODE_END
    // block implementation members

private:
    void driveOut(void);
};

// GENERATED_CODE_BEGIN --template=constructor --section=init
SC_HAS_PROCESS(dataGen);

// === Block factory registration (dataGen) ===
void register_dataGen_variants() {
    instanceFactory::registerBlock("dataGen_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<dataGen>(blockName, variant, bbMode)); }, "", "simple_ip");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _dataGen_registered = (register_dataGen_variants(), 0);
} // namespace
// === End block factory registration ===

dataGen::dataGen(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("dataGen", name(), bbMode)
        ,dataGenBase(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
    SC_THREAD(driveOut);
};

// Push a single marked word onto the non-parameterized boundary into uIp. The
// low data byte (0xA5) is the marker the firmware reads back through
// ipLastData; the push_ack thunker adapts this fixed-width payload onto uIp's
// parameterized ipDataIf (variant0 = marker 1 bit + data 8 bits).
void dataGen::driveOut(void)
{
    simpleData8St d{};
    d.data = 0xA5;
    d.marker = 1;
    log_.logPrint(std::format("{} pushing 0x{:x} marker {} on out", this->name(), (uint64_t)d.data, (uint64_t)d.marker), LOG_IMPORTANT);
    out->push(d);
};

