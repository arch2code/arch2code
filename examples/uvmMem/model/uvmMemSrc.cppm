//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=uvmMemSrc --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=blockModuleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "instanceFactory.h"
#include "rdy_vld_channel.h"
// GENERATED_CODE_END
// user #includes here (global module fragment - attaches to the global module)
// Plain non-modular headers, including any whose definitions live in a .cpp.
// GENERATED_CODE_BEGIN --template=moduleExport
export module uvmMem_uvmMemSrc.block;
import uvmMem_uvmMemSrc.base;
import uvmMem;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=classDecl
using namespace uvmMem_ns;
export SC_MODULE(uvmMemSrc), public blockBase, public uvmMemSrcBase
{
private:

public:

    uvmMemSrc(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~uvmMemSrc() override = default;

    // GENERATED_CODE_END
    // block implementation members

private:
    void sendThread(void);
    void statusPrint(void);
    unsigned sent_ = 0;

};

// GENERATED_CODE_BEGIN --template=constructor --section=init
SC_HAS_PROCESS(uvmMemSrc);

// === Block factory registration (uvmMemSrc) ===
void register_uvmMemSrc_variants() {
    instanceFactory::registerBlock("uvmMemSrc_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<uvmMemSrc>(blockName, variant, bbMode)); }, "", "uvmMem");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _uvmMemSrc_registered = (register_uvmMemSrc_variants(), 0);
} // namespace
// === End block factory registration ===

uvmMemSrc::uvmMemSrc(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("uvmMemSrc", name(), bbMode)
        ,uvmMemSrcBase(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
    logging::GetInstance().registerStatus(name(), [this](void){ statusPrint(); });
    SC_THREAD(sendThread);
};

void uvmMemSrc::sendThread(void)
{
    for (unsigned i = 0; i < UVM_MEM_CMDS; ++i) {
        uvmMemCmdSt c;
        c.wrAddr = static_cast<uvmMemAddrT>(i % UVM_MEM_WORDS);
        c.rdAddr = static_cast<uvmMemAddrT>((i + UVM_MEM_WORDS - 1) % UVM_MEM_WORDS);
        c.data = static_cast<uvmMemDataT>(UVM_MEM_DATA_BASE + i);
        cmd->write(c);
        sent_++;
    }
}

void uvmMemSrc::statusPrint(void)
{
    log_.logPrint(std::format("{} of {} commands sent", sent_, UVM_MEM_CMDS), LOG_IMPORTANT);
}
