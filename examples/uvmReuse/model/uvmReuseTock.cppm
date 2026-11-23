//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=uvmReuseTock --mode=module
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
export module uvmReuse_uvmReuseTock.block;
import uvmReuse_uvmReuseTock.base;
import uvmReuse;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=classDecl
using namespace uvmReuse_ns;
export SC_MODULE(uvmReuseTock), public blockBase, public uvmReuseTockBase
{
private:

public:

    uvmReuseTock(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~uvmReuseTock() override = default;

    // GENERATED_CODE_END
    // block implementation members

private:
    void tocker(void);

};

// GENERATED_CODE_BEGIN --template=constructor --section=init
SC_HAS_PROCESS(uvmReuseTock);

// === Block factory registration (uvmReuseTock) ===
void register_uvmReuseTock_variants() {
    instanceFactory::registerBlock("uvmReuseTock_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<uvmReuseTock>(blockName, variant, bbMode)); }, "", "uvmReuse");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _uvmReuseTock_registered = (register_uvmReuseTock_variants(), 0);
} // namespace
// === End block factory registration ===

uvmReuseTock::uvmReuseTock(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("uvmReuseTock", name(), bbMode)
        ,uvmReuseTockBase(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
    SC_THREAD(tocker);
};

void uvmReuseTock::tocker(void)
{
    uvmReuseCountSt t;
    while (true) {
        in->pushReceive(t);
        in->ack();
    }
}
