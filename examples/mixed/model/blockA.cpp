//copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE


// GENERATED_CODE_PARAM --block=blockA
// GENERATED_CODE_BEGIN --template=constructor --section=init
#include "blockA.h"
SC_HAS_PROCESS(blockA);

blockA::registerBlock blockA::registerBlock_; //register the block with the factory

void blockA::regHandler(void) { //handle register decode
    registerHandler< apbAddrSt, apbDataSt >(regs, apbReg, (1<<(6))-1); }

blockA::blockA(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("blockA", name(), bbMode)
        ,blockABase(name(), variant)
        ,regs(log_)
        ,roA()
        ,blockATableLocal_channel("blockA_blockATableLocal", "blockA")
        ,blockATableLocal_port("blockATableLocal_port")
        ,blockATableLocal_adapter(blockATableLocal_port)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    // register memory registers for FW access
    regs.addMemory( 0x0, 0x28, std::string(this->name()) + ".blockATableLocal", &blockATableLocal_adapter);
    // register registers for FW access
    regs.addRegister( 0x28, 1, "roA", &roA );
    // bind local memory register ports to channels
    blockATableLocal_port(blockATableLocal_channel);
    SC_THREAD(regHandler);
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
    
    // Initialize shadow storage for blockATableLocal with test values
    blockATableLocal_shadow_.assign(BSIZE, aRegSt());
    for (uint32_t i = 0; i < BSIZE; i++) {
        blockATableLocal_shadow_[i].a = i * 0x22;  // Different pattern than blockD (0x11)
    }
    
    SC_THREAD(startTest);
    SC_THREAD(blockATableLocalModel);
}

void blockA::startTest(void)
{
    startDone->notify();
}

void blockA::blockATableLocalModel(void)
{
    while (true) {
        bool isWrite = false;
        bSizeSt addr;
        aRegSt data;

        // Wait for a request from the memory register port
        blockATableLocal_channel.reqReceive(isWrite, addr, data);

        const uint32_t idx = static_cast<uint32_t>(addr.index);
        if (idx >= blockATableLocal_shadow_.size()) {
            log_.logPrint(std::format("blockATableLocalModel: addr out of range idx={}", idx), LOG_ALWAYS);
            if (!isWrite) {
                blockATableLocal_channel.complete(aRegSt());
            }
            continue;
        }

        if (isWrite) {
            // Store write data to shadow storage
            blockATableLocal_shadow_[idx] = data;
            log_.logPrint(std::format("blockATableLocalModel: Write idx={} val=0x{:x}", idx, data.a), LOG_DEBUG);
        } else {
            // Complete reads with the current model value
            blockATableLocal_channel.complete(blockATableLocal_shadow_[idx]);
            log_.logPrint(std::format("blockATableLocalModel: Read idx={} val=0x{:x}", idx, blockATableLocal_shadow_[idx].a), LOG_DEBUG);
        }
    }
}
