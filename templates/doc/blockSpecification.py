"""
Block Specification template for Asciidoctor documentation.

Generates a comprehensive block specification including interfaces, registers, memories,
and structure definitions using the new getBlockData() output format.
"""

from pysrc.asciidoc_structures import (
    render_adoc_table,
    render_structure_tables_for_block
)
from pysrc.arch2codeHelper import printError, warningAndErrorReport


def render(args, prj, data):
    """
    Render block specification as Asciidoctor markup.
    
    Args:
        args: Command-line arguments
        prj: Project object
        data: Block data from getBlockData()
    
    Returns:
        Formatted Asciidoctor string
    """
    # Belt-and-suspenders check: reject register-handler blocks
    if data['blockInfo'].get('isRegHandler', False):
        printError(f"blockSpecification template does not support register-handler blocks. "
                  f"Block '{data['blockName']}' is a register handler (implementation detail). "
                  f"Please point the marker at the parent block instead.")
        exit(warningAndErrorReport())
    
    out = ""
    block_name = data['blockName']
    
  
    # Interfaces section
    out += render_interfaces_section(prj, data, block_name)
    
    # Registers section
    out += render_registers_section(prj, data, block_name)
    
    # Memories section
    out += render_memories_section(prj, data, block_name)
    
    
    # Structures section
    out += f"== Structures referenced by {block_name}\n\n"
    out += render_structure_tables_for_block(prj, data)
    
    return out


def render_interfaces_section(prj, data, block_name):
    """Render the interfaces section with a unified table of all ports."""
    out = f"== Interfaces for {block_name}\n\n"
    
    rows = []
    
    # Process connection-based ports
    for port_key, port_data in data.get('ports', {}).get('connections', {}).items():
        direction = "Destination" if port_data.get('direction') == 'dst' else "Initiator"
        direction_str = f"{block_name} is {direction}"
        
        port_name = port_data.get('name', port_key)
        
        # Get interface info
        intf_key = port_data['connection'].get('interfaceKey')
        if intf_key and intf_key in prj.data['interfaces']:
            intf_info = prj.data['interfaces'][intf_key]
            intf_type = intf_info.get('interfaceType', 'unknown')
            desc = intf_info.get('desc', '')
            
            # Process structures
            structures_data = intf_info.get('structures')
            if structures_data:
                struct_list = []
                # structures can be either a dict or a list
                if isinstance(structures_data, dict):
                    struct_items = structures_data.values()
                else:
                    struct_items = structures_data
                
                for struct_entry in struct_items:
                    struct_name = struct_entry.get('structure', '')
                    struct_type = struct_entry.get('structureType', '')
                    if struct_name:
                        struct_list.append((struct_type, struct_name))
                
                # Add first structure with full port info
                if struct_list:
                    struct_type, struct_name = struct_list[0]
                    # Create a multi-line cell for structures if multiple
                    if len(struct_list) == 1:
                        rows.append([
                            port_name,
                            intf_type,
                            direction_str,
                            struct_type,
                            f"xref:#{struct_name}[{struct_name}]",
                            desc
                        ])
                    else:
                        # Multiple structures - format them together
                        struct_types = "\n\n".join(st for st, _ in struct_list)
                        struct_refs = "\n\n".join(f"xref:#{sn}[{sn}]" for _, sn in struct_list)
                        rows.append([
                            port_name,
                            intf_type,
                            direction_str,
                            struct_types,
                            struct_refs,
                            desc
                        ])
            else:
                # No structures
                rows.append([port_name, intf_type, direction_str, "None", "None", desc])
        else:
            # Interface not found
            rows.append([port_name, "unknown", direction_str, "None", "None", "Interface definition not found"])
    
    # Process register ports
    for port_key, port_data in data.get('ports', {}).get('registers', {}).items():
        port_name = port_data['connection'].get('register', port_key)
        reg_type = port_data['connection'].get('regType', 'unknown')
        intf_type = f"reg_{reg_type}"
        
        # Determine direction based on register type
        if reg_type == 'ro':
            direction_str = f"{block_name} is Destination"
        elif reg_type in ['rw', 'ext']:
            direction_str = f"{block_name} is Initiator"
        else:
            direction_str = f"{block_name} direction unknown"
        
        struct_key = port_data['connection'].get('structureKey')
        if struct_key and struct_key in prj.data['structures']:
            struct_name = prj.data['structures'][struct_key]['structure']
            desc = port_data['connection'].get('desc', '')
            rows.append([
                port_name,
                intf_type,
                direction_str,
                "data_t",
                f"xref:#{struct_name}[{struct_name}]",
                desc
            ])
        else:
            rows.append([port_name, intf_type, direction_str, "data_t", "unknown", ""])
    
    # Process memory ports
    for port_key, port_data in data.get('ports', {}).get('memories', {}).items():
        mem_name = port_data['connection'].get('memory', port_key)
        direction_str = f"{block_name} is Initiator"
        
        # Memory ports typically have data and address structures
        data_struct_key = port_data['connection'].get('structureKey')
        addr_struct_key = port_data['connection'].get('addressStructKey')
        desc = port_data['connection'].get('desc', '')
        
        if data_struct_key and data_struct_key in prj.data['structures']:
            data_struct_name = prj.data['structures'][data_struct_key]['structure']
            rows.append([
                mem_name,
                "memory",
                direction_str,
                "data_t",
                f"xref:#{data_struct_name}[{data_struct_name}]",
                desc
            ])
            
            # Add address structure on next row if present
            if addr_struct_key and addr_struct_key in prj.data['structures']:
                addr_struct_name = prj.data['structures'][addr_struct_key]['structure']
                rows.append([
                    "",
                    "",
                    "",
                    "addr_t",
                    f"xref:#{addr_struct_name}[{addr_struct_name}]",
                    ""
                ])
        else:
            rows.append([mem_name, "memory", direction_str, "data_t", "unknown", desc])
    
    if not rows:
        out += "No interfaces defined for this block.\n\n"
    else:
        out += render_adoc_table(
            title=f"Interfaces for {block_name}",
            headers=["Interface Name", "Interface Type", "Direction", "Structure Type", "Structure Name", "Description"],
            rows=rows,
            cols="2, 2, 2, 1, 2, 3"
        )
    
    return out


def render_registers_section(prj, data, block_name):
    """Render the registers section."""
    out = f"== Registers in {block_name}\n\n"
    
    registers = data.get('registers', {})
    
    if not registers:
        out += "No registers declared in this block.\n\n"
        return out
    
    rows = []
    for reg_key, reg_data in registers.items():
        reg_name = reg_data.get('register', reg_key)
        reg_type = reg_data.get('regType', 'unknown')
        bytes_val = reg_data.get('bytes', 'unknown')
        desc = reg_data.get('desc', '')
        
        struct_key = reg_data.get('structureKey')
        if struct_key and struct_key in prj.data['structures']:
            struct_name = prj.data['structures'][struct_key]['structure']
            struct_ref = f"xref:#{struct_name}[{struct_name}]"
        else:
            struct_ref = "unknown"
        
        rows.append([reg_name, reg_type, str(bytes_val), struct_ref, desc])
    
    out += render_adoc_table(
        title=f"Registers in {block_name}",
        headers=["Register Name", "Type", "Size (bytes)", "Structure", "Description"],
        rows=rows,
        cols="2, 1, 1, 2, 4"
    )
    
    return out


def render_memories_section(prj, data, block_name):
    """Render the memories section."""
    out = f"== Memories in {block_name}\n\n"
    
    memories = data.get('memories', {})
    
    if not memories:
        out += "No memories declared in this block.\n\n"
        return out
    
    rows = []
    for mem_key, mem_data in memories.items():
        mem_name = mem_data.get('memory', mem_key)
        block_containing = mem_data.get('block', block_name)
        
        # Word lines (with constant if available)
        word_lines_key = mem_data.get('wordLinesKey', '')
        if word_lines_key and word_lines_key in prj.data['constants']:
            word_lines_val = prj.data['constants'][word_lines_key]['value']
            word_lines_const = prj.data['constants'][word_lines_key]['constant']
            word_lines_str = f"{word_lines_const} ({word_lines_val})"
        else:
            word_lines_str = str(mem_data.get('wordLines', 'unknown'))
        
        # Count (with constant if available)
        count_key = mem_data.get('countKey', '')
        if count_key and count_key in prj.data['constants']:
            count_val = prj.data['constants'][count_key]['value']
            count_const = prj.data['constants'][count_key]['constant']
            count_str = f"{count_const} ({count_val})"
        else:
            count_str = str(mem_data.get('count', '1'))
        
        # Structures
        addr_struct_key = mem_data.get('addressStructKey')
        if addr_struct_key and addr_struct_key in prj.data['structures']:
            addr_struct_name = prj.data['structures'][addr_struct_key]['structure']
            addr_struct_ref = f"xref:#{addr_struct_name}[{addr_struct_name}]"
        else:
            addr_struct_ref = "unknown"
        
        data_struct_key = mem_data.get('structureKey')
        if data_struct_key and data_struct_key in prj.data['structures']:
            data_struct_name = prj.data['structures'][data_struct_key]['structure']
            data_struct_ref = f"xref:#{data_struct_name}[{data_struct_name}]"
        else:
            data_struct_ref = "unknown"
        
        desc = mem_data.get('desc', '')
        reg_access = "Yes" if mem_data.get('regAccess', False) else "No"
        
        rows.append([
            mem_name,
            block_containing,
            word_lines_str,
            addr_struct_ref,
            data_struct_ref,
            count_str,
            reg_access,
            desc
        ])
    
    out += render_adoc_table(
        title=f"Memories in {block_name}",
        headers=["Memory Name", "Block", "Word Lines", "Address Structure", "Data Structure", "Count", "Reg Access", "Description"],
        rows=rows,
        cols="2, 2, 1, 2, 2, 1, 1, 3"
    )
    
    return out
