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
// nested _packedSt width. Per-field equivalence is validated elsewhere;
// this class performs the runtime packed-value bridge via copy_packed_bits()
// in both directions and preserves the req_ack request / acknowledge
// handshake at both ends.
//
// Up always denotes the parent side and Down the owned child channel; this
// is a topological position, not a data-flow direction (the producer shape
// below flows Down -> Up).
//
// Three construction shapes are supported. The first two are consumer-side
// (the downstream child end is a req_ack consumer, req_ack_in<DownR, DownA>&);
// the third is producer-side (the downstream child end is a req_ack producer,
// req_ack_out<DownR, DownA>&):
//   * connectionMap shape — the up side is a parent port
//     (req_ack_in<UpR, UpA>&). The port's bound interface is not
//     available until SystemC elaboration completes, so it is resolved
//     lazily on the first iteration of thunkIn().
//   * connections shape — the up side is the parent-side channel,
//     bound directly to its req_ack_in_if<UpR, UpA> interface base.
//     The channel is fully constructed before the thunker is, so the
//     interface pointer is captured immediately.
//   * producer (out) shape — the downstream child end is a producer
//     port (req_ack_out<DownR, DownA>&) that drives the owned channel;
//     the thunker consumes from the owned channel and issues the bridged
//     request onto the parent-side channel's req_ack_out_if<UpR, UpA>.
//     Data flows child -> parent here, the reverse of the consumer
//     shapes. Used when a parameterized producer instance feeds a
//     non-parameterized container channel.
//
// In every shape the child-side port bind to the owned channel must occur
// during SystemC elaboration; that bind is performed in the constructor
// body (which is only reached when the thunker is held as a container
// member). The overloaded constructors are disambiguated by the child
// end's port type (req_ack_in vs req_ack_out), so the container generator
// emits identical wiring for both directions.
template <class UpR, class UpA, class DownR, class DownA>
class req_ack_port_thunker
{
public:
    // connectionMap shape: parent port reference.
    req_ack_port_thunker( const char* name_,
                          req_ack_in<UpR, UpA>&     upPort,
                          req_ack_in<DownR, DownA>& downPort,
                          std::string block_ )
      : m_up_port( &upPort ),
        m_up_in_iface( nullptr ),
        m_up_out_iface( nullptr ),
        m_down_channel( (std::string(name_) + "_ch").c_str(), block_ )
    {
        downPort( m_down_channel );
        sc_core::sc_spawn( [this]() { this->thunkIn(); } );
    }

    // connections shape: parent-side channel bound by its interface base.
    req_ack_port_thunker( const char* name_,
                          req_ack_in_if<UpR, UpA>& upInIface,
                          req_ack_in<DownR, DownA>&         downPort,
                          std::string block_ )
      : m_up_port( nullptr ),
        m_up_in_iface( &upInIface ),
        m_up_out_iface( nullptr ),
        m_down_channel( (std::string(name_) + "_ch").c_str(), block_ )
    {
        downPort( m_down_channel );
        sc_core::sc_spawn( [this]() { this->thunkIn(); } );
    }

    // producer (out) shape: the downstream child end is a producer port
    // that drives the owned channel; the bridged request is issued onto
    // the parent-side channel's req_ack_out_if<UpR, UpA>.
    req_ack_port_thunker( const char* name_,
                          req_ack_out_if<UpR, UpA>& upOutIface,
                          req_ack_out<DownR, DownA>&         downPort,
                          std::string block_ )
      : m_up_port( nullptr ),
        m_up_in_iface( nullptr ),
        m_up_out_iface( &upOutIface ),
        m_down_channel( (std::string(name_) + "_ch").c_str(), block_ )
    {
        downPort( m_down_channel );
        sc_core::sc_spawn( [this]() { this->thunkOut(); } );
    }

private:
    void thunkIn()
    {
        // Resolve the up-side interface once. For the port shape, sc_port
        // binding is complete by the time the spawned thread first runs.
        req_ack_in_if<UpR, UpA>* upIn =
            m_up_in_iface ? m_up_in_iface : m_up_port->operator->();
        while (true) {
            UpR   reqIn;
            DownR reqOut;
            DownA ackIn;
            UpA   ackOut;
            typename UpR::_packedSt   reqPacked;
            typename DownR::_packedSt reqOutPacked;
            typename DownA::_packedSt ackPacked;
            typename UpA::_packedSt   ackOutPacked;
            upIn->reqReceive( reqIn );
            // Generated payload structs expose pack() via an out
            // parameter (`void pack(_packedSt& _ret) const`).
            reqIn.pack( reqPacked );
            copy_packed_bits( reqOutPacked, reqPacked, DownR::_bitWidth );
            reqOut.unpack( reqOutPacked );
            m_down_channel.req( reqOut, ackIn );
            ackIn.pack( ackPacked );
            copy_packed_bits( ackOutPacked, ackPacked, UpA::_bitWidth );
            ackOut.unpack( ackOutPacked );
            upIn->ack( ackOut );
        }
    }

    void thunkOut()
    {
        // Producer (out) shape: the child producer drives DownR into the
        // owned m_down_channel; bridge each request and issue UpR onto the
        // parent-side channel, then bridge the returned UpA acknowledge back
        // to DownA and ack the child. Acking the child only after the parent
        // request completes preserves end-to-end backpressure, mirroring
        // thunkIn().
        while (true) {
            DownR reqIn;
            UpR   reqOut;
            UpA   ackIn;
            DownA ackOut;
            typename DownR::_packedSt reqPacked;
            typename UpR::_packedSt   reqOutPacked;
            typename UpA::_packedSt   ackPacked;
            typename DownA::_packedSt ackOutPacked;
            m_down_channel.reqReceive( reqIn );
            reqIn.pack( reqPacked );
            copy_packed_bits( reqOutPacked, reqPacked, UpR::_bitWidth );
            reqOut.unpack( reqOutPacked );
            m_up_out_iface->req( reqOut, ackIn );
            ackIn.pack( ackPacked );
            copy_packed_bits( ackOutPacked, ackPacked, DownA::_bitWidth );
            ackOut.unpack( ackOutPacked );
            m_down_channel.ack( ackOut );
        }
    }

    req_ack_in<UpR, UpA>*             m_up_port;
    req_ack_in_if<UpR, UpA>* m_up_in_iface;
    req_ack_out_if<UpR, UpA>* m_up_out_iface;
    req_ack_channel<DownR, DownA> m_down_channel;
};

#endif // REQ_ACK_PORT_THUNKER_H
