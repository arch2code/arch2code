// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=uvmReuseChain
// GENERATED_CODE_BEGIN --template=uvmRegistrar
#if defined(XCELIUM) || defined(VCS)
#include "instanceFactory.h"
#include "blockBase.h"
#include "uvmReuseChain_uvm_sc_wrapper.h"
#if defined(XCELIUM)
#include "uvmReuseChain_v4_uvm_tb_xcelium.h"
#include "uvmReuseChain_v8_uvm_tb_xcelium.h"
#else
// Written by vlogan -sc_model from the port map.
#include "uvmReuseChain_v4_uvm_tb.h"
#include "uvmReuseChain_v8_uvm_tb.h"
#endif

namespace {
struct _uvmReuseChain_uvm_registrar {
    _uvmReuseChain_uvm_registrar() {
        instanceFactory::registerBlock(
            "uvmReuseChain_uvm",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<uvmReuseChain_uvm_sc_wrapper<uvmReuseChain_v4_uvm_tb, uvmReuse_uvmReuseChainV4Config>>(blockName, variant, bbMode));
            },
            "v4", "uvmReuse");
        instanceFactory::registerBlock(
            "uvmReuseChain_uvm",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<uvmReuseChain_uvm_sc_wrapper<uvmReuseChain_v8_uvm_tb, uvmReuse_uvmReuseChainV8Config>>(blockName, variant, bbMode));
            },
            "v8", "uvmReuse");
    }
};
static _uvmReuseChain_uvm_registrar _uvmReuseChain_uvm_registrar_instance;
} // namespace
#endif // XCELIUM || VCS

// GENERATED_CODE_END
