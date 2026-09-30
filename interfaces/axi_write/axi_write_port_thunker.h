// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE
#ifndef AXI_WRITE_PORT_THUNKER_H
#define AXI_WRITE_PORT_THUNKER_H

#include "axi_write_channel.h"
#include "../../common/systemc/bitTwiddling.h"
#include <memory>
#include <optional>
#include <string>
#include <type_traits>
#include <vector>

// axi_write_port_thunker
//
// Joins a child axi_write port to the parent's endpoint when the payload types
// are per-field _bitWidth equivalent but distinct C++ types. Up is the parent
// side and Down the child, whatever the data direction.
//
// DirectAddr, DirectData and DirectStrb are the generator's verdicts for the
// addr_t, data_t and strb_t pairs: true when the pair's two declarations emit
// identical member storage. Sharing the burst buffer (kDirectData) also needs
// the optional user-signal and id members to be the same C++ type on both
// sides. A false verdict is always correct and merely slower. The verdicts
// precede the optional parameters, so a hand-written instantiation that
// supplies any user-signal or id parameter must spell all three first.
//
// It owns no channel and no thread. The adapter converts every child call,
// portBase calls such as setCycleTransaction included, and makes it on the
// parent's channel, so timing and API mode are those of a direct bind.
//
// Where a verdict is false, copyPayload's packed arm masks each field to its
// declared width. A value with bits outside its range is then cleaned up here
// instead of failing fast as it would on a direct bind. This is an accepted
// limitation.
//
// getSendDataPtr()/getReceiveDataPtr() hand the child raw memory in the parent's
// burst buffer, which the thunker never sees. Unless kDirectData holds, the two
// sides lay out a beat differently, so the adapter gives the child a Down-typed
// copy of 256 beats (the AXI maximum) and converts it on buffered sendData() and
// getReceiveDataPtr(), using the received buffer's beat count independently of AW.
//
// A parent port is unbound until elaboration completes, so it is resolved in
// end_of_elaboration(). Template argument order must match _thunker_member_type
// in pysrc/intf_gen_utils.py. block_ is unused.
template <class UpA, class UpD, class UpS,
          class DownA, class DownD, class DownS,
          bool DirectAddr = false, bool DirectData = false, bool DirectStrb = false,
          class UpAWU = std::monostate, class UpWU = std::monostate, class UpBU = std::monostate, class UpID = _axiIdT, unsigned UpIDW = 4,
          class DownAWU = std::monostate, class DownWU = std::monostate, class DownBU = std::monostate, class DownID = _axiIdT, unsigned DownIDW = 4>
class axi_write_port_thunker
{
    static_assert(UpIDW == DownIDW, "a cross-interface bind must carry the same id_t width on both ends");
    static_assert(!DirectAddr || sizeof(UpA) == sizeof(DownA), "direct copy requires equal payload size");
    static_assert(!DirectData || sizeof(UpD) == sizeof(DownD), "direct copy requires equal payload size");
    static_assert(!DirectStrb || sizeof(UpS) == sizeof(DownS), "direct copy requires equal payload size");

    using UpAddr = axiWriteAddressSt<UpA, UpAWU, UpID, UpIDW>;
    using DownAddr = axiWriteAddressSt<DownA, DownAWU, DownID, DownIDW>;
    using UpData = axiWriteDataSt<UpD, UpS, UpWU, UpID, UpIDW>;
    using DownData = axiWriteDataSt<DownD, DownS, DownWU, DownID, DownIDW>;
    using UpResp = axiWriteRespSt<UpBU, UpID, UpIDW>;
    using DownResp = axiWriteRespSt<DownBU, DownID, DownIDW>;
    using UpIn = axi_write_in_if<UpA, UpD, UpS, UpAWU, UpWU, UpBU, UpID, UpIDW>;
    using UpOut = axi_write_out_if<UpA, UpD, UpS, UpAWU, UpWU, UpBU, UpID, UpIDW>;
    using DownIn = axi_write_in_if<DownA, DownD, DownS, DownAWU, DownWU, DownBU, DownID, DownIDW>;
    using DownOut = axi_write_out_if<DownA, DownD, DownS, DownAWU, DownWU, DownBU, DownID, DownIDW>;

    static constexpr bool kDirectData = DirectData && DirectStrb && std::is_same_v<UpWU, DownWU> && std::is_same_v<UpID, DownID>;
    static_assert(!kDirectData || sizeof(UpData) == sizeof(DownData), "a shared burst buffer requires equal envelope size");
    static constexpr unsigned kMaxBurst = 1u << UpAddr::lenWidth;

public:
    // connectionMap shape: parent port reference.
    axi_write_port_thunker( const char* name_,
                            axi_write_in<UpA, UpD, UpS, UpAWU, UpWU, UpBU, UpID, UpIDW>&     upPort,
                            axi_write_in<DownA, DownD, DownS, DownAWU, DownWU, DownBU, DownID, DownIDW>& downPort,
                            std::string block_ )
    {
        m_in = std::make_unique<inAdapter>( name_, upPort );
        downPort( *m_in );
    }

    // connections shape: parent-side channel bound by its interface base.
    axi_write_port_thunker( const char* name_,
                            axi_write_in_if<UpA, UpD, UpS, UpAWU, UpWU, UpBU, UpID, UpIDW>&    upInIface,
                            axi_write_in<DownA, DownD, DownS, DownAWU, DownWU, DownBU, DownID, DownIDW>& downPort,
                            std::string block_ )
    {
        m_in = std::make_unique<inAdapter>( name_, upInIface );
        downPort( *m_in );
    }

    // producer (out) shape: the child producer port drives the parent-side
    // channel's axi_write_out_if<UpA, UpD, UpS>.
    axi_write_port_thunker( const char* name_,
                            axi_write_out_if<UpA, UpD, UpS, UpAWU, UpWU, UpBU, UpID, UpIDW>&   upOutIface,
                            axi_write_out<DownA, DownD, DownS, DownAWU, DownWU, DownBU, DownID, DownIDW>& downPort,
                            std::string block_ )
    {
        m_out = std::make_unique<outAdapter>( name_, upOutIface );
        downPort( *m_out );
    }

    // producer (out) port shape: the parent side is a parent OUT port.
    axi_write_port_thunker( const char* name_,
                            axi_write_out<UpA, UpD, UpS, UpAWU, UpWU, UpBU, UpID, UpIDW>&     upPort,
                            axi_write_out<DownA, DownD, DownS, DownAWU, DownWU, DownBU, DownID, DownIDW>& downPort,
                            std::string block_ )
    {
        m_out = std::make_unique<outAdapter>( name_, upPort );
        downPort( *m_out );
    }

private:
    template <class To, class From>
    static void copyAddr( To& out, const From& in )
    {
        out.awid = static_cast<decltype(out.awid)>( in.awid );
        copyPayload<DirectAddr>( out.awaddr, in.awaddr );
        out.awlen = in.awlen;
        out.awsize = in.awsize;
        out.awburst = in.awburst;
        if constexpr (hasOptionalPayload<decltype(out.user)> && hasOptionalPayload<decltype(in.user)>) {
            copyPayload<false>( out.user, in.user );
        }
    }

    template <class To, class From>
    static void copyData( To& out, const From& in )
    {
        out.wid = static_cast<decltype(out.wid)>( in.wid );
        copyPayload<DirectData>( out.wdata, in.wdata );
        copyPayload<DirectStrb>( out.wstrb, in.wstrb );
        out.wlast = in.wlast;
        if constexpr (hasOptionalPayload<decltype(out.user)> && hasOptionalPayload<decltype(in.user)>) {
            copyPayload<false>( out.user, in.user );
        }
    }

    template <class To, class From>
    static void copyResp( To& out, const From& in )
    {
        out.bid = static_cast<decltype(out.bid)>( in.bid );
        out.bresp = in.bresp;
        if constexpr (hasOptionalPayload<decltype(out.user)> && hasOptionalPayload<decltype(in.user)>) {
            copyPayload<false>( out.user, in.user );
        }
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

    // Consumer child: the child receives AW and W and sends B.
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
        void receiveData( DownData& data_ ) override
        {
            UpData up;
            this->m_up->receiveData( up );
            copyData( data_, up );
        }
        void receiveDataCycle( DownData& data_ ) override
        {
            UpData up;
            this->m_up->receiveDataCycle( up );
            copyData( data_, up );
        }
        void sendResp( const DownResp& resp_ ) override
        {
            UpResp up;
            copyResp( up, resp_ );
            this->m_up->sendResp( up );
        }
        void sendRespCycle( const DownResp& resp_ ) override
        {
            UpResp up;
            copyResp( up, resp_ );
            this->m_up->sendRespCycle( up );
        }
        void push_burst( uint32_t burstCount ) override { this->m_up->push_burst( burstCount ); }
        uint32_t getReceiveBeatCount(void) override { return this->m_up->getReceiveBeatCount(); }
        // Only a channel with a burst buffer has a read pointer, so the burst is
        // converted here rather than on every receiveData().
        uint8_t* getReceiveDataPtr( void ) override
        {
            if constexpr (kDirectData) {
                return this->m_up->getReceiveDataPtr();
            } else {
                const unsigned beats = getReceiveBeatCount();
                Q_ASSERT( beats > 0 && beats <= kMaxBurst, "received write buffer must contain 1 to 256 beats" );
                const UpData* up = reinterpret_cast<const UpData*>( this->m_up->getReceiveDataPtr() );
                for (unsigned i = 0; i < beats; i++) {
                    copyData( m_shadow[i], up[i] );
                }
                return reinterpret_cast<uint8_t*>( m_shadow.data() );
            }
        }
        bool isActive() override { return this->m_up->isActive(); }
        bool isNotActive() override { return this->m_up->isNotActive(); }
        void setExternalEvent( sc_event* event ) override { this->m_up->setExternalEvent( event ); }
        const char* kind() const override { return "axi_write_port_thunker"; }

    private:
        void end_of_elaboration() override
        {
            if (this->m_up_port) {
                this->m_up = this->m_up_port->operator->();
            }
        }
        std::vector<DownData> m_shadow = std::vector<DownData>( kDirectData ? 0 : kMaxBurst );
    };

    // Producer child: the child sends AW and W and receives B.
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
        void sendData( const DownData& data_ ) override
        {
            if constexpr (!kDirectData) {
                const unsigned beats = getSendBufferCapacity();
                if (beats) {
                    Q_ASSERT( beats <= kMaxBurst, "write buffer exceeds maximum AXI burst" );
                    UpData* up = reinterpret_cast<UpData*>( this->m_up->getSendDataPtr() );
                    for (unsigned i = 0; i < beats; i++) {
                        copyData( up[i], m_shadow[i] );
                    }
                }
            }
            UpData up;
            copyData( up, data_ );
            this->m_up->sendData( up );
        }
        void sendData( const DownData& data_, int burstCount ) override
        {
            if constexpr (!kDirectData) {
                UpData* up = reinterpret_cast<UpData*>( this->m_up->getSendDataPtr() );
                for (int i = 0; i < burstCount; i++) {
                    copyData( up[i], m_shadow[i] );
                }
            }
            UpData up;
            copyData( up, data_ );
            this->m_up->sendData( up, burstCount );
        }
        void sendDataCycle( const DownData& data_ ) override
        {
            UpData up;
            copyData( up, data_ );
            this->m_up->sendDataCycle( up );
        }
        void receiveResp( DownResp& resp_ ) override
        {
            UpResp up;
            this->m_up->receiveResp( up );
            copyResp( resp_, up );
        }
        void receiveRespCycle( DownResp& resp_ ) override
        {
            UpResp up;
            this->m_up->receiveRespCycle( up );
            copyResp( resp_, up );
        }
        uint8_t* getSendDataPtr( void ) override
        {
            if constexpr (kDirectData) {
                return this->m_up->getSendDataPtr();
            } else {
                return reinterpret_cast<uint8_t*>( m_shadow.data() );
            }
        }
        uint32_t getSendBufferCapacity(void) override { return this->m_up->getSendBufferCapacity(); }
        const char* kind() const override { return "axi_write_port_thunker"; }

    private:
        void end_of_elaboration() override
        {
            if (this->m_up_port) {
                this->m_up = this->m_up_port->operator->();
            }
        }
        std::vector<DownData> m_shadow = std::vector<DownData>( kDirectData ? 0 : kMaxBurst );
    };

    // One of the two, by construction shape.
    std::unique_ptr<inAdapter> m_in;
    std::unique_ptr<outAdapter> m_out;
};

#endif // AXI_WRITE_PORT_THUNKER_H
