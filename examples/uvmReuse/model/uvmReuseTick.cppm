//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=uvmReuseTick --mode=module
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
export module uvmReuse_uvmReuseTick.block;
import uvmReuse_uvmReuseTick.base;
import uvmReuse;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=classDecl
using namespace uvmReuse_ns;
export SC_MODULE(uvmReuseTick), public blockBase, public uvmReuseTickBase
{
private:

public:

    uvmReuseTick(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~uvmReuseTick() override = default;

    // GENERATED_CODE_END
    // block implementation members

private:
    void ticker(void);

};

// GENERATED_CODE_BEGIN --template=constructor --section=init
SC_HAS_PROCESS(uvmReuseTick);

// === Block factory registration (uvmReuseTick) ===
void register_uvmReuseTick_variants() {
    instanceFactory::registerBlock("uvmReuseTick_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<uvmReuseTick>(blockName, variant, bbMode)); }, "", "uvmReuse");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _uvmReuseTick_registered = (register_uvmReuseTick_variants(), 0);
} // namespace
// === End block factory registration ===

uvmReuseTick::uvmReuseTick(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("uvmReuseTick", name(), bbMode)
        ,uvmReuseTickBase(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
    SC_THREAD(ticker);
};

// One count per three clkAux periods; the wait keeps the untimed model from
// spinning at one time step against an ack that returns at once.
void uvmReuseTick::ticker(void)
{
    uvmReuseCountSt t;
    while (true) {
        out->push(t);
        t.count = static_cast<uvmReuseCountT>(t.count + 1);
        wait(9, SC_NS);
    }
}
