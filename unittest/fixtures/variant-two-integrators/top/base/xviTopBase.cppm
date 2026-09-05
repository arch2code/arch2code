//

// GENERATED_CODE_PARAM --block=xviTop --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "push_ack_channel.h"

export module xviTop.base;
import xviLeaf;
using namespace xviLeaf_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export class xviTopBase : public virtual blockPortBase
{
public:
    virtual ~xviTopBase() = default;


    xviTopBase(std::string name, const char * variant)
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
    };
};
export class xviTopInverted : public virtual blockPortBase
{
public:


    xviTopInverted(std::string name)
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
    };
};
export class xviTopChannels
{
public:


    xviTopChannels(std::string name, std::string srcName)
    {};
    void bind( xviTopBase *a, xviTopInverted *b)
    {
    };
};

// GENERATED_CODE_END
