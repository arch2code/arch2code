// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE
#ifndef APB_CHANNEL_H
#define APB_CHANNEL_H

#include "sysc/communication/sc_communication_ids.h"
#include "sysc/communication/sc_prim_channel.h"
#include "sysc/communication/sc_interface.h"
#include "sysc/kernel/sc_event.h"
#include "sysc/kernel/sc_simcontext.h"
#include "sysc/tracing/sc_trace.h"
#include <typeinfo>
#include <iostream>
#include "interfaceBase.h"
#include "trackerBase.h"
#include "portBase.h"
#include "regBusChannel.h"


// ----------------------------------------------------------------------------
//  CLASS : apb_in_if<R, D>
// ----------------------------------------------------------------------------

template <class R, class D>
class apb_in_if
: virtual public sc_interface, virtual public portBase
{
public:

    // blocking read/write
    virtual void reqReceive(bool &isWrite, R&, D& ) = 0;
    virtual void complete(const D&, bool slverr = false) = 0;
    // True when the last received request came from requestWithResponse() or
    // requestNonBlockingWithResponse(), so its requester waits for complete().
    virtual bool receivedWantsResponse() = 0;
    virtual bool isActive() = 0;
    virtual bool isNotActive() = 0;
    virtual void setExternalEvent( sc_event *event ) = 0;

protected:
    // constructor
    apb_in_if() {}

private:
    // disabled
    apb_in_if( const apb_in_if<R, D>& );
    apb_in_if<R, D>& operator = ( const apb_in_if<R, D>& );
};

// ----------------------------------------------------------------------------
//  CLASS : apb_out_if<R, D>
// ----------------------------------------------------------------------------

template <class R, class D>
class apb_out_if
: virtual public sc_interface, virtual public portBase
{
public:
    // blocking req
    virtual void request(bool isWrite, const R&, D& ) = 0;
    virtual bool requestWithResponse(bool isWrite, const R&, D& ) = 0;
    virtual void requestNonBlocking(bool isWrite, const R&, D& data ) = 0; // non-blocking req for tee use only
    virtual void waitComplete(D&) = 0; // completion only on read
    // Response-aware non-blocking pair for tee use: the write is not posted,
    // and waitCompleteWithResponse() returns PSLVERR for reads and writes.
    virtual void requestNonBlockingWithResponse(bool isWrite, const R&, D& data ) = 0;
    virtual bool waitCompleteWithResponse(D&) = 0;

protected:
    // constructor
    apb_out_if() {}

private:
    // disabled
    apb_out_if( const apb_out_if<R, D>& );
    apb_out_if<R, D>& operator = ( const apb_out_if<R, D>& );
};

// ----------------------------------------------------------------------------
//  CLASS : apb_channel<R, D>
//
//  The apb_channel<R, D> primitive channel class. regBusChannel holds the
//  transfer behaviour, shared with the other register buses.
// ----------------------------------------------------------------------------

template <class R, class D>
class apb_channel
: public regBusChannel<R, D, apb_in_if<R, D>, apb_out_if<R, D>>
{
public:
    // constructor const char * module, std::string block
    explicit apb_channel( const char* name_, std::string block_, INTERFACE_AUTO_MODE autoModeReq=INTERFACE_AUTO_OFF, INTERFACE_AUTO_MODE autoModeData=INTERFACE_AUTO_OFF)
      : regBusChannel<R, D, apb_in_if<R, D>, apb_out_if<R, D>>( name_, block_, autoModeReq, autoModeData )
        { }

    virtual const char* kind() const override
        { return "apb_channel"; }
};

template <class R, class D>
using apb_out = sc_port<apb_out_if< R, D > >;
template <class R, class D>
using apb_in = sc_port<apb_in_if< R, D > >;

#endif // APB_CHANNEL_H
