// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE
#ifndef AHB_PORT_THUNKER_H
#define AHB_PORT_THUNKER_H

#include "ahb_channel.h"
#include "../../common/systemc/bitTwiddling.h"
#include <memory>
#include <optional>
#include <string>

// ahb_port_thunker
//
// Joins a child ahb port to the parent's endpoint when the payload types are
// per-field _bitWidth equivalent but distinct C++ types. Up is the parent side
// and Down the child, whatever the data direction.
//
// DirectAddr and DirectData are the generator's verdicts for the addr_t and
// data_t pairs: true when the pair's two declarations emit identical member
// storage, so copyPayload() transfers the value whole. data_t crosses in both
// directions, as write data and as read data. A false verdict is always correct
// and merely slower.
//
// It owns no channel and no thread. The adapter converts every child call and
// makes it on the parent's channel, so the address and data phases keep the
// pipelining and timing of a direct bind.
//
// A parent port is unbound until elaboration completes, so it is resolved in
// end_of_elaboration(). Template argument order must match _thunker_member_type
// in pysrc/intf_gen_utils.py. block_ is unused.
template <class UpA, class UpD, class DownA, class DownD,
          bool DirectAddr = false, bool DirectData = false>
class ahb_port_thunker
{
    static_assert(!DirectAddr || sizeof(UpA) == sizeof(DownA), "direct copy requires equal payload size");
    static_assert(!DirectData || sizeof(UpD) == sizeof(DownD), "direct copy requires equal payload size");

    using UpAddr = ahbAddrSt<UpA>;
    using DownAddr = ahbAddrSt<DownA>;
    using UpResp = ahbRespSt<UpD>;
    using DownResp = ahbRespSt<DownD>;
    using UpIn = ahb_in_if<UpA, UpD>;
    using UpOut = ahb_out_if<UpA, UpD>;
    using DownIn = ahb_in_if<DownA, DownD>;
    using DownOut = ahb_out_if<DownA, DownD>;

public:
    // connectionMap shape: parent port reference.
    ahb_port_thunker( const char* name_,
                      ahb_in<UpA, UpD>&     upPort,
                      ahb_in<DownA, DownD>& downPort,
                      std::string block_ )
    {
        m_in = std::make_unique<inAdapter>( name_, upPort );
        downPort( *m_in );
    }

    // connections shape: parent-side channel bound by its interface base.
    ahb_port_thunker( const char* name_,
                      ahb_in_if<UpA, UpD>&  upInIface,
                      ahb_in<DownA, DownD>& downPort,
                      std::string block_ )
    {
        m_in = std::make_unique<inAdapter>( name_, upInIface );
        downPort( *m_in );
    }

    // producer (out) shape: the child producer port drives the parent-side
    // channel's ahb_out_if<UpA, UpD>.
    ahb_port_thunker( const char* name_,
                      ahb_out_if<UpA, UpD>&  upOutIface,
                      ahb_out<DownA, DownD>& downPort,
                      std::string block_ )
    {
        m_out = std::make_unique<outAdapter>( name_, upOutIface );
        downPort( *m_out );
    }

    // producer (out) port shape: the parent side is a parent OUT port.
    ahb_port_thunker( const char* name_,
                      ahb_out<UpA, UpD>&     upPort,
                      ahb_out<DownA, DownD>& downPort,
                      std::string block_ )
    {
        m_out = std::make_unique<outAdapter>( name_, upPort );
        downPort( *m_out );
    }

private:
    template <class To, class From>
    static void copyAddr( To& out, const From& in )
    {
        copyPayload<DirectAddr>( out.haddr, in.haddr );
        out.htrans = in.htrans;
        out.hwrite = in.hwrite;
        out.hsize = in.hsize;
        out.hburst = in.hburst;
        out.hprot = in.hprot;
        out.hmastlock = in.hmastlock;
    }

    template <class To, class From>
    static void copyResp( To& out, const From& in )
    {
        copyPayload<DirectData>( out.hrdata, in.hrdata );
        out.hresp = in.hresp;
    }

    // The portBase calls the child makes through its port, forwarded to the
    // parent's interface as a direct bind would deliver them.
    template <class UpIf>
    struct forwardPortBase : virtual public portBase
    {
        void setMultiDriver( std::string name_, std::function<std::string(const uint64_t &value)> prt = nullptr ) override { m_up->setMultiDriver( name_, prt ); }
        std::shared_ptr<trackerBase> getTracker( void ) override { return m_up->getTracker(); }
        void setTeeBusy( bool busy ) override { m_up->setTeeBusy( busy ); }
        void setTandem( void ) override { m_up->setTandem(); }
        void setLogging( verbosity_e verbosity ) override { m_up->setLogging( verbosity ); }
        void setTimed( int nsec, timedDelayMode mode ) override { m_up->setTimed( nsec, mode ); }
        void setCycleTransaction( portType type_ ) override { m_up->setCycleTransaction( type_ ); }
        void setTimedDelayPtr( std::shared_ptr<timedDelayBase> pTimedDelay ) override { m_up->setTimedDelayPtr( pTimedDelay ); }
        portBase* getPort( void ) override { return m_up->getPort(); }
        sc_core::sc_prim_channel* getChannel( void ) override { return m_up->getChannel(); }
        void setLogQueue( std::shared_ptr<stringPingPong> logQueue ) override { m_up->setLogQueue( logQueue ); }

        UpIf* m_up = nullptr;
        sc_core::sc_port<UpIf>* m_up_port = nullptr;
    };

    // Consumer child: the child receives the address and write data and sends
    // the response.
    class inAdapter final : public sc_core::sc_prim_channel, public DownIn, public forwardPortBase<UpIn>
    {
    public:
        inAdapter( const char* name_, sc_core::sc_port<UpIn>& upPort ) : sc_core::sc_prim_channel( name_ ) { this->m_up_port = &upPort; }
        inAdapter( const char* name_, UpIn& up ) : sc_core::sc_prim_channel( name_ ) { this->m_up = &up; }

        void receiveAddr( DownAddr& addr_ ) override
        {
            UpAddr up;
            this->m_up->receiveAddr( up );
            copyAddr( addr_, up );
        }
        void receiveData( DownD& data_ ) override
        {
            UpD up;
            this->m_up->receiveData( up );
            copyPayload<DirectData>( data_, up );
        }
        void sendResp( const DownResp& resp_ ) override
        {
            UpResp up;
            copyResp( up, resp_ );
            this->m_up->sendResp( up );
        }
        bool isActive() override { return this->m_up->isActive(); }
        bool isNotActive() override { return this->m_up->isNotActive(); }
        void setExternalEvent( sc_event* event ) override { this->m_up->setExternalEvent( event ); }
        const char* kind() const override { return "ahb_port_thunker"; }

    private:
        void end_of_elaboration() override
        {
            if (this->m_up_port) {
                this->m_up = this->m_up_port->operator->();
            }
        }
    };

    // Producer child: the child sends the address and write data and receives
    // the response.
    class outAdapter final : public sc_core::sc_prim_channel, public DownOut, public forwardPortBase<UpOut>
    {
    public:
        outAdapter( const char* name_, sc_core::sc_port<UpOut>& upPort ) : sc_core::sc_prim_channel( name_ ) { this->m_up_port = &upPort; }
        outAdapter( const char* name_, UpOut& up ) : sc_core::sc_prim_channel( name_ ) { this->m_up = &up; }

        void sendAddr( const DownAddr& addr_, std::optional<std::string> str ) override
        {
            UpAddr up;
            copyAddr( up, addr_ );
            this->m_up->sendAddr( up, std::move( str ) );
        }
        void sendData( const DownD& data_ ) override
        {
            UpD up;
            copyPayload<DirectData>( up, data_ );
            this->m_up->sendData( up );
        }
        void receiveResp( DownResp& resp_ ) override
        {
            UpResp up;
            this->m_up->receiveResp( up );
            copyResp( resp_, up );
        }
        const char* kind() const override { return "ahb_port_thunker"; }

    private:
        void end_of_elaboration() override
        {
            if (this->m_up_port) {
                this->m_up = this->m_up_port->operator->();
            }
        }
    };

    // One of the two, by construction shape.
    std::unique_ptr<inAdapter> m_in;
    std::unique_ptr<outAdapter> m_out;
};

#endif // AHB_PORT_THUNKER_H
