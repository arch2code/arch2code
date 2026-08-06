//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=src --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=blockModuleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "bitTwiddling.h"
#include "q_assert.h"
#include <algorithm>
#include "instanceFactory.h"
#include "push_ack_channel.h"
#include "ipLeafVariantConfig.h"
#include "srcVariantConfig.h"
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=moduleExport
export module ip_test_src.block;
import ip_test_src.base;
import ip_test_ipLeaf.base;
import ip_test_src;
import ip_test_ipLeaf;
// GENERATED_CODE_END
// user imports here
// GENERATED_CODE_BEGIN --template=classDecl
using namespace ip_test_src_ns;
using namespace ip_test_ipLeaf_ns;
export template<typename Config>
SC_MODULE(src), public blockBase, public srcBase<Config>
{
private:

public:
    SC_HAS_PROCESS(src);

    // inherited names usable unqualified (no Config:: / this->)
    using srcBase<Config>::OUT0_DATA_WIDTH;
    using srcBase<Config>::OUT1_DATA_WIDTH;
    using srcBase<Config>::out0;
    using srcBase<Config>::out1;
    using srcBase<Config>::out2;
    using srcBase<Config>::out3;

    //instances contained in block
    std::shared_ptr<ipLeafBase<ipLeafVariantLeaf0Config>> uLeaf;

    // inherited parameterized types usable unqualified (no <Config>)
    using typename srcBase<Config>::srcOut0DataT;
    using typename srcBase<Config>::srcOut1DataT;
    using typename srcBase<Config>::srcOut0St;
    using typename srcBase<Config>::srcOut1St;

    src(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~src() override = default;

    // GENERATED_CODE_END
    // block implementation members
private:
    void driveOut0(void);
    void driveOut1(void);
    void driveOut2(void);
    void driveOut3(void);
};

// GENERATED_CODE_BEGIN --template=constructor --section=init
template<typename Config>
src<Config>::src(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("src", name(), bbMode)
        ,srcBase<Config>(name(), variant)
        ,uLeaf(std::dynamic_pointer_cast<ipLeafBase<ipLeafVariantLeaf0Config>>(instanceFactory::createInstance(name(), "uLeaf", "ipLeaf", "variantLeaf0", "ip_test")))
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
    SC_THREAD(driveOut0);
    SC_THREAD(driveOut1);
    SC_THREAD(driveOut2);
    SC_THREAD(driveOut3);
};

// The maintained producer-with-per-port-parameters regression. The
// producer's variantSrc0 binding fixes OUT0_DATA_WIDTH=8 and OUT1_DATA_WIDTH=70;
// each per-port parameter must match the receiving consumer's
// IP_DATA_WIDTH (uIp0 -> variant0=8, uIp1 -> variant1=70) for the
// push_ack thunker on each cross-Config bind to round-trip cleanly.
// The runtime checks below assert that contract at simulation start so
// any future regression that decouples producer per-port widths from
// the bound consumer Configs surfaces here rather than as a silent
// thunker truncation.
template<typename Config>
void src<Config>::driveOut0(void)
{
    log_.logPrint(std::format("{} out0 per-port width = {} bits", this->name(), OUT0_DATA_WIDTH), LOG_IMPORTANT);
    Q_ASSERT(OUT0_DATA_WIDTH == 8, "producer OUT0_DATA_WIDTH must match uIp0 variant0 IP_DATA_WIDTH=8");
    srcOut0St d{};
    d.data = 0xA5;
    d.marker = 1;
    log_.logPrint(std::format("{} pushing 0x{:x} marker {} on out0", this->name(), (uint64_t)d.data, (uint64_t)d.marker), LOG_IMPORTANT);
    out0->push(d);
}

template<typename Config>
void src<Config>::driveOut1(void)
{
    log_.logPrint(std::format("{} out1 per-port width = {} bits", this->name(), OUT1_DATA_WIDTH), LOG_IMPORTANT);
    Q_ASSERT(OUT1_DATA_WIDTH == 70, "producer OUT1_DATA_WIDTH must match uIp1 variant1 IP_DATA_WIDTH=70");
    srcOut1St d{};
    d.data.word[0] = 0x5A;
    d.data.word[1] = 0x2A;
    d.marker = 1;
    log_.logPrint(std::format("{} pushing 0x{:x}{:016x} marker {} on out1", this->name(), d.data.word[1], d.data.word[0], (uint64_t)d.marker), LOG_IMPORTANT);
    out1->push(d);
}

// out2/out3 mirror out0/out1 but feed the ipBridge subsystem
// (uBridge.data8In / data70In) in the composed ip_top. Same per-port widths and
// the same marker/data payload style so the cross-interface push_ack thunker on
// each bridge boundary round-trips cleanly into uBridgeIp0 (variant0=8-bit) and
// uBridgeIp1 (variant1=70-bit).
template<typename Config>
void src<Config>::driveOut2(void)
{
    log_.logPrint(std::format("{} out2 per-port width = {} bits", this->name(), OUT0_DATA_WIDTH), LOG_IMPORTANT);
    Q_ASSERT(OUT0_DATA_WIDTH == 8, "producer OUT0_DATA_WIDTH must match uBridgeIp0 variant0 IP_DATA_WIDTH=8");
    srcOut0St d{};
    d.data = 0xA5;
    d.marker = 1;
    log_.logPrint(std::format("{} pushing 0x{:x} marker {} on out2", this->name(), (uint64_t)d.data, (uint64_t)d.marker), LOG_IMPORTANT);
    out2->push(d);
}

template<typename Config>
void src<Config>::driveOut3(void)
{
    log_.logPrint(std::format("{} out3 per-port width = {} bits", this->name(), OUT1_DATA_WIDTH), LOG_IMPORTANT);
    Q_ASSERT(OUT1_DATA_WIDTH == 70, "producer OUT1_DATA_WIDTH must match uBridgeIp1 variant1 IP_DATA_WIDTH=70");
    srcOut1St d{};
    d.data.word[0] = 0x5A;
    d.data.word[1] = 0x2A;
    d.marker = 1;
    log_.logPrint(std::format("{} pushing 0x{:x}{:016x} marker {} on out3", this->name(), d.data.word[1], d.data.word[0], (uint64_t)d.marker), LOG_IMPORTANT);
    out3->push(d);
}
