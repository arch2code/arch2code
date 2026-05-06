//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=src
// GENERATED_CODE_BEGIN --template=constructor --section=init
#include "src.h"
template<typename Config>
src<Config>::src(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("src", name(), bbMode)
        ,srcBase<Config>(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
    SC_THREAD(driveOut0);
    SC_THREAD(driveOut1);
};

template<typename Config>
void src<Config>::driveOut0(void)
{
    ipDataSt<Config> d{};
    d.data = 0xA5;
    log_.logPrint(std::format("{} pushing 0x{:x} on out0", this->name(), (uint64_t)d.data), LOG_IMPORTANT);
    this->out0->push(d);
}

template<typename Config>
void src<Config>::driveOut1(void)
{
    ipDataSt<Config> d{};
    d.data = 0x5A;
    log_.logPrint(std::format("{} pushing 0x{:x} on out1", this->name(), (uint64_t)d.data), LOG_IMPORTANT);
    this->out1->push(d);
}
