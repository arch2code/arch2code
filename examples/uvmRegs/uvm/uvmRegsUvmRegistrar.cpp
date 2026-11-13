// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=uvmRegs
// GENERATED_CODE_BEGIN --template=uvmRegistrar
#if defined(XCELIUM) || defined(VCS)
#include "instanceFactory.h"
#include "blockBase.h"
#include "uvmRegs_uvm_sc_wrapper.h"
#if defined(XCELIUM)
#include "uvmRegs_uvm_tb_xcelium.h"
#else
// Written by vlogan -sc_model from the port map.
#include "uvmRegs_uvm_tb.h"
#endif

namespace {
struct _uvmRegs_uvm_registrar {
    _uvmRegs_uvm_registrar() {
        instanceFactory::registerBlock(
            "uvmRegs_uvm",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<uvmRegs_uvm_sc_wrapper<uvmRegs_uvm_tb>>(blockName, variant, bbMode));
            },
            "", "uvmRegs");
    }
};
static _uvmRegs_uvm_registrar _uvmRegs_uvm_registrar_instance;
} // namespace
#endif // XCELIUM || VCS

// GENERATED_CODE_END
