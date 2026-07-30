//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=blockA --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=blockModuleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "bitTwiddling.h"
#include "q_assert.h"
#include <algorithm>
#include "instanceFactory.h"
#include "apb_channel.h"
#include "notify_ack_channel.h"
#include "rdy_vld_channel.h"
#include "req_ack_channel.h"
#include "addressMap.h"
#include "hwRegister.h"
#include "hwMemory.h"
// GENERATED_CODE_END
// user #includes here
// GENERATED_CODE_BEGIN --template=moduleExport
export module mixed_blockA.block;
import mixed_blockA.base;
import mixed;
import mixed_mixedInclude;
// GENERATED_CODE_END
// user imports here
// GENERATED_CODE_BEGIN --template=classDecl
import mixed_mixedBlockC;
using namespace mixed_ns;
using namespace mixed_mixedInclude_ns;
using namespace mixed_mixedBlockC_ns;

export SC_MODULE(blockA), public blockBase, public blockABase
{
private:
    void regHandler(void);
    addressMap _a2cRegs;

public:

    //registers
    hwRegister< aRegSt, 4 > roA; // A Read Only register

    //local memory register infrastructure
    memory_channel< bSizeSt, aRegSt > blockATableLocal_channel;
    memory_out< bSizeSt, aRegSt > blockATableLocal_port;
    hwMemoryPort< bSizeSt, aRegSt > blockATableLocal_adapter;
    memory_channel< bSizeSt, test37BitRegSt > blockATable37Bit_channel;
    memory_out< bSizeSt, test37BitRegSt > blockATable37Bit_port;
    hwMemoryPort< bSizeSt, test37BitRegSt > blockATable37Bit_adapter;

    blockA(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~blockA() override = default;

    // GENERATED_CODE_END
    // block implementation members

    std::vector<aRegSt> blockATableLocal_shadow_;  // Shadow storage for local memory register
    std::vector<test37BitRegSt> blockATable37Bit_shadow_;  // Shadow storage for 37-bit memory register
    void startTest(void);
    void blockATableLocalModel(void);  // Service thread for local memory register
    void blockATable37BitModel(void);  // Service thread for 37-bit memory register
};

// GENERATED_CODE_BEGIN --template=constructor --section=init
SC_HAS_PROCESS(blockA);

// === Block factory registration (blockA) ===
void register_blockA_variants() {
    instanceFactory::registerBlock("blockA_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<blockA>(blockName, variant, bbMode)); }, "", "mixed");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _blockA_registered = (register_blockA_variants(), 0);
} // namespace
// === End block factory registration ===

void blockA::regHandler(void) { //handle register decode
    registerHandler< apbAddrSt, apbDataSt >(_a2cRegs, apbReg, (1<<(8))-1); }

blockA::blockA(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("blockA", name(), bbMode)
        ,blockABase(name(), variant)
        ,_a2cRegs(log_)
        ,roA()
        ,blockATableLocal_channel("blockA_blockATableLocal", "blockA")
        ,blockATableLocal_port("blockATableLocal_port")
        ,blockATableLocal_adapter(blockATableLocal_port)
        ,blockATable37Bit_channel("blockA_blockATable37Bit", "blockA")
        ,blockATable37Bit_port("blockATable37Bit_port")
        ,blockATable37Bit_adapter(blockATable37Bit_port)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    // Generated register/memory address offsets
    constexpr uint64_t REG_ADDR_BLOCKA_BLOCKATABLE37BIT = 0x0;
    constexpr uint64_t REG_ADDR_BLOCKA_BLOCKATABLELOCAL = 0x80;
    constexpr uint64_t REG_ADDR_BLOCKA_ROA = 0xc0;

    // register memories for FW access
    _a2cRegs.addMemory( REG_ADDR_BLOCKA_BLOCKATABLE37BIT, test37BitRegSt::_byteWidth, BSIZE, std::string(this->name()) + ".blockATable37Bit", &blockATable37Bit_adapter);
    _a2cRegs.addMemory( REG_ADDR_BLOCKA_BLOCKATABLELOCAL, aRegSt::_byteWidth, BSIZE, std::string(this->name()) + ".blockATableLocal", &blockATableLocal_adapter);
    // register registers for FW access
    _a2cRegs.addRegister( REG_ADDR_BLOCKA_ROA, 1, "roA", &roA );
    // bind local memory register ports to channels
    blockATableLocal_port(blockATableLocal_channel);
    blockATable37Bit_port(blockATable37Bit_channel);
    SC_THREAD(regHandler);
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
    // Initialize shadow storage for blockATableLocal with test values
    blockATableLocal_shadow_.assign(BSIZE, aRegSt());
    for (uint32_t i = 0; i < BSIZE; i++) {
        blockATableLocal_shadow_[i].a = i * 0x22;  // Different pattern than blockD (0x11)
    }
    
    // Initialize shadow storage for blockATable37Bit with test pattern
    blockATable37Bit_shadow_.assign(BSIZE, test37BitRegSt());
    for (uint32_t i = 0; i < BSIZE; i++) {
        uint64_t val = (static_cast<uint64_t>(i) << 32) | i;
        blockATable37Bit_shadow_[i].value37 = val & 0x1FFFFFFFFF;
    }
    
    SC_THREAD(startTest);
    SC_THREAD(blockATableLocalModel);
    SC_THREAD(blockATable37BitModel);
};

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

void blockA::blockATable37BitModel(void)
{
    while (true) {
        bool isWrite = false;
        bSizeSt addr;
        test37BitRegSt data;

        // Wait for a request from the memory register port
        blockATable37Bit_channel.reqReceive(isWrite, addr, data);

        const uint32_t idx = static_cast<uint32_t>(addr.index);
        if (idx >= blockATable37Bit_shadow_.size()) {
            log_.logPrint(std::format("blockATable37BitModel: addr out of range idx={}", idx), LOG_ALWAYS);
            if (!isWrite) {
                blockATable37Bit_channel.complete(test37BitRegSt());
            }
            continue;
        }

        if (isWrite) {
            // Store write data to shadow storage
            blockATable37Bit_shadow_[idx] = data;
            log_.logPrint(std::format("blockATable37BitModel: Write idx={} val=0x{:x}", idx, data.value37), LOG_DEBUG);
        } else {
            // Complete reads with the current model value
            blockATable37Bit_channel.complete(blockATable37Bit_shadow_[idx]);
            log_.logPrint(std::format("blockATable37BitModel: Read idx={} val=0x{:x}", idx, blockATable37Bit_shadow_[idx].value37), LOG_DEBUG);
        }
    }
}

