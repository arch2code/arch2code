// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE
#ifndef AXI4_STREAM_PORT_THUNKER_H
#define AXI4_STREAM_PORT_THUNKER_H

#include "axi4_stream_channel.h"
#include "../../common/systemc/bitTwiddling.h"
#include "sysc/kernel/sc_dynamic_processes.h"
#include <optional>
#include <string>

// axi4_stream_port_thunker
//
// Header-only forwarding adapter held as a member of a generated container
// class. Bridges an upstream axi4_stream consumer-side endpoint carrying
// axi4StreamInfoSt<UpTDATA, UpTID, UpTDEST, UpTUSER> to a downstream
// axi4_stream consumer port carrying
// axi4StreamInfoSt<DownTDATA, DownTID, DownTDEST, DownTUSER>, when the
// corresponding payload structures are per-field _bitWidth equivalent but
// differ in nested _packedSt width. Per-field equivalence is validated
// elsewhere; this class performs the runtime payload bridge via copyPayload()
// and preserves the stream handshake at both ends.
//
// DirectTdata, DirectTid, DirectTdest and DirectTuser are the generator's
// verdicts for the four payload pairs this protocol carries (tdata_t, tid_t,
// tdest_t and tuser_t, in that order): true when the pair's two declarations
// emit identical member storage, which lets copyPayload() transfer the value
// whole instead of packing and unpacking it field by field. All four default to
// false, which is always correct and merely slower, so a hand-written
// instantiation need not supply them.
//
// The envelope is bridged member by member, unlike axi_read / axi_write which
// hand their whole envelope to copyPayload(). Two properties of
// axi4StreamInfoSt force that:
//   * it declares _packedSt and _bitWidth but no pack() / unpack(), so it
//     cannot take copyPayload()'s packed arm at all; and
//   * its tstrb and tkeep members are axi4StreamByteQualT byte qualifiers
//     whose extent is sized from tdata_t::_bitWidth, which is a property of
//     the payload's declared WIDTH and not of its member storage. No payload
//     verdict covers them: two tdata_t declarations may emit identical storage
//     (a uint64_t word array, say) at different declared widths, and then the
//     two envelopes' qualifier arrays have different extents and are not
//     interchangeable. copyInfo()'s unconditional static_assert names that
//     condition. It does not create the restriction — the qualifier assignment
//     is already ill-formed at differing widths, the two member types being
//     different — it converts an opaque template error into a stated one. It
//     holds for any junction the layout check accepted, since equal packed
//     field sequences imply equal total width.
// tlast is a plain bool on both sides and is assigned directly.
//
// Up always denotes the parent side and Down the owned child channel; this
// is a topological position, not a data-flow direction (the producer shape
// below flows Down -> Up).
//
// axi4_stream_if.yaml lists four struct parameters (tdata_t, tid_t, tdest_t,
// tuser_t), so the buildThunkerView payload enumeration is the parent's four
// followed by the child's four, and the template parameter list carries those
// eight types in that order, then one verdict bool per payload pair in
// parameter order. tstrb_t and tkeep_t are hdlparams rather than struct
// parameters and carry no verdict of their own.
//
// Four construction shapes are supported, spanning a 2x2 family: the child
// (down) end is either a consumer (axi4_stream_in<Down...>&) or a producer
// (axi4_stream_out<Down...>&), and the parent (up) end is either a fully-bound
// channel interface base (captured eagerly) or an unbound parent port
// (resolved lazily on the spawned thread's first iteration, since the port's
// interface is not available until SystemC elaboration completes):
//   * connectionMap shape (consumer child, up port) — up is a parent port
//     axi4_stream_in<Up...>&, resolved lazily in thunkIn().
//   * connections shape (consumer child, up channel) — up is the parent-side
//     channel bound directly by its axi4_stream_in_if<Up...> interface base,
//     captured immediately.
//   * producer (out) shape (producer child, up channel) — the child producer
//     port axi4_stream_out<Down...>& sends into the owned channel; the thunker
//     receives from it and sends the bridged envelope onto the parent-side
//     channel's axi4_stream_out_if<Up...>, captured immediately. Data flows
//     child -> parent, the reverse of the consumer shapes.
//   * producer (out) port shape (producer child, up port) — as the producer
//     shape, but the up side is an unbound parent port
//     axi4_stream_out<Up...>& (e.g. a testbench External's inherited
//     <DUT>Inverted boundary port), resolved lazily in thunkOut(). Used when a
//     parameterized producer instance feeds a non-parameterized boundary at an
//     excluded-instance (tb/DUT) boundary.
//
// Single-beat semantics only: the forwarding loop pulls one stream beat per
// iteration and forwards tlast unchanged, so a multi-beat packet crosses the
// adapter as its individual beats.
//
// In every shape the child-side port bind to the owned channel must occur
// during SystemC elaboration; that bind is performed in the constructor
// body (which is only reached when the thunker is held as a container
// member). The overloaded constructors are disambiguated by the child
// end's port type (axi4_stream_in vs axi4_stream_out), so the container
// generator emits identical wiring for both directions.
template <class UpTDATA, class UpTID, class UpTDEST, class UpTUSER,
          class DownTDATA, class DownTID, class DownTDEST, class DownTUSER,
          bool DirectTdata = false, bool DirectTid = false,
          bool DirectTdest = false, bool DirectTuser = false>
class axi4_stream_port_thunker
{
public:
    // connectionMap shape: parent port reference.
    axi4_stream_port_thunker( const char* name_,
                              axi4_stream_in<UpTDATA, UpTID, UpTDEST, UpTUSER>& upPort,
                              axi4_stream_in<DownTDATA, DownTID, DownTDEST, DownTUSER>& downPort,
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
    axi4_stream_port_thunker( const char* name_,
                              axi4_stream_in_if<UpTDATA, UpTID, UpTDEST, UpTUSER>& upInIface,
                              axi4_stream_in<DownTDATA, DownTID, DownTDEST, DownTUSER>& downPort,
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
    // that sends into the owned channel; the bridged envelope is sent onto
    // the parent-side channel's axi4_stream_out_if<Up...>.
    axi4_stream_port_thunker( const char* name_,
                              axi4_stream_out_if<UpTDATA, UpTID, UpTDEST, UpTUSER>& upOutIface,
                              axi4_stream_out<DownTDATA, DownTID, DownTDEST, DownTUSER>& downPort,
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
    // (axi4_stream_out<Up...>&), resolved lazily in thunkOut() once its
    // interface binds during elaboration. Mirrors the connectionMap shape's
    // lazy port handling for the producer direction.
    axi4_stream_port_thunker( const char* name_,
                              axi4_stream_out<UpTDATA, UpTID, UpTDEST, UpTUSER>& upPort,
                              axi4_stream_out<DownTDATA, DownTID, DownTDEST, DownTUSER>& downPort,
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
        axi4_stream_in_if<UpTDATA, UpTID, UpTDEST, UpTUSER>* upIn =
            m_up_in_iface ? m_up_in_iface : m_up_port->operator->();
        while (true) {
            axi4StreamInfoSt<UpTDATA, UpTID, UpTDEST, UpTUSER>         inVal;
            axi4StreamInfoSt<DownTDATA, DownTID, DownTDEST, DownTUSER> outVal;
            upIn->receiveInfo( inVal );
            copyInfo( outVal, inVal );
            // The channel's overridden sendInfo() drops the default optional
            // argument, so the std::nullopt is supplied explicitly to satisfy
            // the two-argument signature.
            m_down_channel.sendInfo( outVal, std::nullopt );
        }
    }

    void thunkOut()
    {
        // Producer (out) shape: the child producer sends the down-side
        // envelope into the owned m_down_channel; bridge each beat and send
        // the up-side envelope onto the parent-side channel. Mirrors
        // thunkIn() with every Up/Down role swapped. Resolve the up-side
        // interface once, from the eager channel iface or (port shape) the
        // lazily-bound parent out port.
        axi4_stream_out_if<UpTDATA, UpTID, UpTDEST, UpTUSER>* upOut =
            m_up_out_iface ? m_up_out_iface : m_up_out_port->operator->();
        while (true) {
            axi4StreamInfoSt<DownTDATA, DownTID, DownTDEST, DownTUSER> inVal;
            axi4StreamInfoSt<UpTDATA, UpTID, UpTDEST, UpTUSER>         outVal;
            m_down_channel.receiveInfo( inVal );
            copyInfo( outVal, inVal );
            upOut->sendInfo( outVal, std::nullopt );
        }
    }

    // Member-by-member envelope bridge, shared by both directions. Each
    // struct-parameter member takes its own verdict; the byte qualifiers are
    // assigned, which is well formed only when the two tdata_t widths agree.
    template <class ToTDATA, class ToTID, class ToTDEST, class ToTUSER,
              class FromTDATA, class FromTID, class FromTDEST, class FromTUSER>
    static void copyInfo( axi4StreamInfoSt<ToTDATA, ToTID, ToTDEST, ToTUSER>& out,
                          const axi4StreamInfoSt<FromTDATA, FromTID, FromTDEST, FromTUSER>& in )
    {
        // tstrb/tkeep are axi4StreamByteQualT sized from tdata_t::_bitWidth, a
        // declared-width property no payload verdict covers, so the two sides
        // must declare the same tdata_t width for the qualifiers to be
        // copyable at all.
        static_assert( ToTDATA::_bitWidth == FromTDATA::_bitWidth,
                       "axi4_stream tstrb/tkeep are sized from tdata_t::_bitWidth; the two sides' tdata_t must declare equal width" );
        static_assert( !DirectTdata || sizeof(ToTDATA) == sizeof(FromTDATA), "axi4_stream tdata_t direct copy requires equal payload size" );
        copyPayload<DirectTdata>( out.tdata, in.tdata );
        out.tstrb = in.tstrb;
        out.tkeep = in.tkeep;
        static_assert( !DirectTid || sizeof(ToTID) == sizeof(FromTID), "axi4_stream tid_t direct copy requires equal payload size" );
        copyPayload<DirectTid>( out.tid, in.tid );
        out.tlast = in.tlast;
        static_assert( !DirectTdest || sizeof(ToTDEST) == sizeof(FromTDEST), "axi4_stream tdest_t direct copy requires equal payload size" );
        copyPayload<DirectTdest>( out.tdest, in.tdest );
        static_assert( !DirectTuser || sizeof(ToTUSER) == sizeof(FromTUSER), "axi4_stream tuser_t direct copy requires equal payload size" );
        copyPayload<DirectTuser>( out.tuser, in.tuser );
    }

    axi4_stream_in<UpTDATA, UpTID, UpTDEST, UpTUSER>*     m_up_port;
    axi4_stream_in_if<UpTDATA, UpTID, UpTDEST, UpTUSER>*  m_up_in_iface;
    axi4_stream_out_if<UpTDATA, UpTID, UpTDEST, UpTUSER>* m_up_out_iface;
    axi4_stream_out<UpTDATA, UpTID, UpTDEST, UpTUSER>*    m_up_out_port;
    axi4_stream_channel<DownTDATA, DownTID, DownTDEST, DownTUSER> m_down_channel;
};

#endif // AXI4_STREAM_PORT_THUNKER_H
