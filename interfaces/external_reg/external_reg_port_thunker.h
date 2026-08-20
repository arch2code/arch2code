// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE
#ifndef EXTERNAL_REG_PORT_THUNKER_H
#define EXTERNAL_REG_PORT_THUNKER_H

#include "../../common/systemc/bitTwiddling.h"
#include "external_reg_channel.h"
#include "sysc/kernel/sc_dynamic_processes.h"
#include <string>

// external_reg_port_thunker
//
// Header-only forwarding adapter held as a member of a generated container
// class. Bridges an upstream external_reg consumer-side endpoint carrying UpT
// to a downstream external_reg consumer port carrying DownT, when the two
// types are per-field _bitWidth equivalent but differ in nested _packedSt
// width. Per-field equivalence is validated elsewhere; this class performs the
// runtime payload bridge via copyPayload() and republishes each observed
// value onto the other side.
//
// DirectData is the generator's verdict for the one payload pair this protocol
// carries (data_t): true when the two declarations emit identical member
// storage, which lets copyPayload() transfer the value whole instead of packing
// and unpacking it field by field. It defaults to false, which is always
// correct and merely slower, so a hand-written instantiation need not supply it.
//
// One data_t, four copy sites. external_reg is the only bidirectional
// single-payload protocol here: the same declared data_t types the register
// write value (reg_write / read) and the register read-back value (write /
// reg_read), so DirectData gates both legs of both construction shapes. The
// two legs are independently event-driven, so each shape spawns two forwarding
// threads rather than one; a single loop cannot serve them without imposing an
// ordering the protocol does not have.
//
// Up always denotes the parent side and Down the owned child channel; this
// is a topological position, not a data-flow direction.
//
// Four construction shapes are supported, spanning a 2x2 family: the child
// (down) end is either a consumer (external_reg_in<DownT>&, the register
// owner) or a producer (external_reg_out<DownT>&, the register driver), and
// the parent (up) end is either a fully-bound channel interface base (captured
// eagerly) or an unbound parent port (resolved lazily on the spawned threads'
// first iteration, since the port's interface is not available until SystemC
// elaboration completes):
//   * connectionMap shape (consumer child, up port) — up is a parent port
//     external_reg_in<UpT>&, resolved lazily in the two thunkIn* threads.
//   * connections shape (consumer child, up channel) — up is the parent-side
//     channel bound directly by its external_reg_in_if<UpT> interface base,
//     captured immediately.
//   * producer (out) shape (producer child, up channel) — the child driver
//     port external_reg_out<DownT>& drives the owned channel; the thunker
//     forwards its register writes onto the parent-side channel's
//     external_reg_out_if<UpT> and forwards the parent's read-back down.
//   * producer (out) port shape (producer child, up port) — as the producer
//     shape, but the up side is an unbound parent port external_reg_out<UpT>&
//     (e.g. a testbench External's inherited <DUT>Inverted boundary port),
//     resolved lazily in the two thunkOut* threads. Used when a parameterized
//     producer instance feeds a non-parameterized boundary at an
//     excluded-instance (tb/DUT) boundary.
//
// In every shape the child-side port bind to the owned channel must occur
// during SystemC elaboration; that bind is performed in the constructor
// body (which is only reached when the thunker is held as a container
// member). The overloaded constructors are disambiguated by the child
// end's port type (external_reg_in vs external_reg_out), so the container
// generator emits identical wiring for both directions.
template <class UpT, class DownT, bool DirectData = false>
class external_reg_port_thunker
{
public:
    // connectionMap shape: parent port reference.
    external_reg_port_thunker( const char* name_,
                               external_reg_in<UpT>&   upPort,
                               external_reg_in<DownT>& downPort,
                               std::string block_ )
      : m_up_port( &upPort ),
        m_up_in_iface( nullptr ),
        m_up_out_iface( nullptr ),
        m_up_out_port( nullptr ),
        m_down_channel( (std::string(name_) + "_ch").c_str(), block_, m_down_initial )
    {
        downPort( m_down_channel );
        sc_core::sc_spawn( [this]() { this->thunkInWrite(); } );
        sc_core::sc_spawn( [this]() { this->thunkInRead(); } );
    }

    // connections shape: parent-side channel bound by its interface base.
    external_reg_port_thunker( const char* name_,
                               external_reg_in_if<UpT>& upInIface,
                               external_reg_in<DownT>&  downPort,
                               std::string block_ )
      : m_up_port( nullptr ),
        m_up_in_iface( &upInIface ),
        m_up_out_iface( nullptr ),
        m_up_out_port( nullptr ),
        m_down_channel( (std::string(name_) + "_ch").c_str(), block_, m_down_initial )
    {
        downPort( m_down_channel );
        sc_core::sc_spawn( [this]() { this->thunkInWrite(); } );
        sc_core::sc_spawn( [this]() { this->thunkInRead(); } );
    }

    // producer (out) shape: the downstream child end is the register driver;
    // its register writes are forwarded onto the parent-side channel's
    // external_reg_out_if<UpT>, and the parent's read-back is forwarded down.
    external_reg_port_thunker( const char* name_,
                               external_reg_out_if<UpT>& upOutIface,
                               external_reg_out<DownT>&  downPort,
                               std::string block_ )
      : m_up_port( nullptr ),
        m_up_in_iface( nullptr ),
        m_up_out_iface( &upOutIface ),
        m_up_out_port( nullptr ),
        m_down_channel( (std::string(name_) + "_ch").c_str(), block_, m_down_initial )
    {
        downPort( m_down_channel );
        sc_core::sc_spawn( [this]() { this->thunkOutWrite(); } );
        sc_core::sc_spawn( [this]() { this->thunkOutRead(); } );
    }

    // producer (out) port shape: the up side is an unbound parent OUT port
    // (external_reg_out<UpT>&), resolved lazily once its interface binds
    // during elaboration. Mirrors the connectionMap shape's lazy port handling
    // for the producer direction.
    external_reg_port_thunker( const char* name_,
                               external_reg_out<UpT>&   upPort,
                               external_reg_out<DownT>& downPort,
                               std::string block_ )
      : m_up_port( nullptr ),
        m_up_in_iface( nullptr ),
        m_up_out_iface( nullptr ),
        m_up_out_port( &upPort ),
        m_down_channel( (std::string(name_) + "_ch").c_str(), block_, m_down_initial )
    {
        downPort( m_down_channel );
        sc_core::sc_spawn( [this]() { this->thunkOutWrite(); } );
        sc_core::sc_spawn( [this]() { this->thunkOutRead(); } );
    }

private:
    // Resolve the up-side consumer interface once. For the port shape, sc_port
    // binding is complete by the time a spawned thread first runs.
    external_reg_in_if<UpT>* upIn()
    {
        return m_up_in_iface ? m_up_in_iface : m_up_port->operator->();
    }

    external_reg_out_if<UpT>* upOut()
    {
        return m_up_out_iface ? m_up_out_iface : m_up_out_port->operator->();
    }

    void thunkInWrite()
    {
        // Register-write leg, parent -> child: the thunker takes the role of
        // the register owner on the parent channel and of the driver on the
        // owned channel.
        external_reg_in_if<UpT>* up = upIn();
        while (true) {
            UpT   inVal;
            DownT outVal;
            up->read( inVal );
            static_assert( !DirectData || sizeof(DownT) == sizeof(UpT), "external_reg data_t direct copy requires equal payload size" );
            copyPayload<DirectData>( outVal, inVal );
            m_down_channel.reg_write( outVal );
        }
    }

    void thunkInRead()
    {
        // Read-back leg, child -> parent: the child register owner publishes
        // its value on the owned channel; republish it on the parent channel.
        external_reg_in_if<UpT>* up = upIn();
        while (true) {
            DownT inVal;
            UpT   outVal;
            m_down_channel.reg_read( inVal );
            static_assert( !DirectData || sizeof(UpT) == sizeof(DownT), "external_reg data_t direct copy requires equal payload size" );
            copyPayload<DirectData>( outVal, inVal );
            up->write( outVal );
        }
    }

    void thunkOutWrite()
    {
        // Register-write leg, child -> parent: mirrors thunkInWrite() with the
        // channel and interface roles exchanged and every Up<->Down type
        // swapped.
        external_reg_out_if<UpT>* up = upOut();
        while (true) {
            DownT inVal;
            UpT   outVal;
            m_down_channel.read( inVal );
            static_assert( !DirectData || sizeof(UpT) == sizeof(DownT), "external_reg data_t direct copy requires equal payload size" );
            copyPayload<DirectData>( outVal, inVal );
            up->reg_write( outVal );
        }
    }

    void thunkOutRead()
    {
        // Read-back leg, parent -> child: mirrors thunkInRead() with the
        // channel and interface roles exchanged.
        external_reg_out_if<UpT>* up = upOut();
        while (true) {
            UpT   inVal;
            DownT outVal;
            up->reg_read( inVal );
            static_assert( !DirectData || sizeof(DownT) == sizeof(UpT), "external_reg data_t direct copy requires equal payload size" );
            copyPayload<DirectData>( outVal, inVal );
            m_down_channel.write( outVal );
        }
    }

    external_reg_in<UpT>*      m_up_port;
    external_reg_in_if<UpT>*   m_up_in_iface;
    external_reg_out_if<UpT>*  m_up_out_iface;
    external_reg_out<UpT>*     m_up_out_port;
    // external_reg_channel's initial-value parameter defaults to
    // `typename T::_packedSt(0)`, which is not a valid expression when the
    // packed form is a word array, so the owned channel is always handed an
    // explicit zero. Declared before m_down_channel so it is initialized first.
    //
    // The owned channel therefore starts at zero rather than at the connection's
    // declared default: the emitted adapter constructor call is fixed at four
    // arguments and carries no initial value, so a register-backed connection's
    // default_value cannot reach it. Only a reader that samples before the first
    // update can observe the difference, and readNonBlocking() has no caller
    // anywhere in the tree today.
    typename DownT::_packedSt m_down_initial{};
    external_reg_channel<DownT> m_down_channel;
};

#endif // EXTERNAL_REG_PORT_THUNKER_H
