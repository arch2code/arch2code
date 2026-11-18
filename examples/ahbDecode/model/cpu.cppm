//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=cpu --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=blockModuleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "instanceFactory.h"
#include "ahb_channel.h"
// GENERATED_CODE_END
// user #includes here (global module fragment - attaches to the global module)
// Plain non-modular headers, including any whose definitions live in a .cpp.
#include "regAddresses.h"
#include "testController.h"
#include "testBenchConfigBase.h"
#include "q_assert.h"
// GENERATED_CODE_BEGIN --template=moduleExport
export module ahbDecode_cpu.block;
import ahbDecode_cpu.base;
import ahbDecode;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
import a2c.endOfTest;
// GENERATED_CODE_BEGIN --template=classDecl
using namespace ahbDecode_ns;
export SC_MODULE(cpu), public blockBase, public cpuBase
{
private:

public:

    cpu(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~cpu() override = default;

    // GENERATED_CODE_END
    // block implementation members

    void test_ahbDecode(void);
    void endOfTestThread(void);

private:
    bool m_errorResponses = false;
    uint32_t read(uint64_t address, bool expectError, const std::string &what);
    void write(uint64_t address, uint32_t data, bool expectError, const std::string &what);
};

// GENERATED_CODE_BEGIN --template=constructor --section=init
SC_HAS_PROCESS(cpu);

// === Block factory registration (cpu) ===
void register_cpu_variants() {
    instanceFactory::registerBlock("cpu_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<cpu>(blockName, variant, bbMode)); }, "", "ahbDecode");
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
    ADD_TEST(test_ahbDecode);
    SC_THREAD(endOfTestThread);
};

void cpu::endOfTestThread(void)
{
    endOfTest eot(true);
    testController::GetInstance().wait_all_tests_complete();
    eot.setEndOfTest(true);
}

// A response-aware read: checks HRESP and returns the read data
uint32_t cpu::read(uint64_t address, bool expectError, const std::string &what)
{
    ahbAddrSt addr;
    ahbDataSt data;
    addr.address = address;
    const bool error = ahbReg->requestWithResponse(false, addr, data);
    Q_ASSERT(error == (expectError && m_errorResponses),
             std::format("{}: read 0x{:x} HRESP {}, expected {}", what, address, error, expectError && m_errorResponses));
    return data.data;
}

void cpu::write(uint64_t address, uint32_t value, bool expectError, const std::string &what)
{
    ahbAddrSt addr;
    ahbDataSt data;
    addr.address = address;
    data.data = value;
    const bool error = ahbReg->requestWithResponse(true, addr, data);
    Q_ASSERT(error == (expectError && m_errorResponses),
             std::format("{}: write 0x{:x} HRESP {}, expected {}", what, address, error, expectError && m_errorResponses));
}

void cpu::test_ahbDecode(void)
{
    m_errorResponses = testBenchConfigBase::getParam("errorResponses") != 0;
    log_.logPrint(std::format("HRESP ERROR expected on unmapped accesses and refused writes: {}", m_errorResponses));

    const uint64_t cfgA = BASE_ADDR_ULEAFA + REG_LEAFA_CFGA;
    const uint64_t statA = BASE_ADDR_ULEAFA + REG_LEAFA_STATA;
    const uint64_t cmdA = BASE_ADDR_ULEAFA + REG_LEAFA_CMDA;
    const uint64_t tblA = BASE_ADDR_ULEAFA + REG_LEAFA_TBLA;
    const uint64_t cfgB = BASE_ADDR_ULEAFB + REG_LEAFB_CFGB;
    const uint64_t cfgC = BASE_ADDR_USUBSYS + BASE_ADDR_ULEAFC + REG_LEAFB_CFGB;
    // the router's fourth address space and the nested router's second hold no instance
    const uint64_t emptySlot = 0x3000;
    const uint64_t emptySubSlot = BASE_ADDR_USUBSYS + 0x100;
    // registers are 8-byte aligned, so the word after cfgA holds nothing
    const uint64_t gapA = cfgA + 4;

    Q_ASSERT(read(cfgA, false, "cfgA reset") == 0x12345678, "cfgA reads its reset value");
    write(cfgA, 0x11111111, false, "cfgA");
    Q_ASSERT(read(cfgA, false, "cfgA") == 0x11111111, "cfgA reads back");

    Q_ASSERT(read(statA, false, "statA") == 0x5a5a, "statA reads the value leafA drives");
    write(statA, 0xffff, false, "statA write is dropped without an error");
    Q_ASSERT(read(statA, false, "statA") == 0x5a5a, "statA is unchanged by a write");

    Q_ASSERT(read(cmdA, false, "cmdA reset") == 0x0c0d, "cmdA reads its reset value");
    write(cmdA, 0x0001, false, "cmdA accepted write");
    write(cmdA, 0x0bad, true, "cmdA refused write");
    Q_ASSERT(read(cmdA, false, "cmdA") == 0x0001, "cmdA keeps the value it accepted");

    write(gapA, 0x2222, true, "leafA gap");
    Q_ASSERT(read(gapA, true, "leafA gap") == 0xBADDC0DE, "a leafA gap reads 0xBADDC0DE");
    write(emptySlot, 0x3333, true, "empty router slot");
    Q_ASSERT(read(emptySlot, true, "empty router slot") == 0xBADDC0DE, "an empty router slot reads 0xBADDC0DE");
    write(emptySubSlot, 0x4444, true, "empty nested router slot");
    Q_ASSERT(read(emptySubSlot, true, "empty nested router slot") == 0xBADDC0DE,
             "an empty nested router slot reads 0xBADDC0DE");
    Q_ASSERT(read(cfgA, false, "cfgA") == 0x11111111, "unmapped writes leave cfgA unchanged");

    write(cfgB, 0xb0b0b0b0, false, "cfgB");
    write(cfgC, 0xc0c0c0c0, false, "cfgC through the nested router");
    Q_ASSERT(read(cfgB, false, "cfgB") == 0xb0b0b0b0, "cfgB reads back");
    Q_ASSERT(read(cfgC, false, "cfgC") == 0xc0c0c0c0, "cfgC reads back through the nested router");

    // Posted writes, each issued as soon as the last is accepted, then read
    // back. In RTL each table read waits on the memory.
    for (uint32_t row = 0; row < TBL_WORDS; row++) {
        ahbAddrSt addr;
        ahbDataSt data;
        addr.address = tblA + row * 4;
        data.data = 0xa5000000 | row;
        ahbReg->request(true, addr, data);
    }
    for (uint32_t row = 0; row < TBL_WORDS; row++) {
        const uint32_t got = read(tblA + row * 4, false, "tblA");
        Q_ASSERT(got == (0xa5000000 | row), std::format("tblA row {} reads 0x{:x}", row, got));
    }
    log_.logPrint("test_ahbDecode passed");
}
