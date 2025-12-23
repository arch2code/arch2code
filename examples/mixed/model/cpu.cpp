// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE
#include "testController.h"
#include "regAddresses.h"

// GENERATED_CODE_PARAM --block=cpu
// GENERATED_CODE_BEGIN --template=constructor --section=init
#include "cpu.h"
SC_HAS_PROCESS(cpu);

cpu::registerBlock cpu::registerBlock_; //register the block with the factory

cpu::cpu(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("cpu", name(), bbMode)
        ,cpuBase(name(), variant)
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
    SC_THREAD(fwTest);

}

void cpu::fwTest(void)
{
    testController &controller = testController::GetInstance();
    
    std::string test_read = "test_mem_hier_cpu_read";
    controller.register_test_name(test_read);

    std::string test_write = "test_mem_hier_cpu_write";
    controller.register_test_name(test_write);

    std::string test_ext = "test_mem_hier_cpu_ext_rw";
    controller.register_test_name(test_ext);

    // Wait for read test
    controller.wait_test(test_read, sc_core::sc_time(1, sc_core::SC_NS));
    
    apbAddrSt addr;
    apbDataSt data;
    
    // Read and verify 0x1234567812345678
    uint32_t valLow, valHigh;
    
    addr.address = BASE_ADDR_UBLOCKB + REG_BLOCKB_BLOCKBTABLE1 + 0x0;
    cpu_main->request(false, addr, data);
    valLow = data.data;
    
    addr.address = BASE_ADDR_UBLOCKB + REG_BLOCKB_BLOCKBTABLE1 + 0x4;
    cpu_main->request(false, addr, data);
    valHigh = data.data;
    
    if (valLow == 0x12345678 && valHigh == 0x12345678) {
         log_.logPrint("CPU Read verify success", LOG_ALWAYS);
    } else {
         std::stringstream ss;
         ss << "CPU Read verify failed. Expected 0x1234567812345678, got 0x" 
            << std::hex << valHigh << std::setw(8) << std::setfill('0') << valLow;
         log_.logPrint(ss.str(), LOG_ALWAYS);
    }
    
    controller.test_complete(test_read);

    // Wait for write test
    controller.wait_test(test_write, sc_core::sc_time(1, sc_core::SC_NS));

    // Write a new 64b value and read back via APB (2x32b)
    const uint32_t wrLow = 0xCAFEBABE;
    const uint32_t wrHigh = 0xDEADBEEF;

    addr.address = BASE_ADDR_UBLOCKB + REG_BLOCKB_BLOCKBTABLE1 + 0x0;
    data.data = wrLow;
    cpu_main->request(true, addr, data);

    addr.address = BASE_ADDR_UBLOCKB + REG_BLOCKB_BLOCKBTABLE1 + 0x4;
    data.data = wrHigh;
    cpu_main->request(true, addr, data);

    // Read back and verify
    addr.address = BASE_ADDR_UBLOCKB + REG_BLOCKB_BLOCKBTABLE1 + 0x0;
    cpu_main->request(false, addr, data);
    valLow = data.data;

    addr.address = BASE_ADDR_UBLOCKB + REG_BLOCKB_BLOCKBTABLE1 + 0x4;
    cpu_main->request(false, addr, data);
    valHigh = data.data;

    if (valLow == wrLow && valHigh == wrHigh) {
         log_.logPrint("CPU Write/Readback verify success", LOG_ALWAYS);
    } else {
         std::stringstream ss;
         ss << "CPU Write/Readback verify failed. Expected 0x"
            << std::hex << wrHigh << std::setw(8) << std::setfill('0') << wrLow
            << ", got 0x"
            << std::hex << valHigh << std::setw(8) << std::setfill('0') << valLow;
         log_.logPrint(ss.str(), LOG_ALWAYS);
    }

    controller.test_complete(test_write);

    // Wait for external memory interface test (blockBTableExt)
    controller.wait_test(test_ext, sc_core::sc_time(1, sc_core::SC_NS));

    // blockBTableExt is an external memory: in the model it is serviced directly by blockB.
    // Access it via the FW-visible APB window (one 32b word per row; only low 5 bits are stored).
    const uint32_t ext_idx0 = 2;
    const uint32_t ext_idx1 = 7;
    const uint32_t ext_wr0 = 0x15;
    const uint32_t ext_wr1 = 0x0A;

    // Write row 2
    addr.address = BASE_ADDR_UBLOCKB + REG_BLOCKB_BLOCKBTABLEEXT + 0x4 * ext_idx0;
    data.data = ext_wr0;
    cpu_main->request(true, addr, data);

    // Write row 7
    addr.address = BASE_ADDR_UBLOCKB + REG_BLOCKB_BLOCKBTABLEEXT + 0x4 * ext_idx1;
    data.data = ext_wr1;
    cpu_main->request(true, addr, data);

    // Read back row 2
    addr.address = BASE_ADDR_UBLOCKB + REG_BLOCKB_BLOCKBTABLEEXT + 0x4 * ext_idx0;
    cpu_main->request(false, addr, data);
    const uint32_t ext_rd0 = data.data & 0x1F;

    // Read back row 7
    addr.address = BASE_ADDR_UBLOCKB + REG_BLOCKB_BLOCKBTABLEEXT + 0x4 * ext_idx1;
    cpu_main->request(false, addr, data);
    const uint32_t ext_rd1 = data.data & 0x1F;

    if (ext_rd0 == (ext_wr0 & 0x1F) && ext_rd1 == (ext_wr1 & 0x1F)) {
         log_.logPrint("CPU ExtMem (blockBTableExt) RW verify success", LOG_ALWAYS);
    } else {
         std::stringstream ss;
         ss << "CPU ExtMem (blockBTableExt) RW verify failed. Expected row"
            << ext_idx0 << "=0x" << std::hex << (ext_wr0 & 0x1F)
            << " row" << std::dec << ext_idx1 << "=0x" << std::hex << (ext_wr1 & 0x1F)
            << ", got row" << std::dec << ext_idx0 << "=0x" << std::hex << ext_rd0
            << " row" << std::dec << ext_idx1 << "=0x" << std::hex << ext_rd1;
         log_.logPrint(ss.str(), LOG_ALWAYS);
    }

    controller.test_complete(test_ext);
}


