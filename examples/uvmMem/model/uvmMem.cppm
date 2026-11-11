//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=uvmMem --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=blockModuleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "instanceFactory.h"
#include "memory_channel.h"
#include "rdy_vld_channel.h"
// GENERATED_CODE_END
// user #includes here (global module fragment - attaches to the global module)
// Plain non-modular headers, including any whose definitions live in a .cpp.
// GENERATED_CODE_BEGIN --template=moduleExport
export module uvmMem.block;
import uvmMem.base;
import uvmMem;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=classDecl
using namespace uvmMem_ns;
export SC_MODULE(uvmMem), public blockBase, public uvmMemBase
{
private:

public:

    uvmMem(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~uvmMem() override = default;

    // GENERATED_CODE_END
    // block implementation members

private:
    // One command at a time, as the RTL takes the next command only after it
    // has sent the word the last one read. The read blocks until its word
    // returns, so the command's own write follows it.
    void copyThread(void);

};

// GENERATED_CODE_BEGIN --template=constructor --section=init
SC_HAS_PROCESS(uvmMem);

// === Block factory registration (uvmMem) ===
void register_uvmMem_variants() {
    instanceFactory::registerBlock("uvmMem_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<uvmMem>(blockName, variant, bbMode)); }, "", "uvmMem");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _uvmMem_registered = (register_uvmMem_variants(), 0);
} // namespace
// === End block factory registration ===

uvmMem::uvmMem(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("uvmMem", name(), bbMode)
        ,uvmMemBase(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
    SC_THREAD(copyThread);
};

void uvmMem::copyThread(void)
{
    while (true) {
        uvmMemCmdSt c;
        cmd->read(c);
        uvmMemAddrSt addr;
        uvmMemWordSt word;
        addr.address = c.rdAddr;
        rd->request(false, addr, word);
        uvmMemAddrSt wrAddr;
        uvmMemWordSt wrWord;
        wrAddr.address = c.wrAddr;
        wrWord.word = c.data;
        wr->request(true, wrAddr, wrWord);
        out->write(word);
    }
}
