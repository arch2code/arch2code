//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=bridgeStdTop
// GENERATED_CODE_BEGIN --template=constructor --section=init
#include "bridgeStdTop.h"
import cpu.base;
import bridgeDriver.base;
import ipBridge.base;
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
        ,uCpu(std::dynamic_pointer_cast<cpuBase>(instanceFactory::createInstance(name(), "uCpu", "cpu", "", "ipBridge")))
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

