// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE
#ifndef AHB_CHANNEL_H
#define AHB_CHANNEL_H

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
//  CLASS : ahb_in_if<R, D>
// ----------------------------------------------------------------------------

template <class R, class D>
class ahb_in_if
: virtual public sc_interface, virtual public portBase
{
public:

    // blocking read/write
    virtual void reqReceive(bool &isWrite, R&, D& ) = 0;
    virtual void complete(const D&, bool error = false) = 0;
    // True when the last received request came from requestWithResponse() or
    // requestNonBlockingWithResponse(), so its requester waits for complete().
    virtual bool receivedWantsResponse() = 0;
    virtual bool isActive() = 0;
    virtual bool isNotActive() = 0;
    virtual void setExternalEvent( sc_event *event ) = 0;

protected:
    // constructor
    ahb_in_if() {}

private:
    // disabled
    ahb_in_if( const ahb_in_if<R, D>& );
    ahb_in_if<R, D>& operator = ( const ahb_in_if<R, D>& );
};

// ----------------------------------------------------------------------------
//  CLASS : ahb_out_if<R, D>
// ----------------------------------------------------------------------------

template <class R, class D>
class ahb_out_if
: virtual public sc_interface, virtual public portBase
{
public:
    // blocking req
    virtual void request(bool isWrite, const R&, D& ) = 0;
    virtual bool requestWithResponse(bool isWrite, const R&, D& ) = 0;
    virtual void requestNonBlocking(bool isWrite, const R&, D& data ) = 0; // non-blocking req for tee use only
    virtual void waitComplete(D&) = 0; // completion only on read
    // Response-aware non-blocking pair for tee use: the write is not posted,
    // and waitCompleteWithResponse() returns HRESP ERROR for reads and writes.
    virtual void requestNonBlockingWithResponse(bool isWrite, const R&, D& data ) = 0;
    virtual bool waitCompleteWithResponse(D&) = 0;

protected:
    // constructor
    ahb_out_if() {}

private:
    // disabled
    ahb_out_if( const ahb_out_if<R, D>& );
    ahb_out_if<R, D>& operator = ( const ahb_out_if<R, D>& );
};

// ----------------------------------------------------------------------------
//  CLASS : ahb_channel<R, D>
//
//  The ahb_channel<R, D> primitive channel class. It carries the same
//  transfers as apb_channel, through the regBusChannel they share, with HRESP
//  ERROR as the error bit. HSIZE and HTRANS exist only at pin level.
// ----------------------------------------------------------------------------

template <class R, class D>
class ahb_channel
: public regBusChannel<R, D, ahb_in_if<R, D>, ahb_out_if<R, D>>
{
public:
    // constructor const char * module, std::string block
    explicit ahb_channel( const char* name_, std::string block_, INTERFACE_AUTO_MODE autoModeReq=INTERFACE_AUTO_OFF, INTERFACE_AUTO_MODE autoModeData=INTERFACE_AUTO_OFF)
      : regBusChannel<R, D, ahb_in_if<R, D>, ahb_out_if<R, D>>( name_, block_, autoModeReq, autoModeData )
        { }

    virtual const char* kind() const override
        { return "ahb_channel"; }
};

template <class R, class D>
using ahb_out = sc_port<ahb_out_if< R, D > >;
template <class R, class D>
using ahb_in = sc_port<ahb_in_if< R, D > >;

#endif // AHB_CHANNEL_H
