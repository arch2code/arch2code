// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE
#ifndef AXI_WRITE_PORT_THUNKER_H
#define AXI_WRITE_PORT_THUNKER_H

#include "axi_write_channel.h"
#include "../../common/systemc/bitTwiddling.h"
#include "sysc/kernel/sc_dynamic_processes.h"
#include <optional>
#include <string>

// axi_write_port_thunker
//
// Header-only forwarding adapter held as a member of a generated container
// class. Bridges an upstream axi_write consumer-side endpoint carrying
// (axiWriteAddressSt<UpA>, axiWriteDataSt<UpD, UpS>) and the upstream
// response axiWriteRespSt to a downstream axi_write consumer port carrying
// (axiWriteAddressSt<DownA>, axiWriteDataSt<DownD, DownS>) and the
// downstream response axiWriteRespSt, when the corresponding payload
// structures are per-field _bitWidth equivalent but differ in nested
// _packedSt width. The per-field equivalence is validated elsewhere; this
// class performs the runtime payload bridge for the per-parameter
// envelope fields via copyPayload() and preserves the AXI write
// address / data / response handshake at both ends.
//
// DirectAddr, DirectData and DirectStrb are the generator's verdicts for the
// three payload pairs this protocol carries (addr_t, data_t and strb_t, in that
// order): true when the pair's two declarations emit identical member storage.
// The copies here are on the envelopes rather than the payloads themselves,
// which is sound because the only parameter-dependent members are
// axiWriteAddressSt<A>'s A awaddr and axiWriteDataSt<D, S>'s D wdata and
// S wstrb; every other member is the same fixed type on both sides, so
// corresponding payload storage makes the whole envelope correspond. strb_t has
// no copy site of its own — it is the second parameter of the data envelope — so
// the data envelope copy is gated by DirectData && DirectStrb. The response leg
// carries the non-templated axiWriteRespSt, identical on both sides, so it takes
// copyPayload's identity arm and needs no verdict. All three default to false,
// which is always correct and merely slower, so a hand-written instantiation
// need not supply them.
//
// Up always denotes the parent side and Down the owned child channel; this
// is a topological position, not a data-flow direction (the producer shape
// below flows Down -> Up).
//
// Single-beat semantics only: the forwarding loop pulls one address, one
// data beat and one response per iteration. Multi-beat burst transfers
// and partial writes are out of scope for the thunker; the packed-form
// check is the canonical guard against width disagreement for the wrapped
// envelope.
//
// axi_write_if.yaml lists three struct parameters (addr_t, data_t, strb_t),
// so the buildThunkerView payload enumeration is the parent's three followed
// by the child's three — the strobe types UpS and DownS are its third and
// sixth entries — and the template parameter list carries those six types in
// that order, then one verdict bool per payload pair in parameter order.
//
// Four construction shapes are supported, spanning a 2x2 family: the child
// (down) end is either a consumer (axi_write_in<DownA, DownD, DownS>&) or a
// producer (axi_write_out<DownA, DownD, DownS>&), and the parent (up) end is
// either a fully-bound channel interface base (captured eagerly) or an
// unbound parent port (resolved lazily on the spawned thread's first
// iteration, since the port's interface is not available until SystemC
// elaboration completes):
//   * connectionMap shape (consumer child, up port) — up is a parent port
//     axi_write_in<UpA, UpD, UpS>&, resolved lazily in thunkIn().
//   * connections shape (consumer child, up channel) — up is the parent-side
//     channel bound directly by its axi_write_in_if<UpA, UpD, UpS> interface
//     base, captured immediately.
//   * producer (out) shape (producer child, up channel) — the child producer
//     port axi_write_out<DownA, DownD, DownS>& drives the owned channel; the
//     thunker consumes from it and drives the bridged payload onto the
//     parent-side channel's axi_write_out_if<UpA, UpD, UpS>, captured
//     immediately. Data flows child -> parent, the reverse of the consumer
//     shapes.
//   * producer (out) port shape (producer child, up port) — as the producer
//     shape, but the up side is an unbound parent port
//     axi_write_out<UpA, UpD, UpS>& (e.g. a testbench External's inherited
//     <DUT>Inverted boundary port), resolved lazily in thunkOut(). Used when
//     a parameterized producer instance feeds a non-parameterized boundary at
//     an excluded-instance (tb/DUT) boundary.
//
// In every shape the child-side port bind to the owned channel must occur
// during SystemC elaboration; that bind is performed in the constructor
// body (which is only reached when the thunker is held as a container
// member).
template <class UpA, class UpD, class UpS,
          class DownA, class DownD, class DownS,
          bool DirectAddr = false, bool DirectData = false, bool DirectStrb = false>
class axi_write_port_thunker
{
public:
    // connectionMap shape: parent port reference.
    axi_write_port_thunker( const char* name_,
                            axi_write_in<UpA, UpD, UpS>&     upPort,
                            axi_write_in<DownA, DownD, DownS>& downPort,
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
    axi_write_port_thunker( const char* name_,
                            axi_write_in_if<UpA, UpD, UpS>&    upInIface,
                            axi_write_in<DownA, DownD, DownS>& downPort,
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
    // the parent-side channel's axi_write_out_if<UpA, UpD, UpS>.
    axi_write_port_thunker( const char* name_,
                            axi_write_out_if<UpA, UpD, UpS>&   upOutIface,
                            axi_write_out<DownA, DownD, DownS>& downPort,
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
    // (axi_write_out<UpA, UpD, UpS>&), resolved lazily in thunkOut() once its
    // interface binds during elaboration. Mirrors the connectionMap shape's
    // lazy port handling for the producer direction.
    axi_write_port_thunker( const char* name_,
                            axi_write_out<UpA, UpD, UpS>&     upPort,
                            axi_write_out<DownA, DownD, DownS>& downPort,
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
        axi_write_in_if<UpA, UpD, UpS>* upIn =
            m_up_in_iface ? m_up_in_iface : m_up_port->operator->();
        while (true) {
            // Address phase: upstream receives, downstream sends.
            axiWriteAddressSt<UpA>   addrIn;
            axiWriteAddressSt<DownA> addrOut;
            upIn->receiveAddr( addrIn );
            static_assert( !DirectAddr || sizeof(axiWriteAddressSt<DownA>) == sizeof(axiWriteAddressSt<UpA>), "axi_write addr_t direct copy requires equal envelope size" );
            copyPayload<DirectAddr>( addrOut, addrIn );
            // The channel's overridden sendAddr() drops the default
            // optional argument, so the std::nullopt is supplied
            // explicitly to satisfy the two-argument signature.
            m_down_channel.sendAddr( addrOut, std::nullopt );

            // Data phase: upstream receives, downstream sends.
            axiWriteDataSt<UpD, UpS>     dataIn;
            axiWriteDataSt<DownD, DownS> dataOut;
            upIn->receiveData( dataIn );
            static_assert( !(DirectData && DirectStrb) || sizeof(axiWriteDataSt<DownD, DownS>) == sizeof(axiWriteDataSt<UpD, UpS>), "axi_write data_t/strb_t direct copy requires equal envelope size" );
            copyPayload<DirectData && DirectStrb>( dataOut, dataIn );
            m_down_channel.sendData( dataOut );

            // Response phase: downstream returns, upstream answered.
            axiWriteRespSt respIn;
            axiWriteRespSt respOut;
            m_down_channel.receiveResp( respIn );
            copyPayload<false>( respOut, respIn );
            upIn->sendResp( respOut );
        }
    }

    void thunkOut()
    {
        // Producer (out) shape: the child producer drives DownA/DownD into
        // the owned m_down_channel; bridge each payload and drive UpA/UpD
        // onto the parent-side channel. Mirrors thunkIn() with the consumer
        // object (upIn) replaced by m_down_channel, the producer object
        // (m_down_channel) replaced by m_up_out_iface, and every Up<->Down
        // type swapped. Resolve the up-side interface once, from the eager
        // channel iface or (port shape) the lazily-bound parent out port.
        axi_write_out_if<UpA, UpD, UpS>* upOut =
            m_up_out_iface ? m_up_out_iface : m_up_out_port->operator->();
        while (true) {
            // Address phase: downstream receives, upstream sends.
            axiWriteAddressSt<DownA> addrIn;
            axiWriteAddressSt<UpA>   addrOut;
            m_down_channel.receiveAddr( addrIn );
            static_assert( !DirectAddr || sizeof(axiWriteAddressSt<UpA>) == sizeof(axiWriteAddressSt<DownA>), "axi_write addr_t direct copy requires equal envelope size" );
            copyPayload<DirectAddr>( addrOut, addrIn );
            // The out interface's sendAddr() carries a default optional
            // argument; the std::nullopt is supplied explicitly to mirror
            // thunkIn() and the channel's two-argument signature.
            upOut->sendAddr( addrOut, std::nullopt );

            // Data phase: downstream receives, upstream sends.
            axiWriteDataSt<DownD, DownS> dataIn;
            axiWriteDataSt<UpD, UpS>     dataOut;
            m_down_channel.receiveData( dataIn );
            static_assert( !(DirectData && DirectStrb) || sizeof(axiWriteDataSt<UpD, UpS>) == sizeof(axiWriteDataSt<DownD, DownS>), "axi_write data_t/strb_t direct copy requires equal envelope size" );
            copyPayload<DirectData && DirectStrb>( dataOut, dataIn );
            upOut->sendData( dataOut );

            // Response phase: upstream returns, downstream answered.
            axiWriteRespSt respIn;
            axiWriteRespSt respOut;
            upOut->receiveResp( respIn );
            copyPayload<false>( respOut, respIn );
            m_down_channel.sendResp( respOut );
        }
    }

    axi_write_in<UpA, UpD, UpS>*    m_up_port;
    axi_write_in_if<UpA, UpD, UpS>* m_up_in_iface;
    axi_write_out_if<UpA, UpD, UpS>* m_up_out_iface;
    axi_write_out<UpA, UpD, UpS>* m_up_out_port;
    axi_write_channel<DownA, DownD, DownS> m_down_channel;
};

#endif // AXI_WRITE_PORT_THUNKER_H
