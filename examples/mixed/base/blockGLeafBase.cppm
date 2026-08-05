//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=blockGLeaf --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "status_channel.h"

export module mixed_blockGLeaf.base;
import mixed;
using namespace mixed_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export class blockGLeafBase : public virtual blockPortBase
{
public:
    virtual ~blockGLeafBase() = default;
    // dst ports
    // blockG->reg(rwG) A Read Write register owned by parameterized container blockG and forwarded to a leaf
    status_in< dRegSt > rwG;


    blockGLeafBase(std::string name, const char * variant) :
        rwG("rwG")
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        rwG->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        rwG->setLogging(verbosity);
    };
};
export class blockGLeafInverted : public virtual blockPortBase
{
public:
    // dst ports
    // blockG->reg(rwG) A Read Write register owned by parameterized container blockG and forwarded to a leaf
    status_out< dRegSt > rwG;


    blockGLeafInverted(std::string name) :
        rwG(("rwG"+name).c_str())
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        rwG->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        rwG->setLogging(verbosity);
    };
};
export class blockGLeafChannels
{
public:
    // dst ports
    // A Read Write register owned by parameterized container blockG and forwarded to a leaf
    status_channel< dRegSt > rwG;


    blockGLeafChannels(std::string name, std::string srcName) :
    rwG(("rwG"+name).c_str(), srcName)
    {};
    void bind( blockGLeafBase *a, blockGLeafInverted *b)
    {
        a->rwG( rwG );
        b->rwG( rwG );
    };
};

// GENERATED_CODE_END
