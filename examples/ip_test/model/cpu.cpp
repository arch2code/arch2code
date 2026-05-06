// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

#include "testController.h"
#include "regAddresses.h"
#include "endOfTest.h"

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
    SC_THREAD(checkUIp0);
    SC_THREAD(checkUIp1);
    SC_THREAD(endOfTestThread);
}

void cpu::checkUIp0(void)
{
    testController &controller = testController::GetInstance();
    std::string test_name = "test_ip_uIp0_check";
    controller.register_test_name(test_name);
    controller.wait_test(test_name);

    // Allow time for src (model or RTL) to push and ip to capture.
    wait(50, SC_NS);

    apbAddrSt addr;
    apbDataSt data;
    addr.address = BASE_ADDR_UIP0 + REG_IP_IPLASTDATA;
    cpu_main->request(false, addr, data);
    log_.logPrint(std::format("{} read uIp0 ipLastData = 0x{:x}", this->name(), (uint64_t)data.data), LOG_IMPORTANT);
    Q_ASSERT_CTX((data.data & 0xFF) == 0xA5, "checkUIp0", "ipLastData mismatch on uIp0");

    controller.test_complete(test_name);
}

void cpu::checkUIp1(void)
{
    testController &controller = testController::GetInstance();
    std::string test_name = "test_ip_uIp1_check";
    controller.register_test_name(test_name);
    controller.wait_test(test_name);

    // Allow time for src (model or RTL) to push and ip to capture.
    wait(50, SC_NS);

    apbAddrSt addr;
    apbDataSt data;
    addr.address = BASE_ADDR_UIP1 + REG_IP_IPLASTDATA;
    cpu_main->request(false, addr, data);
    log_.logPrint(std::format("{} read uIp1 ipLastData = 0x{:x}", this->name(), (uint64_t)data.data), LOG_IMPORTANT);
    controller.test_complete(test_name);
}

void cpu::endOfTestThread(void)
{
    endOfTest eot(true);
    testController::GetInstance().wait_all_tests_complete();
    eot.setEndOfTest(true);
}
