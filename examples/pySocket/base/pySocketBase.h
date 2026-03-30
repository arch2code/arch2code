#ifndef PYSOCKET_BASE_H
#define PYSOCKET_BASE_H

//

#include "systemc.h"

// GENERATED_CODE_PARAM --block=pySocket
// GENERATED_CODE_BEGIN --template=baseClassDecl
#include "blockBase.h"

class pySocketBase : public virtual blockPortBase
{
public:
    virtual ~pySocketBase() = default;


    pySocketBase(std::string name, const char * variant) 
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
    };
};
class pySocketInverted : public virtual blockPortBase
{
public:


    pySocketInverted(std::string name) 
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
    };
};
class pySocketChannels
{
public:


    pySocketChannels(std::string name, std::string srcName) 
    {};
    void bind( pySocketBase *a, pySocketInverted *b)
    {
    };
};

// GENERATED_CODE_END
#endif //PYSOCKET_BASE_H
