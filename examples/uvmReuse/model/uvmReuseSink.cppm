//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=uvmReuseSink --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=blockModuleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "instanceFactory.h"
#include "rdy_vld_channel.h"
// GENERATED_CODE_END
// user #includes here (global module fragment - attaches to the global module)
// Plain non-modular headers, including any whose definitions live in a .cpp.
#include "testController.h"
// GENERATED_CODE_BEGIN --template=moduleExport
export module uvmReuse_uvmReuseSink.block;
import uvmReuse_uvmReuseSink.base;
import uvmReuseLeaf;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
import uvmReuse;
import a2c.endOfTest;
// GENERATED_CODE_BEGIN --template=classDecl
using namespace uvmReuseLeaf_ns;
export SC_MODULE(uvmReuseSink), public blockBase, public uvmReuseSinkBase
{
private:

public:

    uvmReuseSink(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~uvmReuseSink() override = default;

    // GENERATED_CODE_END
    // block implementation members

private:
    void stream_test(void);
    void endOfTestVoter(void);

};

// GENERATED_CODE_BEGIN --template=constructor --section=init
SC_HAS_PROCESS(uvmReuseSink);

// === Block factory registration (uvmReuseSink) ===
void register_uvmReuseSink_variants() {
    instanceFactory::registerBlock("uvmReuseSink_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<uvmReuseSink>(blockName, variant, bbMode)); }, "", "uvmReuse");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _uvmReuseSink_registered = (register_uvmReuseSink_variants(), 0);
} // namespace
// === End block factory registration ===

uvmReuseSink::uvmReuseSink(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("uvmReuseSink", name(), bbMode)
        ,uvmReuseSinkBase(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
    ADD_TEST(stream_test);
    SC_THREAD(endOfTestVoter);
};

// uDrv programs both offsets before it streams, and sends word i of packet p
// as p * 0x100 + i.
void uvmReuseSink::stream_test(void)
{
    using namespace uvmReuse_ns;
    for (uint32_t p = 0; p < UVM_REUSE_PACKETS; ++p) {
        for (uint32_t i = 0; i < UVM_REUSE_PACKET_WORDS; ++i) {
            uvmReuseBeatSt b;
            in->read(b);
            uvmReuseBeatSt e;
            e.word = static_cast<uvmReuseWordT>(p * 0x100 + i + UVM_REUSE_TB_OFFSET_A + UVM_REUSE_TB_OFFSET_B);
            e.last = (i == UVM_REUSE_PACKET_WORDS - 1);
            if (!(b == e)) {
                errorCode::fail(std::format("{}: packet {} word {} is {}, expected {}", name(), p, i, b.prt(), e.prt()));
            }
        }
    }
}

void uvmReuseSink::endOfTestVoter(void)
{
    endOfTest eot(true);
    testController::GetInstance().wait_all_tests_complete();
    eot.setEndOfTest(true);
}
