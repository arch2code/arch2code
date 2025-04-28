#ifndef FIRSTBLOCK_BASE_H
#define FIRSTBLOCK_BASE_H

//copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

#include "systemc.h"

// GENERATED_CODE_PARAM --block=firstBlock
// GENERATED_CODE_BEGIN --template=baseClassDecl
#include "rdy_vld_channel.h"
#include "nestedTopIncludes.h"

class firstBlockBase : public virtual blockPortBase
{
public:
    virtual ~firstBlockBase() = default;
    // src ports
    // alpha->uSecond: Test interface alpha
    rdy_vld_out< test_st > primary;

    // dst ports
    // uLast->gamma: Test interface gamma
    rdy_vld_in< test_st > response;


    firstBlockBase(std::string name, const char * variant) :
        primary("primary")
        ,response("response")
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        primary->setTimed(nsec, mode);
        response->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        primary->setLogging(verbosity);
        response->setLogging(verbosity);
    };
};
class firstBlockInverted : public virtual blockPortBase
{
public:
    // src ports
    // alpha->uSecond: Test interface alpha
    rdy_vld_in< test_st > primary;

    // dst ports
    // uLast->gamma: Test interface gamma
    rdy_vld_out< test_st > response;


    firstBlockInverted(std::string name) :
        primary(("primary"+name).c_str())
        ,response(("response"+name).c_str())
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        primary->setTimed(nsec, mode);
        response->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        primary->setLogging(verbosity);
        response->setLogging(verbosity);
    };
};
class firstBlockChannels
{
public:
    // src ports
    //   alpha
    rdy_vld_channel< test_st > primary;

    // dst ports
    //   gamma
    rdy_vld_channel< test_st > response;


    firstBlockChannels(std::string name, std::string srcName) :
    primary(("primary"+name).c_str(), srcName)
    ,response(("response"+name).c_str(), srcName)
    {};
    void bind( firstBlockBase *a, firstBlockInverted *b)
    {
        a->primary( primary );
        b->primary( primary );
        a->response( response );
        b->response( response );
    };
};

// GENERATED_CODE_END

#endif //FIRSTBLOCK_BASE_H
