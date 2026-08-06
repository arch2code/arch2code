//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=bridgeStdTop --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=blockModuleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "bitTwiddling.h"
#include "q_assert.h"
#include <algorithm>
#include "instanceFactory.h"
#include "apb_channel.h"
#include "push_ack_channel.h"
// GENERATED_CODE_END
// user #includes here
// GENERATED_CODE_BEGIN --template=moduleExport
export module ipBridge_bridgeStdTop.block;
import ipBridge_bridgeStdTop.base;
import ipBridge;
import common_shared_types;
import common_cpu.base;
import ipBridge_bridgeDriver.base;
import ipBridge.base;
// GENERATED_CODE_END
// user imports here
// GENERATED_CODE_BEGIN --template=classDecl
using namespace ipBridge_ns;
using namespace common_shared_types_ns;
export SC_MODULE(bridgeStdTop), public blockBase, public bridgeStdTopBase
{
private:

public:
    // channels
    // Non-parameterized 8-bit bridge data interface
    push_ack_channel< data8St > out8;
    // Non-parameterized 70-bit bridge data interface
    push_ack_channel< data70St > out70;
    // CPU access to registers via APB
    apb_channel< apbAddrSt, apbDataSt > cpu_main;

    //instances contained in block
    std::shared_ptr<cpuBase> uCpu;
    std::shared_ptr<bridgeDriverBase> uBridgeDriver;
    std::shared_ptr<ipBridgeBase> uBridge;

    bridgeStdTop(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~bridgeStdTop() override = default;

    // GENERATED_CODE_END
    // block implementation members

};

// GENERATED_CODE_BEGIN --template=constructor --section=init
SC_HAS_PROCESS(bridgeStdTop);

// === Block factory registration (bridgeStdTop) ===
void register_bridgeStdTop_variants() {
    instanceFactory::registerBlock("bridgeStdTop_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<bridgeStdTop>(blockName, variant, bbMode)); }, "", "ipBridge");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _bridgeStdTop_registered = (register_bridgeStdTop_variants(), 0);
} // namespace
// === End block factory registration ===

bridgeStdTop::bridgeStdTop(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("bridgeStdTop", name(), bbMode)
        ,bridgeStdTopBase(name(), variant)
        ,out8("ipBridge_out8", "bridgeDriver")
        ,out70("ipBridge_out70", "bridgeDriver")
        ,cpu_main("ipBridge_cpu_main", "cpu")
        ,uCpu(std::dynamic_pointer_cast<cpuBase>(instanceFactory::createInstance(name(), "uCpu", "cpu", "", "common")))
        ,uBridgeDriver(std::dynamic_pointer_cast<bridgeDriverBase>(instanceFactory::createInstance(name(), "uBridgeDriver", "bridgeDriver", "", "ipBridge")))
        ,uBridge(std::dynamic_pointer_cast<ipBridgeBase>(instanceFactory::createInstance(name(), "uBridge", "ipBridge", "", "ipBridge")))
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    // instance to instance connections via channel
    uBridgeDriver->out8(out8);
    uBridge->data8In(out8);
    uBridgeDriver->out70(out70);
    uBridge->data70In(out70);
    uCpu->cpu_main(cpu_main);
    uBridge->apbReg(cpu_main);
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
};

