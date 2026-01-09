//copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE
#include "testController.h"

// GENERATED_CODE_PARAM --block=blockD
// GENERATED_CODE_BEGIN --template=constructor --section=init
#include "blockD.h"
SC_HAS_PROCESS(blockD);

blockD::registerBlock blockD::registerBlock_; //register the block with the factory

blockD::blockD(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("blockD", name(), bbMode)
        ,blockDBase(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
    SC_THREAD(memoryTest);
    SC_THREAD(blockBTableExtModel);
    
    // Model-backed storage for memory register blockBTableExt (BSIZE wordlines).
    // Default init: all zeros.
    blockBTableExt_shadow_.assign(BSIZE, seeSt());
}

void blockD::memoryTest(void)
{
    testController &controller = testController::GetInstance();
    
    std::string test_write = "test_mem_hier_blockd_write";
    controller.register_test_name(test_write);
    
    std::string test_read = "test_mem_hier_blockd_read";
    controller.register_test_name(test_read);

    // Wait for write test
    controller.wait_test(test_write, sc_time(1, SC_NS));
    
    bSizeSt addr;
    addr.index = 0;
    bigSt data;
    
    data.big = 0x1234567812345678;
    blockBTable1->request(true, addr, data);
    log_.logPrint("BlockD Write complete", LOG_ALWAYS);
    
    controller.test_complete(test_write);

    // Wait for read test
    controller.wait_test(test_read);
    
    blockBTable1->request(false, addr, data);
    
    if (data.big == 0x1234567812345678) {
        log_.logPrint("BlockD Read verify success", LOG_ALWAYS);
    } else {
        std::stringstream ss;
        ss << "BlockD Read verify failed. Expected 0x1234567812345678, got 0x" << std::hex << data.big;
        log_.logPrint(ss.str(), LOG_ALWAYS);
    }
    
    controller.test_complete(test_read);
}

void blockD::blockBTableExtModel(void)
{
    while (true) {
        bool isWrite = false;
        bSizeSt addr;
        seeSt data;

        // Wait for a request from the memory register port.
        blockBTableExt->reqReceive(isWrite, addr, data);

        const uint32_t idx = static_cast<uint32_t>(addr.index);
        if (idx >= blockBTableExt_shadow_.size()) {
            log_.logPrint(std::format("blockBTableExtModel: addr out of range idx={}", idx), LOG_ALWAYS);
            if (!isWrite) {
                blockBTableExt->complete(seeSt());
            }
            continue;
        }

        if (isWrite) {
            // Writes are acknowledged via complete with default constructed value
            blockBTableExt_shadow_[idx] = data;
            // For writes, complete is called automatically or we need to call it
            // (depending on interface semantics, but usually not needed for writes)
        } else {
            // Complete reads with the current model value.
            blockBTableExt->complete(blockBTableExt_shadow_[idx]);
        }
    }
}
