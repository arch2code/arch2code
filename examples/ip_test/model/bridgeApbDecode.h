#ifndef BRIDGEAPBDECODE_H
#define BRIDGEAPBDECODE_H

//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

#include "systemc.h"

// GENERATED_CODE_PARAM --block=bridgeApbDecode
// GENERATED_CODE_BEGIN --template=classDecl
#include "logging.h"
#include "instanceFactory.h"
#include "bridgeApbDecodeBase.h"
import ip_top;
using namespace ip_top_ns;
#include "apbBusDecode.h"

SC_MODULE(bridgeApbDecode), public blockBase, public bridgeApbDecodeBase
{
private:
    void routerDecode(void);
    abpBusDecode< apbAddrSt, apbDataSt > decoder;

public:

    bridgeApbDecode(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~bridgeApbDecode() override = default;

    // GENERATED_CODE_END
    // block implementation members

};

#endif //BRIDGEAPBDECODE_H
