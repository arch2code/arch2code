#include "ip_topExternal.h"
#include "workerThread.h"

// GENERATED_CODE_PARAM --block=ip_top

// GENERATED_CODE_BEGIN --template=tbExternal --section=init
#include "apbDecodeBase.h"
#include "srcBase.h"
#include "ipBase.h"
#include "bridgeDriverBase.h"
#include "ipBridgeBase.h"

ip_topExternal::ip_topExternal(sc_module_name modulename) :
    ip_topInverted("Chnl"),
    log_(name())

   ,uAPBDecode(std::dynamic_pointer_cast<apbDecodeBase>((force_link_apbDecode(), instanceFactory::createInstance(name(), "uAPBDecode", "apbDecode", ""))))
   ,uSrc(std::dynamic_pointer_cast<srcBase<srcVariantSrc0Config>>(instanceFactory::createInstance(name(), "uSrc", "src", "variantSrc0")))
   ,uIp0(std::dynamic_pointer_cast<ipBase<ipVariant0Config>>(instanceFactory::createInstance(name(), "uIp0", "ip", "variant0")))
   ,uIp1(std::dynamic_pointer_cast<ipBase<ipVariant1Config>>(instanceFactory::createInstance(name(), "uIp1", "ip", "variant1")))
   ,uBridgeDriver(std::dynamic_pointer_cast<bridgeDriverBase>((force_link_bridgeDriver(), instanceFactory::createInstance(name(), "uBridgeDriver", "bridgeDriver", ""))))
   ,uBridge(std::dynamic_pointer_cast<ipBridgeBase>((force_link_ipBridge(), instanceFactory::createInstance(name(), "uBridge", "ipBridge", ""))))
   ,out0("out0", "uSrc")
   ,thunker_out0_uIp0("thunker_out0_uIp0", out0, uIp0->ipDataIf, name())
   ,out1("out1", "uSrc")
   ,thunker_out1_uIp1("thunker_out1_uIp1", out1, uIp1->ipDataIf, name())
   ,out8("out8", "uBridgeDriver")
   ,out70("out70", "uBridgeDriver")
   ,apb_uIp0("apb_uIp0", "uAPBDecode")
   ,apb_uIp1("apb_uIp1", "uAPBDecode")
   ,apb_uBridge("apb_uBridge", "uAPBDecode")
   ,_ext_cm_uAPBDecode_cpu_main("_ext_cm_uAPBDecode_cpu_main", "uAPBDecode")
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=tbExternal --section=body
{
    // instance to instance connections via channel
    uSrc->out0(out0);
    uSrc->out1(out1);
    uBridgeDriver->out8(out8);
    uBridge->data8In(out8);
    uBridgeDriver->out70(out70);
    uBridge->data70In(out70);
    uAPBDecode->apb_uIp0(apb_uIp0);
    uIp0->apbReg(apb_uIp0);
    uAPBDecode->apb_uIp1(apb_uIp1);
    uIp1->apbReg(apb_uIp1);
    uAPBDecode->apb_uBridge(apb_uBridge);
    uBridge->apbReg(apb_uBridge);
    uAPBDecode->cpu_main(_ext_cm_uAPBDecode_cpu_main);

    SC_THREAD(eotThread);
// GENERATED_CODE_END
}
