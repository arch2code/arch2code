#ifndef BRIDGESTDTOP_H
#define BRIDGESTDTOP_H

//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

#include "systemc.h"

// GENERATED_CODE_PARAM --block=bridgeStdTop
// GENERATED_CODE_BEGIN --template=classDecl
#include "logging.h"
#include "instanceFactory.h"
import bridgeStdTop.base;
#include "apb_channel.h"
#include "push_ack_channel.h"
import ipBridge;
using namespace ipBridge_ns;
import shared_types;
using namespace shared_types_ns;
//contained instances base module imports
import cpu.base;
import bridgeDriver.base;
import ipBridge.base;

SC_MODULE(bridgeStdTop), public blockBase, public bridgeStdTopBase
{
private:

public:
    // channels
    // Non-parameterized 8-bit Q10 bridge data interface
    push_ack_channel< data8St > out8;
    // Non-parameterized 70-bit Q10 bridge data interface
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

#endif //BRIDGESTDTOP_H
