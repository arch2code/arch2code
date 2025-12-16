"""
Structure Diagram template for Asciidoctor documentation.

Generates structure tables for interfaces referenced by a block.
"""

from pysrc.asciidoc_structures import (
    render_structure_table,
    collect_referenced_struct_keys
)


def render(args, prj, data):
    """
    Render structure diagrams as Asciidoctor tables.
    
    Args:
        args: Command-line arguments (includes section parameter)
        prj: Project object
        data: Block data from getBlockData() or getBlockDataHier()
    
    Returns:
        Formatted Asciidoctor string with structure tables
    """
    out = ""
    
    section = getattr(args, 'section', 'all')
    
    if section == 'interfaces':
        # Render only structures referenced by interfaces
        struct_keys = set()
        
        # Collect from connection-based ports
        for port_key, port_data in data.get('ports', {}).get('connections', {}).items():
            intf_key = port_data['connection'].get('interfaceKey')
            if intf_key and intf_key in prj.data['interfaces']:
                intf_info = prj.data['interfaces'][intf_key]
                structures_data = intf_info.get('structures')
                if structures_data:
                    # structures can be either a dict or a list
                    if isinstance(structures_data, dict):
                        struct_items = structures_data.values()
                    else:
                        struct_items = structures_data
                    
                    for struct_entry in struct_items:
                        struct_key = struct_entry.get('structureKey')
                        if struct_key:
                            struct_keys.add(struct_key)
        
        # Sort by structure name for deterministic output
        if struct_keys:
            sorted_keys = sorted(struct_keys, key=lambda k: prj.data['structures'][k]['structure'])
            for struct_key in sorted_keys:
                out += render_structure_table(prj, struct_key, include_bit_ranges=True)
                out += "\n"
        else:
            out += "No interface structures found.\n\n"
    
    else:
        # Render all structures referenced by the block
        struct_keys = collect_referenced_struct_keys(prj, data)
        
        if struct_keys:
            sorted_keys = sorted(struct_keys, key=lambda k: prj.data['structures'][k]['structure'])
            for struct_key in sorted_keys:
                out += render_structure_table(prj, struct_key, include_bit_ranges=True)
                out += "\n"
        else:
            out += "No structures referenced by this block.\n\n"
    
    return out
