#ifndef IPSTDDECODE_H
#define IPSTDDECODE_H

//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

#include "systemc.h"

// GENERATED_CODE_PARAM --block=ipStdDecode
// GENERATED_CODE_BEGIN --template=classDecl
#include "logging.h"
#include "instanceFactory.h"
import ipStdDecode.base;
#include "apb_channel.h"
import ip;
using namespace ip_ns;
#include "apbBusDecode.h"

SC_MODULE(ipStdDecode), public blockBase, public ipStdDecodeBase
{
private:
    void routerDecode(void);
    abpBusDecode< ipRegAddrSt, ipRegDataSt > decoder;

public:

    ipStdDecode(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~ipStdDecode() override = default;

    // GENERATED_CODE_END
    // block implementation members

};

#endif //IPSTDDECODE_H
