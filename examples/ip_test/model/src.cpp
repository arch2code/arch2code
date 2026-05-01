//copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

// GENERATED_CODE_PARAM --block=src
// GENERATED_CODE_BEGIN --template=constructor --section=init
#include "src.h"
SC_HAS_PROCESS(src);

src::registerBlock src::registerBlock_; //register the block with the factory

src::src(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("src", name(), bbMode)
        ,srcBase(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
    SC_THREAD(driveOut0);
    SC_THREAD(driveOut1);
};

void src::driveOut0(void)
{
    ipDataSt d{};
    d.data = 0xA5;
    log_.logPrint(std::format("{} pushing 0x{:x} on out0", this->name(), (uint64_t)d.data), LOG_IMPORTANT);
    out0->push(d);
}

void src::driveOut1(void)
{
    ipDataSt d{};
    d.data = 0x5A;
    log_.logPrint(std::format("{} pushing 0x{:x} on out1", this->name(), (uint64_t)d.data), LOG_IMPORTANT);
    out1->push(d);
}

