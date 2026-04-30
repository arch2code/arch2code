#include "ip_topExternal.h"
#include "workerThread.h"

// GENERATED_CODE_PARAM --block=ip_top

// GENERATED_CODE_BEGIN --template=tbExternal --section=init
#include "apbDecodeBase.h"
#include "srcBase.h"
#include "ipBase.h"

ip_topExternal::ip_topExternal(sc_module_name modulename) :
    ip_topInverted("Chnl"),
    log_(name())

   ,uAPBDecode(std::dynamic_pointer_cast<apbDecodeBase>( instanceFactory::createInstance(name(), "uAPBDecode", "apbDecode", "")))
   ,uSrc(std::dynamic_pointer_cast<srcBase>( instanceFactory::createInstance(name(), "uSrc", "src", "")))
   ,uIp0(std::dynamic_pointer_cast<ipBase>( instanceFactory::createInstance(name(), "uIp0", "ip", "")))
   ,uIp1(std::dynamic_pointer_cast<ipBase>( instanceFactory::createInstance(name(), "uIp1", "ip", "")))
   ,out0("out0", "uSrc")
   ,out1("out1", "uSrc")
   ,apb_uIp0("apb_uIp0", "uAPBDecode")
   ,apb_uIp1("apb_uIp1", "uAPBDecode")
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=tbExternal --section=body
{
    // instance to instance connections via channel
    uSrc->out0(out0);
    uIp0->ipDataIf(out0);
    uSrc->out1(out1);
    uIp1->ipDataIf(out1);
    uAPBDecode->apb_uIp0(apb_uIp0);
    uIp0->apbReg(apb_uIp0);
    uAPBDecode->apb_uIp1(apb_uIp1);
    uIp1->apbReg(apb_uIp1);

    SC_THREAD(eotThread);
// GENERATED_CODE_END
}
