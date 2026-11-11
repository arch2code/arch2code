//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=uvmMemStore --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=blockModuleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "instanceFactory.h"
#include "memory_channel.h"
// GENERATED_CODE_END
// user #includes here (global module fragment - attaches to the global module)
// Plain non-modular headers, including any whose definitions live in a .cpp.
#include "q_assert.h"
// GENERATED_CODE_BEGIN --template=moduleExport
export module uvmMem_uvmMemStore.block;
import uvmMem_uvmMemStore.base;
import uvmMem;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=classDecl
using namespace uvmMem_ns;
export SC_MODULE(uvmMemStore), public blockBase, public uvmMemStoreBase
{
private:

public:

    uvmMemStore(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~uvmMemStore() override = default;

    // GENERATED_CODE_END
    // block implementation members

private:
    void serveWr(void);
    void serveRd(void);
    void statusPrint(void);
    uvmMemWordSt mem_[UVM_MEM_WORDS];
    unsigned writes_ = 0;
    unsigned reads_ = 0;

};

// GENERATED_CODE_BEGIN --template=constructor --section=init
SC_HAS_PROCESS(uvmMemStore);

// === Block factory registration (uvmMemStore) ===
void register_uvmMemStore_variants() {
    instanceFactory::registerBlock("uvmMemStore_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<uvmMemStore>(blockName, variant, bbMode)); }, "", "uvmMem");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _uvmMemStore_registered = (register_uvmMemStore_variants(), 0);
} // namespace
// === End block factory registration ===

uvmMemStore::uvmMemStore(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("uvmMemStore", name(), bbMode)
        ,uvmMemStoreBase(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
    logging::GetInstance().registerStatus(name(), [this](void){ statusPrint(); });
    SC_THREAD(serveWr);
    SC_THREAD(serveRd);
};

void uvmMemStore::serveWr(void)
{
    while (true) {
        bool isWrite;
        uvmMemAddrSt addr;
        uvmMemWordSt word;
        wr->reqReceive(isWrite, addr, word);
        Q_ASSERT(isWrite, "uvmMemStore: the DUT read through its wr port");
        mem_[addr.address] = word;
        writes_++;
    }
}

void uvmMemStore::serveRd(void)
{
    while (true) {
        bool isWrite;
        uvmMemAddrSt addr;
        uvmMemWordSt word;
        rd->reqReceive(isWrite, addr, word);
        Q_ASSERT(!isWrite, "uvmMemStore: the DUT wrote through its rd port");
        rd->complete(mem_[addr.address]);
        reads_++;
    }
}

void uvmMemStore::statusPrint(void)
{
    log_.logPrint(std::format("{} writes and {} reads served", writes_, reads_), LOG_IMPORTANT);
}
