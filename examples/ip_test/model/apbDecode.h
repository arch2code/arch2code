#ifndef APBDECODE_H
#define APBDECODE_H

//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

#include "systemc.h"

// GENERATED_CODE_PARAM --block=apbDecode
// GENERATED_CODE_BEGIN --template=classDecl
#include "logging.h"
#include "instanceFactory.h"
#include "apbDecodeBase.h"
import ip_top;
using namespace ip_top_ns;
#include "apbBusDecode.h"

SC_MODULE(apbDecode), public blockBase, public apbDecodeBase
{
private:
    void routerDecode(void);
    abpBusDecode< apbAddrSt, apbDataSt > decoder;

public:

    apbDecode(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~apbDecode() override = default;

    // GENERATED_CODE_END
    // block implementation members

};

#endif //APBDECODE_H
