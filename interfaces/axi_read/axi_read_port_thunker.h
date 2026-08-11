// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE
#ifndef AXI_READ_PORT_THUNKER_H
#define AXI_READ_PORT_THUNKER_H

#include "axi_read_channel.h"
#include "../../common/systemc/bitTwiddling.h"
#include "sysc/kernel/sc_dynamic_processes.h"
#include <optional>
#include <string>

// axi_read_port_thunker
//
// Header-only forwarding adapter held as a member of a generated container
// class. Bridges an upstream axi_read consumer-side endpoint carrying
// (axiReadAddressSt<UpA>, axiReadRespSt<UpD>) to a downstream axi_read
// consumer port carrying (axiReadAddressSt<DownA>, axiReadRespSt<DownD>),
// when the two pairs are per-field _bitWidth equivalent but differ in
// nested _packedSt width. Per-field equivalence is validated elsewhere;
// this class performs the runtime payload bridge via copyPayload()
// in both directions and preserves the AXI read handshake at both ends.
//
// DirectAddr and DirectData are the generator's verdicts for the two payload
// pairs this protocol carries (addr_t and data_t, in that order): true when the
// pair's two declarations emit identical member storage. The copies here are on
// the envelopes rather than the payloads themselves, which is sound because the
// only parameter-dependent member of axiReadAddressSt<A> is its A araddr and the
// only parameter-dependent member of axiReadRespSt<D> is its D rdata; every
// other member is the same fixed type on both sides, so corresponding payload
// storage makes the whole envelope correspond. Both default to false, which is
// always correct and merely slower, so a hand-written instantiation need not
// supply them.
//
// Up always denotes the parent side and Down the owned child channel; this
// is a topological position, not a data-flow direction (the producer shape
// below flows Down -> Up).
//
// Single-beat semantics only: the forwarding loop pulls one address and
// returns one response per iteration. Multi-beat burst transfers are out
// of scope for the thunker; the packed-form check is the canonical guard
// against width disagreement for the wrapped envelope.
//
// Four construction shapes are supported, spanning a 2x2 family: the child
// (down) end is either a consumer (axi_read_in<DownA, DownD>&) or a producer
// (axi_read_out<DownA, DownD>&), and the parent (up) end is either a
// fully-bound channel interface base (captured eagerly) or an unbound parent
// port (resolved lazily on the spawned thread's first iteration, since the
// port's interface is not available until SystemC elaboration completes):
//   * connectionMap shape (consumer child, up port) — up is a parent port
//     axi_read_in<UpA, UpD>&, resolved lazily in thunkIn().
//   * connections shape (consumer child, up channel) — up is the parent-side
//     channel bound directly by its axi_read_in_if<UpA, UpD> interface base,
//     captured immediately.
//   * producer (out) shape (producer child, up channel) — the child producer
//     port axi_read_out<DownA, DownD>& drives the owned channel; the thunker
//     consumes from it and drives the bridged payload onto the parent-side
//     channel's axi_read_out_if<UpA, UpD>, captured immediately. Data flows
//     child -> parent, the reverse of the consumer shapes.
//   * producer (out) port shape (producer child, up port) — as the producer
//     shape, but the up side is an unbound parent port axi_read_out<UpA, UpD>&
//     (e.g. a testbench External's inherited <DUT>Inverted boundary port),
//     resolved lazily in thunkOut(). Used when a parameterized producer
//     instance feeds a non-parameterized boundary at an excluded-instance
//     (tb/DUT) boundary.
//
// In every shape the child-side port bind to the owned channel must occur
// during SystemC elaboration; that bind is performed in the constructor
// body (which is only reached when the thunker is held as a container
// member).
template <class UpA, class UpD, class DownA, class DownD,
          bool DirectAddr = false, bool DirectData = false>
class axi_read_port_thunker
{
public:
    // connectionMap shape: parent port reference.
    axi_read_port_thunker( const char* name_,
                           axi_read_in<UpA, UpD>&     upPort,
                           axi_read_in<DownA, DownD>& downPort,
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
    axi_read_port_thunker( const char* name_,
                           axi_read_in_if<UpA, UpD>&  upInIface,
                           axi_read_in<DownA, DownD>& downPort,
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
    // that drives the owned channel; the bridged payload is driven onto
    // the parent-side channel's axi_read_out_if<UpA, UpD>.
    axi_read_port_thunker( const char* name_,
                           axi_read_out_if<UpA, UpD>&  upOutIface,
                           axi_read_out<DownA, DownD>& downPort,
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
    // (axi_read_out<UpA, UpD>&), resolved lazily in thunkOut() once its
    // interface binds during elaboration. Mirrors the connectionMap shape's
    // lazy port handling for the producer direction.
    axi_read_port_thunker( const char* name_,
                           axi_read_out<UpA, UpD>&     upPort,
                           axi_read_out<DownA, DownD>& downPort,
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
        axi_read_in_if<UpA, UpD>* upIn =
            m_up_in_iface ? m_up_in_iface : m_up_port->operator->();
        while (true) {
            // Address phase: upstream receives, downstream sends.
            axiReadAddressSt<UpA>   addrIn;
            axiReadAddressSt<DownA> addrOut;
            upIn->receiveAddr( addrIn );
            static_assert( !DirectAddr || sizeof(axiReadAddressSt<DownA>) == sizeof(axiReadAddressSt<UpA>), "axi_read addr_t direct copy requires equal envelope size" );
            copyPayload<DirectAddr>( addrOut, addrIn );
            // The channel's overridden sendAddr() drops the default
            // optional argument, so the std::nullopt is supplied
            // explicitly to satisfy the two-argument signature.
            m_down_channel.sendAddr( addrOut, std::nullopt );

            // Data phase: downstream returns, upstream answered.
            axiReadRespSt<DownD> dataIn;
            axiReadRespSt<UpD>   dataOut;
            m_down_channel.receiveData( dataIn );
            static_assert( !DirectData || sizeof(axiReadRespSt<UpD>) == sizeof(axiReadRespSt<DownD>), "axi_read data_t direct copy requires equal envelope size" );
            copyPayload<DirectData>( dataOut, dataIn );
            upIn->sendData( dataOut );
        }
    }

    void thunkOut()
    {
        // Producer (out) shape: the child producer drives DownA/DownD into
        // the owned m_down_channel; bridge each payload and drive UpA/UpD
        // onto the parent-side channel. Data flows child -> parent,
        // mirroring thunkIn() with every Up/Down role swapped. Resolve the
        // up-side interface once, from the eager channel iface or (port
        // shape) the lazily-bound parent out port.
        axi_read_out_if<UpA, UpD>* upOut =
            m_up_out_iface ? m_up_out_iface : m_up_out_port->operator->();
        while (true) {
            // Address phase: downstream receives, upstream sends.
            axiReadAddressSt<DownA> addrIn;
            axiReadAddressSt<UpA>   addrOut;
            m_down_channel.receiveAddr( addrIn );
            static_assert( !DirectAddr || sizeof(axiReadAddressSt<UpA>) == sizeof(axiReadAddressSt<DownA>), "axi_read addr_t direct copy requires equal envelope size" );
            copyPayload<DirectAddr>( addrOut, addrIn );
            // The out interface's sendAddr() carries a defaulted optional
            // argument; the std::nullopt is supplied explicitly to mirror
            // the channel-side call in thunkIn().
            upOut->sendAddr( addrOut, std::nullopt );

            // Data phase: upstream returns, downstream answered.
            axiReadRespSt<UpD>   dataIn;
            axiReadRespSt<DownD> dataOut;
            upOut->receiveData( dataIn );
            static_assert( !DirectData || sizeof(axiReadRespSt<DownD>) == sizeof(axiReadRespSt<UpD>), "axi_read data_t direct copy requires equal envelope size" );
            copyPayload<DirectData>( dataOut, dataIn );
            m_down_channel.sendData( dataOut );
        }
    }

    axi_read_in<UpA, UpD>*    m_up_port;
    axi_read_in_if<UpA, UpD>* m_up_in_iface;
    axi_read_out_if<UpA, UpD>* m_up_out_iface;
    axi_read_out<UpA, UpD>* m_up_out_port;
    axi_read_channel<DownA, DownD> m_down_channel;
};

#endif // AXI_READ_PORT_THUNKER_H
