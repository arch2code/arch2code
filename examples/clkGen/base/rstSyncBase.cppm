//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=rstSync --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "blockBase.h"

export module clkGen_rstSync.base;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export class rstSyncBase : public virtual blockPortBase
{
public:
    virtual ~rstSyncBase() = default;


    rstSyncBase(std::string name, const char * variant) 
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
    };
};
export class rstSyncInverted : public virtual blockPortBase
{
public:


    rstSyncInverted(std::string name) 
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
    };
};
export class rstSyncChannels
{
public:


    rstSyncChannels(std::string name, std::string srcName) 
    {};
    void bind( rstSyncBase *a, rstSyncInverted *b)
    {
    };
};

// GENERATED_CODE_END
