// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

#include "testController.h"
#include "regAddresses.h"
#include "endOfTest.h"
#include "fwIpMain.h"

// GENERATED_CODE_PARAM --block=cpu
// GENERATED_CODE_BEGIN --template=constructor --section=init
#include "cpu.h"
SC_HAS_PROCESS(cpu);

// === Block factory registration (cpu) ===
void register_cpu_variants() {
    instanceFactory::registerBlock("cpu_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<cpu>(blockName, variant, bbMode)); }, "");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _cpu_registered = (register_cpu_variants(), 0);
} // namespace
// === End block factory registration ===

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

fw_ns::ipRegBus cpu::makeRegBus(void)
{
    // Adapt the firmware's synchronous register seam onto this cpu's apb master
    // port. The register read/write logic lives in the firmware TU
    // (fw/src/fwIpMain.cpp); the model only provides transport.
    //
    // PRO/A2CPRO DIFFERENCE: with the firmware BSP, the cpu instead runs a
    // listener thread that drains the regRdWr.h cross-thread queue onto the apb
    // bus while firmware uses global regRead32()/regWrite32() on a worker
    // thread. See fwIpMain.h.
    fw_ns::ipRegBus bus;
    bus.write32 = [this](uint64_t address, uint32_t value) {
        apbAddrSt addr;
        apbDataSt data;
        addr.address = address;
        data.data = value;
        cpu_main->request(true, addr, data);
    };
    bus.read32 = [this](uint64_t address) -> uint32_t {
        apbAddrSt addr;
        apbDataSt data;
        addr.address = address;
        cpu_main->request(false, addr, data);
        return (uint32_t)data.data;
    };
    return bus;
}

void cpu::checkUIp0(void)
{
    testController &controller = testController::GetInstance();
    std::string test_name = "test_ip_uIp0_check";
    controller.register_test_name(test_name);
    controller.wait_test(test_name);

    // Allow time for src (model or RTL) to push and ip to capture.
    wait(50, SC_NS);

    fw_ns::ipRegBus bus = makeRegBus();
    bool ok = fw_ns::fwCheckUIp0(bus);
    Q_ASSERT_CTX(ok, "checkUIp0", "uIp0 firmware register check failed");

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

    fw_ns::ipRegBus bus = makeRegBus();
    bool ok = fw_ns::fwCheckUIp1(bus);
    Q_ASSERT_CTX(ok, "checkUIp1", "uIp1 firmware register check failed");

    controller.test_complete(test_name);
}

void cpu::endOfTestThread(void)
{
    endOfTest eot(true);
    testController::GetInstance().wait_all_tests_complete();
    eot.setEndOfTest(true);
}
