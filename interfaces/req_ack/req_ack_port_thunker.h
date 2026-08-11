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
// this class performs the runtime payload bridge via copyPayload()
// in both directions and preserves the req_ack request / acknowledge
// handshake at both ends.
//
// DirectData and DirectRdata are the generator's verdicts for the two payload
// pairs this protocol carries (data_t and rdata_t, in that order): true when
// the pair's two declarations emit identical member storage, which lets
// copyPayload() transfer the value whole instead of packing and unpacking it
// field by field. Both default to false, which is always correct and merely
// slower, so a hand-written instantiation need not supply them.
//
// Up always denotes the parent side and Down the owned child channel; this
// is a topological position, not a data-flow direction (the producer shape
// below flows Down -> Up).
//
// Four construction shapes are supported, spanning a 2x2 family: the child
// (down) end is either a consumer (req_ack_in<DownR, DownA>&) or a producer
// (req_ack_out<DownR, DownA>&), and the parent (up) end is either a
// fully-bound channel interface base (captured eagerly) or an unbound parent
// port (resolved lazily on the spawned thread's first iteration, since the
// port's interface is not available until SystemC elaboration completes):
//   * connectionMap shape (consumer child, up port) — up is a parent port
//     req_ack_in<UpR, UpA>&, resolved lazily in thunkIn().
//   * connections shape (consumer child, up channel) — up is the parent-side
//     channel bound directly by its req_ack_in_if<UpR, UpA> interface base,
//     captured immediately.
//   * producer (out) shape (producer child, up channel) — the child producer
//     port req_ack_out<DownR, DownA>& drives the owned channel; the thunker
//     consumes from it and issues the bridged request onto the parent-side
//     channel's req_ack_out_if<UpR, UpA>, captured immediately. Data flows
//     child -> parent, the reverse of the consumer shapes.
//   * producer (out) port shape (producer child, up port) — as the producer
//     shape, but the up side is an unbound parent port req_ack_out<UpR, UpA>&
//     (e.g. a testbench External's inherited <DUT>Inverted boundary port),
//     resolved lazily in thunkOut(). Used when a parameterized producer
//     instance feeds a non-parameterized boundary at an excluded-instance
//     (tb/DUT) boundary.
//
// In every shape the child-side port bind to the owned channel must occur
// during SystemC elaboration; that bind is performed in the constructor
// body (which is only reached when the thunker is held as a container
// member). The overloaded constructors are disambiguated by the child
// end's port type (req_ack_in vs req_ack_out), so the container generator
// emits identical wiring for both directions.
template <class UpR, class UpA, class DownR, class DownA,
          bool DirectData = false, bool DirectRdata = false>
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
        m_up_out_port( nullptr ),
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
        m_up_out_port( nullptr ),
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
        m_up_out_port( nullptr ),
        m_down_channel( (std::string(name_) + "_ch").c_str(), block_ )
    {
        downPort( m_down_channel );
        sc_core::sc_spawn( [this]() { this->thunkOut(); } );
    }

    // producer (out) port shape: the up side is an unbound parent OUT port
    // (req_ack_out<UpR, UpA>&), resolved lazily in thunkOut() once its
    // interface binds during elaboration. Mirrors the connectionMap shape's
    // lazy port handling for the producer direction.
    req_ack_port_thunker( const char* name_,
                          req_ack_out<UpR, UpA>&     upPort,
                          req_ack_out<DownR, DownA>& downPort,
                          std::string block_ )
      : m_up_port( nullptr ),
        m_up_in_iface( nullptr ),
        m_up_out_iface( nullptr ),
        m_up_out_port( &upPort ),
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
            upIn->reqReceive( reqIn );
            static_assert( !DirectData || sizeof(DownR) == sizeof(UpR), "req_ack data_t direct copy requires equal payload size" );
            copyPayload<DirectData>( reqOut, reqIn );
            m_down_channel.req( reqOut, ackIn );
            static_assert( !DirectRdata || sizeof(UpA) == sizeof(DownA), "req_ack rdata_t direct copy requires equal payload size" );
            copyPayload<DirectRdata>( ackOut, ackIn );
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
        // thunkIn(). Resolve the up-side interface once, from the eager
        // channel iface or (port shape) the lazily-bound parent out port.
        req_ack_out_if<UpR, UpA>* upOut =
            m_up_out_iface ? m_up_out_iface : m_up_out_port->operator->();
        while (true) {
            DownR reqIn;
            UpR   reqOut;
            UpA   ackIn;
            DownA ackOut;
            m_down_channel.reqReceive( reqIn );
            static_assert( !DirectData || sizeof(UpR) == sizeof(DownR), "req_ack data_t direct copy requires equal payload size" );
            copyPayload<DirectData>( reqOut, reqIn );
            upOut->req( reqOut, ackIn );
            static_assert( !DirectRdata || sizeof(DownA) == sizeof(UpA), "req_ack rdata_t direct copy requires equal payload size" );
            copyPayload<DirectRdata>( ackOut, ackIn );
            m_down_channel.ack( ackOut );
        }
    }

    req_ack_in<UpR, UpA>*             m_up_port;
    req_ack_in_if<UpR, UpA>* m_up_in_iface;
    req_ack_out_if<UpR, UpA>* m_up_out_iface;
    req_ack_out<UpR, UpA>* m_up_out_port;
    req_ack_channel<DownR, DownA> m_down_channel;
};

#endif // REQ_ACK_PORT_THUNKER_H
