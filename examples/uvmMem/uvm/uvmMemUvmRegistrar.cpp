// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=uvmMem
// GENERATED_CODE_BEGIN --template=uvmRegistrar
#if defined(XCELIUM) || defined(VCS)
#include "instanceFactory.h"
#include "blockBase.h"
#include "uvmMem_uvm_sc_wrapper.h"
#if defined(XCELIUM)
#include "uvmMem_uvm_tb_xcelium.h"
#else
// Written by vlogan -sc_model from the port map.
#include "uvmMem_uvm_tb.h"
#endif

namespace {
struct _uvmMem_uvm_registrar {
    _uvmMem_uvm_registrar() {
        instanceFactory::registerBlock(
            "uvmMem_uvm",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<uvmMem_uvm_sc_wrapper<uvmMem_uvm_tb>>(blockName, variant, bbMode));
            },
            "", "uvmMem");
    }
};
static _uvmMem_uvm_registrar _uvmMem_uvm_registrar_instance;
} // namespace
#endif // XCELIUM || VCS

// GENERATED_CODE_END
