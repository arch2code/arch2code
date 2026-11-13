//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=uvmRegsDrv --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=blockModuleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "instanceFactory.h"
#include "apb_channel.h"
#include "rdy_vld_channel.h"
// GENERATED_CODE_END
// user #includes here (global module fragment - attaches to the global module)
// Plain non-modular headers, including any whose definitions live in a .cpp.
#include "testController.h"
// GENERATED_CODE_BEGIN --template=moduleExport
export module uvmRegs_uvmRegsDrv.block;
import uvmRegs_uvmRegsDrv.base;
import uvmRegs;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=classDecl
using namespace uvmRegs_ns;
export SC_MODULE(uvmRegsDrv), public blockBase, public uvmRegsDrvBase
{
private:

public:

    uvmRegsDrv(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~uvmRegsDrv() override = default;

    // GENERATED_CODE_END
    // block implementation members

private:
    void program_test(void);
    void stream_test(void);
    void status_test(void);
    void write(uint32_t address, uint32_t value);
    void expect(uint32_t address, uint32_t value, const char *what);

};

// GENERATED_CODE_BEGIN --template=constructor --section=init
SC_HAS_PROCESS(uvmRegsDrv);

// === Block factory registration (uvmRegsDrv) ===
void register_uvmRegsDrv_variants() {
    instanceFactory::registerBlock("uvmRegsDrv_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<uvmRegsDrv>(blockName, variant, bbMode)); }, "", "uvmRegs");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _uvmRegsDrv_registered = (register_uvmRegsDrv_variants(), 0);
} // namespace
// === End block factory registration ===

uvmRegsDrv::uvmRegsDrv(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("uvmRegsDrv", name(), bbMode)
        ,uvmRegsDrvBase(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
    ADD_TEST(program_test);
    ADD_TEST(stream_test);
    ADD_TEST(status_test);
};

// Each slot of uRouter is 0x1000 bytes and each of uBridgeRouter 0x100; the
// register offsets are the ones fw/<block>RegAddresses.h gives each block.
namespace {
constexpr uint32_t SCALE0 = ADDR_ID_UVM_REGS_USCALE0 * 0x1000;
constexpr uint32_t SCALE1 = ADDR_ID_UVM_REGS_USCALE1 * 0x1000;
constexpr uint32_t STAT = ADDR_ID_UVM_REGS_USTAT * 0x1000;
constexpr uint32_t DEEP = ADDR_ID_UVM_REGS_UBRIDGE * 0x1000 + ADDR_ID_UVM_REGS_BRIDGE_UDEEP * 0x100;
constexpr uint32_t INNER = ADDR_ID_UVM_REGS_UWRAP * 0x1000;
constexpr uint32_t STAT_HIST = 0x0, STAT_TAB = 0x40, STAT_MODE = 0x80, STAT_COUNT = 0x88, STAT_SCRATCH = 0x90;
constexpr uint32_t DEEP_IDENT = 0x0, DEEP_CFG = 0x8, INNER_TAG = 0x0;

uint16_t word(unsigned i) { return static_cast<uint16_t>(i * 7); }
uint16_t scaled(unsigned i) { return static_cast<uint16_t>(word(i) + UVM_REGS_TB_OFFSET0 + UVM_REGS_TB_OFFSET1); }
} // namespace

void uvmRegsDrv::write(uint32_t address, uint32_t value)
{
    uvmRegsAddrSt a;
    uvmRegsDataSt d;
    a.address = address;
    d.data = value;
    apbReg->request(true, a, d);
}

void uvmRegsDrv::expect(uint32_t address, uint32_t value, const char *what)
{
    uvmRegsAddrSt a;
    uvmRegsDataSt d;
    a.address = address;
    apbReg->request(false, a, d);
    if (d.data != value) {
        errorCode::fail(std::format("{}: {} at 0x{:x} reads 0x{:x}, expected 0x{:x}", name(), what, address, (uint64_t)d.data, value));
    }
}

void uvmRegsDrv::program_test(void)
{
    expect(SCALE0, 1, "uScale0.offset reset");
    expect(DEEP + DEEP_IDENT, UVM_REGS_IDENT, "uBridge.uDeep.ident");
    expect(DEEP + DEEP_CFG, 0x5a, "uBridge.uDeep.cfg reset");
    expect(INNER + INNER_TAG, 0x11, "uWrap.uInner.tag reset");
    write(SCALE0, UVM_REGS_TB_OFFSET0);
    write(SCALE1, UVM_REGS_TB_OFFSET1);
    write(STAT + STAT_MODE, 1);
    write(STAT + STAT_SCRATCH, 0xbeef);
    for (uint32_t r = 0; r < UVM_REGS_TAB_ROWS; ++r) {
        write(STAT + STAT_TAB + 8 * r, (r * UVM_REGS_TB_TAB_STEP) & 0xfff);
    }
    expect(SCALE0, UVM_REGS_TB_OFFSET0, "uScale0.offset");
    expect(SCALE1, UVM_REGS_TB_OFFSET1, "uScale1.offset");
    expect(STAT + STAT_SCRATCH, 0xbeef, "uStat.scratch");
    for (uint32_t r = 0; r < UVM_REGS_TAB_ROWS; ++r) {
        expect(STAT + STAT_TAB + 8 * r, (r * UVM_REGS_TB_TAB_STEP) & 0xfff, "uStat.tab row");
    }
}

void uvmRegsDrv::stream_test(void)
{
    for (unsigned i = 0; i < UVM_REGS_WORDS; ++i) {
        uvmRegsWordSt w;
        w.word = word(i);
        out->write(w);
    }
}

// Run after uSink has taken every word, so count and hist are final.
void uvmRegsDrv::status_test(void)
{
    expect(STAT + STAT_COUNT, UVM_REGS_WORDS, "uStat.count");
    for (unsigned i = UVM_REGS_WORDS - UVM_REGS_TAB_ROWS; i < UVM_REGS_WORDS; ++i) {
        expect(STAT + STAT_HIST + 4 * (scaled(i) % UVM_REGS_TAB_ROWS), scaled(i), "uStat.hist row");
    }
}
