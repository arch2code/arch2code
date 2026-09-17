//

// GENERATED_CODE_PARAM --block=vliDrv --parent=vliWrap/../../yaml/vliCont.yaml
// GENERATED_CODE_BEGIN --template=blockRegistrar
module;
#include "instanceFactory.h"
#include "blockBase.h"

export module vlInh.vlInh_vliDrv.registrar;
import vlInh_vliDrv.block;
import vlInh.vliDrv.config;

namespace {
struct _vliDrv_registrar {
    _vliDrv_registrar() {
        instanceFactory::registerBlock(
            "vliDrv_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<vliDrv<vlInh_vliDrvDrvAltConfig>>(blockName, variant, bbMode));
            },
            "drvAlt", "vlInh");
        instanceFactory::registerBlock(
            "vliDrv_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<vliDrv<vlInh_vliDrvDrvAltConfig>>(blockName, variant, bbMode));
            },
            "drvAlt", "vlInh.vlInh_vliWrap.vlInh_vliDrv");
        instanceFactory::registerBlock(
            "vliDrv_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<vliDrv<vlInh_vliDrvDrvDefConfig>>(blockName, variant, bbMode));
            },
            "drvDef", "vlInh");
        instanceFactory::registerBlock(
            "vliDrv_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<vliDrv<vlInh_vliDrvDrvDefConfig>>(blockName, variant, bbMode));
            },
            "drvDef", "vlInh.vlInh_vliWrap.vlInh_vliDrv");
        instanceFactory::registerBlock(
            "vliDrv_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<vliDrv<vlInh_vliDrvDrvSoloConfig>>(blockName, variant, bbMode));
            },
            "drvSolo", "vlInh");
        instanceFactory::registerBlock(
            "vliDrv_model",
            [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                return static_cast<std::shared_ptr<blockBase>>(std::make_shared<vliDrv<vlInh_vliDrvDrvSoloConfig>>(blockName, variant, bbMode));
            },
            "drvSolo", "vlInh.vlInh_vliWrap.vlInh_vliDrv");
    }
};
static _vliDrv_registrar _vliDrv_registrar_instance;
} // namespace
// GENERATED_CODE_END
