//

// GENERATED_CODE_PARAM --block=cppDriver --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=blockModuleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "instanceFactory.h"
#include "push_ack_channel.h"
// GENERATED_CODE_END
// user #includes here (global module fragment - attaches to the global module)
// Plain non-modular headers, including any whose definitions live in a .cpp.
// GENERATED_CODE_BEGIN --template=moduleExport
export module xpCppAxis_cppDriver.block;
import xpCppAxis_cppDriver.base;
import xpCppAxis_xpCppAxisTop;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=classDecl
using namespace xpCppAxis_xpCppAxisTop_ns;
export SC_MODULE(cppDriver), public blockBase, public cppDriverBase
{
private:

public:

    cppDriver(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~cppDriver() override = default;

    // GENERATED_CODE_END
    // block implementation members
private:
    // Sample count and the first value driven on each boundary shape field.
    static constexpr uint32_t SAMPLE_COUNT = 4;
    static constexpr uint32_t FIRST_EQ_PIXEL = 0x10;
    static constexpr uint32_t FIRST_ORDER_FIRST = 0x20;
    static constexpr uint32_t FIRST_ORDER_SECOND = 0x70;
    static constexpr uint32_t FIRST_SIGN_PIXEL = 0x30;
    static constexpr uint32_t FIRST_NEST_FLAG = 0x40;
    static constexpr uint32_t FIRST_NEST_TAIL = 0x50;
    static constexpr uint32_t FIRST_NEST_PIXEL = 0x60;
    static constexpr uint32_t NEST_WORD_BASE = 0x11110000;
    void driveShapes(void);
};

// GENERATED_CODE_BEGIN --template=constructor --section=init
SC_HAS_PROCESS(cppDriver);

// === Block factory registration (cppDriver) ===
void register_cppDriver_variants() {
    instanceFactory::registerBlock("cppDriver_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<cppDriver>(blockName, variant, bbMode)); }, "", "xpCppAxis");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _cppDriver_registered = (register_cppDriver_variants(), 0);
} // namespace
// === End block factory registration ===

cppDriver::cppDriver(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("cppDriver", name(), bbMode)
        ,cppDriverBase(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
    SC_THREAD(driveShapes);
};

// Drives one sample per boundary shape per iteration. Every value is distinct
// per field and per iteration, so a thunker that copied the wrong field or the
// wrong number of bits shows up as a mismatch at the consumer rather than as a
// value that happens to survive.
void cppDriver::driveShapes(void)
{
    for (uint32_t i = 0; i < SAMPLE_COUNT; i++) {
        bndEqSt eq{};
        eq.tag = i;
        eq.data = FIRST_EQ_PIXEL + i;
        eqOut->push(eq);

        bndOrderSt order{};
        order.first = FIRST_ORDER_FIRST + i;
        order.second = FIRST_ORDER_SECOND + i;
        orderOut->push(order);

        bndSignSt sign{};
        sign.data = FIRST_SIGN_PIXEL + i;
        signOut->push(sign);

        bndNestSt nest{};
        nest.word = NEST_WORD_BASE + i;
        nest.flag = FIRST_NEST_FLAG + i;
        nest.tail = FIRST_NEST_TAIL + i;
        nest.data = FIRST_NEST_PIXEL + i;
        nestOut->push(nest);

        log_.logPrint(std::format("{} drove sample {} on all four shapes", this->name(), i),
            LOG_IMPORTANT);
    }
}

