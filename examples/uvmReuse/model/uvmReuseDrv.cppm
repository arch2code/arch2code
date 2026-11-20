//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=uvmReuseDrv --mode=module
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
export module uvmReuse_uvmReuseDrv.block;
import uvmReuse_uvmReuseDrv.base;
import uvmReuseLeaf;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
import uvmReuse;
// GENERATED_CODE_BEGIN --template=classDecl
using namespace uvmReuseLeaf_ns;
export SC_MODULE(uvmReuseDrv), public blockBase, public uvmReuseDrvBase
{
private:

public:

    uvmReuseDrv(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~uvmReuseDrv() override = default;

    // GENERATED_CODE_END
    // block implementation members

private:
    void program_test(void);
    void stream_test(void);
    void write(uint32_t address, uint32_t value);
    void expect(uint32_t address, uint32_t value, const char *what);

};

// GENERATED_CODE_BEGIN --template=constructor --section=init
SC_HAS_PROCESS(uvmReuseDrv);

// === Block factory registration (uvmReuseDrv) ===
void register_uvmReuseDrv_variants() {
    instanceFactory::registerBlock("uvmReuseDrv_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<uvmReuseDrv>(blockName, variant, bbMode)); }, "", "uvmReuse");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _uvmReuseDrv_registered = (register_uvmReuseDrv_variants(), 0);
} // namespace
// === End block factory registration ===

uvmReuseDrv::uvmReuseDrv(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("uvmReuseDrv", name(), bbMode)
        ,uvmReuseDrvBase(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
    ADD_TEST(program_test);
    ADD_TEST(stream_test);
};

// Each slot of uRouter is 0x1000 bytes, and offset is the leaf's register at 0.
namespace {
constexpr uint32_t LEAF_A = uvmReuse_ns::ADDR_ID_UVM_REUSE_CHAIN_ULEAFA * 0x1000;
constexpr uint32_t LEAF_B = uvmReuse_ns::ADDR_ID_UVM_REUSE_CHAIN_ULEAFB * 0x1000;
} // namespace

void uvmReuseDrv::write(uint32_t address, uint32_t value)
{
    uvmReuseAddrSt a;
    uvmReuseDataSt d;
    a.address = address;
    d.data = value;
    apbReg->request(true, a, d);
}

void uvmReuseDrv::expect(uint32_t address, uint32_t value, const char *what)
{
    uvmReuseAddrSt a;
    uvmReuseDataSt d;
    a.address = address;
    apbReg->request(false, a, d);
    if (d.data != value) {
        errorCode::fail(std::format("{}: {} at 0x{:x} reads 0x{:x}, expected 0x{:x}", name(), what, address, (uint64_t)d.data, value));
    }
}

void uvmReuseDrv::program_test(void)
{
    expect(LEAF_A, 1, "uLeafA.offset reset");
    expect(LEAF_B, 1, "uLeafB.offset reset");
    write(LEAF_A, uvmReuse_ns::UVM_REUSE_TB_OFFSET_A);
    write(LEAF_B, uvmReuse_ns::UVM_REUSE_TB_OFFSET_B);
    expect(LEAF_A, uvmReuse_ns::UVM_REUSE_TB_OFFSET_A, "uLeafA.offset");
    expect(LEAF_B, uvmReuse_ns::UVM_REUSE_TB_OFFSET_B, "uLeafB.offset");
}

// Word i of packet p is p * 0x100 + i, which uSink recomputes.
void uvmReuseDrv::stream_test(void)
{
    using namespace uvmReuse_ns;
    for (uint32_t p = 0; p < UVM_REUSE_PACKETS; ++p) {
        for (uint32_t i = 0; i < UVM_REUSE_PACKET_WORDS; ++i) {
            uvmReuseBeatSt b;
            b.word = static_cast<uvmReuseWordT>(p * 0x100 + i);
            b.last = (i == UVM_REUSE_PACKET_WORDS - 1);
            out->write(b);
        }
    }
}
