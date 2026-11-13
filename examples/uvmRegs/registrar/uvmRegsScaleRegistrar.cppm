//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=uvmRegsScale --parent=uvmRegs/../../yaml/uvmRegs.yaml
// GENERATED_CODE_BEGIN --template=blockRegistrar
module;
#include "instanceFactory.h"
#include "blockBase.h"

export module uvmRegs.uvmRegs_uvmRegsScale.registrar;
import uvmRegs_uvmRegsScale.block;
import uvmRegs.uvmRegsScale.config;

namespace {
struct _uvmRegsScale_registrar {
    _uvmRegsScale_registrar() {
        instanceFactory::registerBlock(
            "uvmRegsScale_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<uvmRegsScale<uvmRegs_uvmRegsScaleV0Config>>(blockName, variant, bbMode));
            },
            "v0", "uvmRegs");
        instanceFactory::registerBlock(
            "uvmRegsScale_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<uvmRegsScale<uvmRegs_uvmRegsScaleV0Config>>(blockName, variant, bbMode));
            },
            "v0", "uvmRegs.uvmRegs.uvmRegs_uvmRegsScale");
        instanceFactory::registerBlock(
            "uvmRegsScale_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<uvmRegsScale<uvmRegs_uvmRegsScaleV1Config>>(blockName, variant, bbMode));
            },
            "v1", "uvmRegs");
        instanceFactory::registerBlock(
            "uvmRegsScale_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<uvmRegsScale<uvmRegs_uvmRegsScaleV1Config>>(blockName, variant, bbMode));
            },
            "v1", "uvmRegs.uvmRegs.uvmRegs_uvmRegsScale");
    }
};
static _uvmRegsScale_registrar _uvmRegsScale_registrar_instance;
} // namespace
// GENERATED_CODE_END
