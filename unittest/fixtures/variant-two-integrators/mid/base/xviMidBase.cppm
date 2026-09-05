//

// GENERATED_CODE_PARAM --block=xviMid --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "push_ack_channel.h"

export module xviMid.base;
import xviLeaf;
using namespace xviLeaf_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export class xviMidBase : public virtual blockPortBase
{
public:
    virtual ~xviMidBase() = default;


    xviMidBase(std::string name, const char * variant)
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
    };
};
export class xviMidInverted : public virtual blockPortBase
{
public:


    xviMidInverted(std::string name)
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
    };
};
export class xviMidChannels
{
public:


    xviMidChannels(std::string name, std::string srcName)
    {};
    void bind( xviMidBase *a, xviMidInverted *b)
    {
    };
};

// GENERATED_CODE_END
