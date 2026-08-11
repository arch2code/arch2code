// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE
#ifndef APB_PORT_THUNKER_H
#define APB_PORT_THUNKER_H

#include "apb_channel.h"
#include "../../common/systemc/bitTwiddling.h"
#include "sysc/kernel/sc_dynamic_processes.h"
#include <string>

// apb_port_thunker
//
// Header-only forwarding adapter held as a member of a generated container
// class. Bridges an upstream APB consumer-side endpoint carrying (UpA,
// UpD) to a downstream APB consumer port carrying (DownA, DownD), when
// the two pairs are per-field _bitWidth equivalent but differ in nested
// _packedSt width. Per-field equivalence is validated elsewhere; this
// class performs the runtime payload bridge via copyPayload()
// in both directions and preserves the APB request / completion handshake
// at both ends.
//
// DirectAddr and DirectData are the generator's verdicts for the two payload
// pairs this protocol carries (addr_t and data_t, in that order): true when the
// pair's two declarations emit identical member storage, which lets
// copyPayload() transfer the value whole instead of packing and unpacking it
// field by field. DirectData gates four call sites, not two, because the read
// response leg carries data_t back. Both default to false, which is always
// correct and merely slower, so a hand-written instantiation need not supply
// them.
//
// Up always denotes the parent side and Down the owned child channel; this
// is a topological position, not a data-flow direction (the producer shape
// below flows Down -> Up).
//
// APB handshake notes (see apb_channel.h):
//   * The completer side accepts a transaction via
//     reqReceive(isWrite, addrIn, dataIn). For write transactions the
//     channel already acknowledges by clearing the pending request, so
//     no complete() call is issued by the thunker for writes. For read
//     transactions the thunker pack-converts the response data and
//     calls complete() with the converted data.
//   * The requester side issues a single round trip per transaction via
//     request(isWrite, addrOut, dataInOut). The function blocks until the
//     response is in dataInOut for reads, and returns after acknowledging
//     the write for writes.
//
// Four construction shapes are supported, spanning a 2x2 family: the child
// (down) end is either a consumer (apb_in<DownA, DownD>&) or a producer
// (apb_out<DownA, DownD>&), and the parent (up) end is either a fully-bound
// channel interface base (captured eagerly) or an unbound parent port
// (resolved lazily on the spawned thread's first iteration, since the port's
// interface is not available until SystemC elaboration completes):
//   * connectionMap shape (consumer child, up port) — up is a parent port
//     apb_in<UpA, UpD>&, resolved lazily in thunkIn().
//   * connections shape (consumer child, up channel) — up is the parent-side
//     channel bound directly by its apb_in_if<UpA, UpD> interface base,
//     captured immediately.
//   * producer (out) shape (producer child, up channel) — the child producer
//     port apb_out<DownA, DownD>& drives the owned channel; the thunker
//     receives from it and issues the bridged request onto the parent-side
//     channel's apb_out_if<UpA, UpD>, captured immediately. Data flows
//     child -> parent, the reverse of the consumer shapes.
//   * producer (out) port shape (producer child, up port) — as the producer
//     shape, but the up side is an unbound parent port apb_out<UpA, UpD>&
//     (e.g. a testbench External's inherited <DUT>Inverted boundary port),
//     resolved lazily in thunkOut(). Used when a parameterized producer
//     instance feeds a non-parameterized boundary at an excluded-instance
//     (tb/DUT) boundary.
//
// In every shape the child-side port bind to the owned channel must occur
// during SystemC elaboration; that bind is performed in the constructor
// body (which is only reached when the thunker is held as a container
// member). The overloaded constructors are disambiguated by the child
// end's port type (apb_in vs apb_out), so the container generator emits
// identical wiring for both directions.
template <class UpA, class UpD, class DownA, class DownD,
          bool DirectAddr = false, bool DirectData = false>
class apb_port_thunker
{
public:
    // connectionMap shape: parent port reference.
    apb_port_thunker( const char* name_,
                      apb_in<UpA, UpD>&     upPort,
                      apb_in<DownA, DownD>& downPort,
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
    apb_port_thunker( const char* name_,
                      apb_in_if<UpA, UpD>& upInIface,
                      apb_in<DownA, DownD>&         downPort,
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
    // the parent-side channel's apb_out_if<UpA, UpD>.
    apb_port_thunker( const char* name_,
                      apb_out_if<UpA, UpD>& upOutIface,
                      apb_out<DownA, DownD>&         downPort,
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
    // (apb_out<UpA, UpD>&), resolved lazily in thunkOut() once its interface
    // binds during elaboration. Mirrors the connectionMap shape's lazy port
    // handling for the producer direction.
    apb_port_thunker( const char* name_,
                      apb_out<UpA, UpD>&     upPort,
                      apb_out<DownA, DownD>& downPort,
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
        apb_in_if<UpA, UpD>* upIn =
            m_up_in_iface ? m_up_in_iface : m_up_port->operator->();
        while (true) {
            bool   isWrite = false;
            UpA    addrIn;
            UpD    dataIn;
            DownA  addrOut;
            DownD  dataOut;
            upIn->reqReceive( isWrite, addrIn, dataIn );
            static_assert( !DirectAddr || sizeof(DownA) == sizeof(UpA), "apb addr_t direct copy requires equal payload size" );
            copyPayload<DirectAddr>( addrOut, addrIn );
            // For reads dataIn is unused; for writes it carries the
            // upstream write payload. Convert it unconditionally — the
            // downstream request() ignores the data on reads, and on
            // writes the converted value is what must reach the
            // downstream completer.
            static_assert( !DirectData || sizeof(DownD) == sizeof(UpD), "apb data_t direct copy requires equal payload size" );
            copyPayload<DirectData>( dataOut, dataIn );
            // request() blocks until the read response arrives, or until
            // the write ack is observed for writes.
            m_down_channel.request( isWrite, addrOut, dataOut );
            if (!isWrite) {
                // Convert the downstream read response back to up-side
                // typing and complete the transaction. Writes are
                // already acknowledged by apb_channel::reqReceive() —
                // calling complete() on a write would trip its assertion.
                UpD dataUp;
                static_assert( !DirectData || sizeof(UpD) == sizeof(DownD), "apb data_t direct copy requires equal payload size" );
                copyPayload<DirectData>( dataUp, dataOut );
                upIn->complete( dataUp );
            }
        }
    }

    void thunkOut()
    {
        // Producer (out) shape: the child producer drives DownA/DownD
        // into the owned m_down_channel; bridge each transaction and
        // issue the request onto the parent-side channel. This is
        // thunkIn() with the consumer and producer objects swapped and
        // every Up<->Down type swapped, preserving the same APB handshake
        // asymmetry (complete() only on reads). Resolve the up-side
        // interface once, from the eager channel iface or (port shape) the
        // lazily-bound parent out port.
        apb_out_if<UpA, UpD>* upOut =
            m_up_out_iface ? m_up_out_iface : m_up_out_port->operator->();
        while (true) {
            bool   isWrite = false;
            DownA  addrIn;
            DownD  dataIn;
            UpA    addrOut;
            UpD    dataOut;
            m_down_channel.reqReceive( isWrite, addrIn, dataIn );
            static_assert( !DirectAddr || sizeof(UpA) == sizeof(DownA), "apb addr_t direct copy requires equal payload size" );
            copyPayload<DirectAddr>( addrOut, addrIn );
            // For reads dataIn is unused; for writes it carries the
            // child-side write payload. Convert it unconditionally — the
            // up-side request() ignores the data on reads, and on writes
            // the converted value is what must reach the up-side completer.
            static_assert( !DirectData || sizeof(UpD) == sizeof(DownD), "apb data_t direct copy requires equal payload size" );
            copyPayload<DirectData>( dataOut, dataIn );
            // request() blocks until the read response arrives, or until
            // the write ack is observed for writes.
            upOut->request( isWrite, addrOut, dataOut );
            if (!isWrite) {
                // Convert the up-side read response back to down-side
                // typing and complete the transaction. Writes are
                // already acknowledged by apb_channel::reqReceive() —
                // calling complete() on a write would trip its assertion.
                DownD respDown;
                static_assert( !DirectData || sizeof(DownD) == sizeof(UpD), "apb data_t direct copy requires equal payload size" );
                copyPayload<DirectData>( respDown, dataOut );
                m_down_channel.complete( respDown );
            }
        }
    }

    apb_in<UpA, UpD>*              m_up_port;
    apb_in_if<UpA, UpD>*  m_up_in_iface;
    apb_out_if<UpA, UpD>* m_up_out_iface;
    apb_out<UpA, UpD>*    m_up_out_port;
    apb_channel<DownA, DownD> m_down_channel;
};

#endif // APB_PORT_THUNKER_H
