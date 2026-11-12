// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=uvmVideo
// GENERATED_CODE_BEGIN --template=uvmRegistrar
#if defined(XCELIUM) || defined(VCS)
#include "instanceFactory.h"
#include "blockBase.h"
#include "uvmVideo_uvm_sc_wrapper.h"
#if defined(XCELIUM)
#include "uvmVideo_uvm_tb_xcelium.h"
#else
// Written by vlogan -sc_model from the port map.
#include "uvmVideo_uvm_tb.h"
#endif

namespace {
struct _uvmVideo_uvm_registrar {
    _uvmVideo_uvm_registrar() {
        instanceFactory::registerBlock(
            "uvmVideo_uvm",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<uvmVideo_uvm_sc_wrapper<uvmVideo_uvm_tb>>(blockName, variant, bbMode));
            },
            "", "uvmVideo");
    }
};
static _uvmVideo_uvm_registrar _uvmVideo_uvm_registrar_instance;
} // namespace
#endif // XCELIUM || VCS

// GENERATED_CODE_END
