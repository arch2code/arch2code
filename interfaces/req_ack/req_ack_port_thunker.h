// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE
#ifndef REQ_ACK_PORT_THUNKER_H
#define REQ_ACK_PORT_THUNKER_H

#include "../../common/systemc/bitTwiddling.h"
#include "req_ack_channel.h"
#include "sysc/kernel/sc_dynamic_processes.h"
#include <string>

// req_ack_port_thunker
//
// Header-only forwarding adapter held as a member of a generated container
// class. Bridges an upstream req_ack consumer-side endpoint carrying
// (UpR, UpA) to a downstream req_ack consumer port carrying (DownR, DownA),
// when the two pairs are per-field _bitWidth equivalent but differ in
// nested _packedSt width. The per-field equivalence is validated
// separately in Step 6.2; this class performs the runtime packed-value
// bridge via copy_packed_bits() in both directions.
//
// Two construction shapes are supported:
//   * connectionMap shape — the up side is a parent port
//     (req_ack_in<UpR, UpA>&). The port's bound interface is not
//     available until SystemC elaboration completes, so it is resolved
//     lazily on the first iteration of thunk().
//   * connections shape — the up side is the parent-side channel,
//     bound directly to its req_ack_in_if<UpR, UpA> interface base.
//     The channel is fully constructed before the thunker is, so the
//     interface pointer is captured immediately.
//
// In both shapes the IP-side port bind to the owned channel must occur
// during SystemC elaboration; that bind is performed in the constructor
// body (which is only reached when the thunker is held as a container
// member).
template <class UpR, class UpA, class DownR, class DownA>
class req_ack_port_thunker
{
public:
    // connectionMap shape: parent port reference.
    req_ack_port_thunker( const char* name_,
                          req_ack_in<UpR, UpA>&     upPort,
                          req_ack_in<DownR, DownA>& downPort,
                          std::string blockName )
      : m_up_port( &upPort ),
        m_up_iface( nullptr ),
        m_chDown( (std::string(name_) + "_ch").c_str(), blockName )
    {
        downPort( m_chDown );
        sc_core::sc_spawn( [this]() { this->thunk(); } );
    }

    // connections shape: parent-side channel bound by its interface base.
    req_ack_port_thunker( const char* name_,
                          sc_core::req_ack_in_if<UpR, UpA>& upIface,
                          req_ack_in<DownR, DownA>&         downPort,
                          std::string blockName )
      : m_up_port( nullptr ),
        m_up_iface( &upIface ),
        m_chDown( (std::string(name_) + "_ch").c_str(), blockName )
    {
        downPort( m_chDown );
        sc_core::sc_spawn( [this]() { this->thunk(); } );
    }

private:
    void thunk()
    {
        // Resolve the up-side interface once. For the port shape, sc_port
        // binding is complete by the time the spawned thread first runs.
        sc_core::req_ack_in_if<UpR, UpA>* up =
            m_up_iface ? m_up_iface : m_up_port->operator->();
        while (true) {
            UpR   reqIn;
            DownR reqOut;
            DownA ackIn;
            UpA   ackOut;
            typename UpR::_packedSt   reqPacked;
            typename DownR::_packedSt reqOutPacked;
            typename DownA::_packedSt ackPacked;
            typename UpA::_packedSt   ackOutPacked;
            up->reqReceive( reqIn );
            // Generated payload structs expose pack() via an out
            // parameter (`void pack(_packedSt& _ret) const`).
            reqIn.pack( reqPacked );
            copy_packed_bits( reqOutPacked, reqPacked, DownR::_bitWidth );
            reqOut.unpack( reqOutPacked );
            m_chDown.req( reqOut, ackIn );
            ackIn.pack( ackPacked );
            copy_packed_bits( ackOutPacked, ackPacked, UpA::_bitWidth );
            ackOut.unpack( ackOutPacked );
            up->ack( ackOut );
        }
    }

    req_ack_in<UpR, UpA>*             m_up_port;
    sc_core::req_ack_in_if<UpR, UpA>* m_up_iface;
    sc_core::req_ack_channel<DownR, DownA> m_chDown;
};

#endif // REQ_ACK_PORT_THUNKER_H
