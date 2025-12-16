"""
Reusable Asciidoctor table and structure rendering helpers for documentation generation.

This module provides utilities to render structures as Asciidoctor tables with bit ranges,
suitable for hardware documentation. It handles nested structures, arrays, and Reserved fields.
"""

from typing import Dict, Set, List, Tuple, Any
from collections import OrderedDict

from pysrc.asciidoc_bytefield import render_bytefield

def render_adoc_table(
    title: str,
    headers: List[str],
    rows: List[List[str]],
    cols: str = None
) -> str:
    """
    Render an Asciidoctor table with the given title, headers, and rows.
    
    Args:
        title: Table title (appears above the table)
        headers: List of column headers
        rows: List of rows, each row is a list of cell values
        cols: Optional column specification (e.g., "1,1,2,3")
    
    Returns:
        Formatted Asciidoctor table as a string
    """
    if not rows:
        return f".{title}\nNo data available.\n\n"
    
    out = f".{title}\n"
    
    if cols:
        out += f'[cols="{cols}"]\n'
    else:
        # Auto-generate equal-width columns
        col_spec = ", ".join(["1"] * len(headers))
        out += f'[cols="{col_spec}"]\n'
    
    out += "|===\n"
    out += "|" + " |".join(headers) + "\n\n"
    
    for row in rows:
        out += "|" + "\n|".join(str(cell) for cell in row) + "\n"
    
    out += "|===\n\n"
    
    return out


def get_field_width(prj: Any, field_data: Dict[str, Any], yamlFile: str) -> int:
    """
    Calculate the width (in bits) of a structure field.
    
    Args:
        prj: Project object with data['types'], data['structures'], data['constants']
        field_data: Field dictionary with entryType and related keys
        yamlFile: Context for lookups
    
    Returns:
        Width in bits
    """
    entry_type = field_data.get('entryType', '')
    
    if entry_type == 'NamedStruct':
        # Nested structure
        struct_key = field_data['subStructKey']
        struct_info = prj.data['structures'][struct_key]
        width = struct_info['width']
    elif entry_type == 'Reserved':
        # Reserved field has explicit width in 'align'
        width = field_data['align']
    else:  # NamedVar or NamedType
        # Look up type width
        type_key = field_data['varTypeKey']
        type_info = prj.data['types'][type_key]
        type_width = type_info['width']
        
        # Handle constant or literal width
        if isinstance(type_width, int):
            width = type_width
        else:
            # It's a constant key
            width = prj.data['constants'][type_width]['value']
    
    # Handle array size
    array_size_key = field_data.get('arraySizeKey', '')
    if array_size_key:
        array_size = prj.data['constants'][array_size_key]['value']
    else:
        array_size = field_data.get('arraySize', 1)
        if array_size == '':
            array_size = 1
        else:
            array_size = int(array_size)
    
    return width * array_size if array_size else width


def render_structure_table(
    prj: Any,
    struct_key: str,
    anchor_id: str = None,
    include_bit_ranges: bool = True
) -> str:
    """
    Render a single structure as an Asciidoctor table with bit ranges.
    
    Args:
        prj: Project object
        struct_key: Qualified structure key (structure_name/context)
        anchor_id: Optional anchor ID for cross-references (defaults to structure name)
        include_bit_ranges: Include MSB:LSB bit range column
    
    Returns:
        Formatted Asciidoctor structure table
    """
    struct_info = prj.data['structures'][struct_key]
    struct_name = struct_info['structure']
    
    if anchor_id is None:
        anchor_id = struct_name
    
    total_width = struct_info['width']
    out = f"=== {struct_name} ({total_width} bits)\n\n"
    out += f"[#{anchor_id}]\n"
    
    # Prepare table headers
    # Give more space to Description column
    headers = ["Field Name", "Type/Structure", "Bits (width)", "Description"]
    cols = "2, 2, 2, 7"
    
    # First pass: calculate all rows in MSB->LSB order
    temp_rows = []
    bit_position = struct_info['width'] - 1  # Start from MSB
    
    # Walk fields in order
    for field_name, field_data in struct_info['vars'].items():
        field_width = get_field_width(prj, field_data, struct_info['_context'])
        
        # Compute bit range [msb:lsb]
        msb = bit_position
        lsb = bit_position - field_width + 1
        if field_width > 1:
            bit_range_str = f"[{msb}:{lsb}]({field_width})"
        else:
            bit_range_str = f"[{msb}](1)"
        bit_position = lsb - 1  # Move to next field
        
        entry_type = field_data.get('entryType', '')
        
        if entry_type == 'NamedStruct':
            # Nested structure
            sub_struct = field_data['subStruct']
            type_or_struct = f"xref:#{sub_struct}[{sub_struct}]"
            
            # Add array notation if applicable (only if array size > 1)
            array_size_key = field_data.get('arraySizeKey', '')
            if array_size_key:
                array_size = prj.data['constants'][array_size_key]['value']
                try:
                    if int(array_size) > 1:
                        field_display = f"{field_data['variable']}[{array_size}]"
                    else:
                        field_display = field_data['variable']
                except (ValueError, TypeError):
                    field_display = field_data['variable']
            else:
                array_size = field_data.get('arraySize', '')
                try:
                    size_int = int(array_size) if array_size != '' else 1
                    if size_int > 1:
                        field_display = f"{field_data['variable']}[{array_size}]"
                    else:
                        field_display = field_data['variable']
                except (ValueError, TypeError):
                    field_display = field_data['variable']
            
            desc = "Embedded structure (see below)"
        elif entry_type == 'Reserved':
            field_display = field_data['variable']
            type_or_struct = "Reserved"
            desc = field_data.get('desc', 'Reserved for alignment')
        else:  # NamedVar or NamedType
            var_type_key = field_data['varTypeKey']
            type_name = prj.data['types'][var_type_key]['type']
            type_or_struct = type_name
            
            # Add array notation if applicable (only if array size > 1)
            array_size_key = field_data.get('arraySizeKey', '')
            if array_size_key:
                array_size = prj.data['constants'][array_size_key]['value']
                try:
                    if int(array_size) > 1:
                        field_display = f"{field_data['variable']}[{array_size}]"
                    else:
                        field_display = field_data['variable']
                except (ValueError, TypeError):
                    field_display = field_data['variable']
            else:
                array_size = field_data.get('arraySize', '')
                try:
                    size_int = int(array_size) if array_size != '' else 1
                    if size_int > 1:
                        field_display = f"{field_data['variable']}[{array_size}]"
                    else:
                        field_display = field_data['variable']
                except (ValueError, TypeError):
                    field_display = field_data['variable']
            
            # Get description from variable if NamedVar
            if entry_type == 'NamedVar':
                var_key = field_data['variableKey']
                desc = prj.data['variables'].get(var_key, {}).get('desc', '')
            else:
                # NamedType - use type description
                desc = prj.data['types'][var_type_key].get('desc', '')
        
        temp_rows.append([field_display, type_or_struct, bit_range_str, desc])
    
    # Reverse the rows to show in ascending bit order (LSB at top, MSB at bottom)
    rows = list(reversed(temp_rows))
    
    out += render_adoc_table(
        title=f"Structure: {struct_name}",
        headers=headers,
        rows=rows,
        cols=cols
    )
    
    return out


def collect_referenced_struct_keys(prj: Any, block_data: Dict[str, Any]) -> Set[str]:
    """
    Collect all structure keys referenced by a block (interfaces, registers, memories).
    Recursively includes embedded structures.
    
    Args:
        prj: Project object
        block_data: Block data from getBlockData()
    
    Returns:
        Set of qualified structure keys
    """
    struct_keys = set()
    
    # Helper to recursively collect embedded structs
    def collect_nested_structs(struct_key: str):
        if struct_key in struct_keys:
            return
        struct_keys.add(struct_key)
        
        struct_info = prj.data['structures'][struct_key]
        for field_name, field_data in struct_info['vars'].items():
            if field_data.get('entryType') == 'NamedStruct':
                sub_struct_key = field_data['subStructKey']
                collect_nested_structs(sub_struct_key)
    
    # Collect from connection-based ports
    for port_key, port_data in block_data.get('ports', {}).get('connections', {}).items():
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
                        collect_nested_structs(struct_key)
    
    # Collect from register ports
    for port_key, port_data in block_data.get('ports', {}).get('registers', {}).items():
        struct_key = port_data['connection'].get('structureKey')
        if struct_key:
            collect_nested_structs(struct_key)
    
    # Collect from memory ports
    for port_key, port_data in block_data.get('ports', {}).get('memories', {}).items():
        # Memory has both data structure and address structure
        data_struct_key = port_data['connection'].get('structureKey')
        if data_struct_key:
            collect_nested_structs(data_struct_key)
        addr_struct_key = port_data['connection'].get('addressStructKey')
        if addr_struct_key:
            collect_nested_structs(addr_struct_key)
    
    # Collect from registers directly (for blocks that have them)
    for reg_key, reg_data in block_data.get('registers', {}).items():
        struct_key = reg_data.get('structureKey')
        if struct_key:
            collect_nested_structs(struct_key)
    
    # Collect from memories directly
    for mem_key, mem_data in block_data.get('memories', {}).items():
        data_struct_key = mem_data.get('structureKey')
        if data_struct_key:
            collect_nested_structs(data_struct_key)
        addr_struct_key = mem_data.get('addressStructKey')
        if addr_struct_key:
            collect_nested_structs(addr_struct_key)
    
    return struct_keys


def render_structure_tables(prj: Any, struct_keys: Set[str]) -> str:
    """
    Render multiple structure tables, sorted by structure name.
    
    Args:
        prj: Project object
        struct_keys: Set of qualified structure keys to render
    
    Returns:
        Formatted Asciidoctor output with all structure tables
    """
    if not struct_keys:
        return "No structures referenced.\n\n"
    
    # Sort by structure name for deterministic output
    sorted_keys = sorted(struct_keys, key=lambda k: prj.data['structures'][k]['structure'])
    
    out = ""
    for struct_key in sorted_keys:
        out += render_structure_table(prj, struct_key, include_bit_ranges=True)
        out += "\n"
    
    return out


def render_structure_tables_for_block(prj: Any, block_data: Dict[str, Any]) -> str:
    """
    Convenience function to collect and render all structures for a block.
    
    Args:
        prj: Project object
        block_data: Block data from getBlockData()
    
    Returns:
        Formatted Asciidoctor output with all structure tables
    """
    struct_keys = collect_referenced_struct_keys(prj, block_data)
    return render_structure_tables(prj, struct_keys)

