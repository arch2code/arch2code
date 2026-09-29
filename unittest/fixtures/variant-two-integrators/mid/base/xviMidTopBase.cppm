//

// GENERATED_CODE_PARAM --block=xviMidTop --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "blockBase.h"

export module xviMid_xviMidTop.base;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export class xviMidTopBase : public virtual blockPortBase
{
public:
    virtual ~xviMidTopBase() = default;


    xviMidTopBase(std::string name, const char * variant)
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
    };
};
export class xviMidTopInverted : public virtual blockPortBase
{
public:


    xviMidTopInverted(std::string name)
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
    };
};
export class xviMidTopChannels
{
public:


    xviMidTopChannels(std::string name, std::string srcName)
    {};
    void bind( xviMidTopBase *a, xviMidTopInverted *b)
    {
    };
};

// GENERATED_CODE_END
