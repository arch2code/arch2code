from pysrc.table_format import TableFormatter

from pysrc.intf_gen_utils import get_struct_width

# A memory whose depth is a variant-bound block parameter has no single depth,
# and therefore no single size. Its size cell carries NO_SINGLE_SIZE, and every
# hierarchy total it would have contributed to is suffixed with PARTIAL_TOTAL,
# so a reader can tell a partial total from a complete one.
NO_SINGLE_SIZE = '-'
PARTIAL_TOTAL = '+'

NO_SINGLE_SIZE_NOTE = (f"{NO_SINGLE_SIZE} depth is a variant-bound block parameter, "
                       f"so this memory has no single size.\n")
PARTIAL_TOTAL_NOTE = (f"{PARTIAL_TOTAL} total excludes memories whose depth is a "
                      f"variant-bound block parameter, so it is a lower bound.\n")


def memory_geometry(prj, instance_data):
    """Resolve one memory instance's width, depth and size in KB.

    wordLinesKey names the constant a memory's depth resolves to. It is empty
    when the author sized the memory with a variant-bound block parameter
    instead, in which case the depth is the parameter symbol as written and
    there is no size, reported as None so the memory is never counted as zero.
    """
    width = get_struct_width(instance_data['structureKey'], prj.data['structures'])
    if instance_data['wordLinesKey'] == '':
        return width, instance_data['wordLines'], None
    depth = prj.getConst(instance_data['wordLinesKey'], require_int=True,
                         context_msg=f"memory '{instance_data['memory']}' depth")
    return width, depth, (width * depth) / 8192

# args from generator line
# prj object
# data set dict
def render(args, prj, data):
    match args.section:
        case 'meminst':
            return renderer_meminst(args, prj, data)
        case 'memusage':
            return renderer_memusage(args, prj, data)
        case _:
            raise ValueError(f"Unknown section '{args.section}' for template '{args.template}'. Valid values are meminst, memusage")


def create_meminsts_extractor(prj, data):
    """
    Create a data extractor function specifically for memory instances data.

    Returns:
        callable: Function that extracts data for meminsts table display
    """
    def meminsts_extractor(instance_key, instance_data, columns):
        """Extract data for each column from the memory instance data."""
        _w, _d, _size = memory_geometry(prj, instance_data)
        # Map column names to data extraction
        column_mapping = {
            'Instance': instance_key,
            'Memory': instance_data['memory'],
            'Block': instance_data['block'],
            'Structure': instance_data['structure'],
            'Description': instance_data['desc'],
            'Offset': str(instance_data.get('offset', '')),
            'RegAccess': 'Y' if instance_data.get('regAccess', 0) else 'N',
            'MemType': instance_data.get('memoryType', ''),
            'WordLines': instance_data.get('wordLines', ''),
            'AddressStruct': instance_data['addressStruct'],
            'Count': str(instance_data.get('count', '')),
            'Local': str(instance_data.get('local', '')),
            'Width' : _w,
            'Depth' : _d,
            'Size(KB)' : NO_SINGLE_SIZE if _size is None else f"{_size:.2f}",
            'Context': instance_data.get('_context', '')
        }

        return [column_mapping.get(col_name, '') for col_name, _ in columns]

    return meminsts_extractor

def format_meminsts_table(prj, data, meminsts, columns=None, border_style='ascii'):
    """
    Format memory instances data from JSON file in a text-based tabular format.

    Args:
        meminsts (dict): Memory instances data
        columns (list, optional): List of tuples (column_name, width) to display.
                                If None, uses default columns.
        border_style (str): Border style ('ascii', 'simple', 'minimal')

    Returns:
        bool: True if successful, False otherwise
    """
    # Default columns if none specified
    if columns is None:
        columns = [
            ('Instance', 0), # autosize all columns
            ('Memory', 0),
            ('Block', 0),
            ('Structure', 0),
            ('WordLines', 0),
            ('Description', 0),
            ('RegAccess', 0),
            ('MemType', 0),
            ('Width', 0),
            ('Depth', 0),
            ('Size(KB)', 0)
        ]

    # Create table formatter instance
    table = TableFormatter(border_style, max_autosize_width=80)

    # Use the generic library with our custom extractor
    extractor = create_meminsts_extractor(prj, data)

    return table.format_dict_table(
        meminsts,
        columns,
        extractor=extractor,
        title="Memory Instances Table",
    )

def build_hierarchical_usage_data(prj, data, memInsts):
    """
    Build hierarchical memory usage data from flat memory instances.

    Returns:
        dict: Hierarchical data with cumulative sizes for each hierarchy level
    """
    # Dictionary to store the hierarchical usage data
    # Key: instance path, Value: {'size': cumulative_size, 'is_memory': bool}
    hierarchical_data = {}

    # First, process all memory instances to get their individual sizes
    for instance_path, instance_data in memInsts.items():
        # Calculate memory size for this instance
        _w, _d, size_kb = memory_geometry(prj, instance_data)

        # Add the memory instance itself. A parameterized memory has no size to
        # report, and marks itself partial so it renders as such.
        hierarchical_data[instance_path] = {
            'size': size_kb,
            'is_memory': True,
            'partial': size_kb is None
        }

        # Build the hierarchy by adding parent paths
        path_parts = instance_path.split('.')
        for i in range(len(path_parts) - 1, 0, -1):  # Go from child to parent
            parent_path = '.'.join(path_parts[:i])
            if parent_path not in hierarchical_data:
                hierarchical_data[parent_path] = {
                    'size': 0.0,
                    'is_memory': False,
                    'partial': False
                }
            # Add this instance's size to all its parents. A parameterized
            # memory contributes no number, so it marks every parent total
            # partial instead of silently adding zero to it.
            if size_kb is None:
                hierarchical_data[parent_path]['partial'] = True
            else:
                hierarchical_data[parent_path]['size'] += size_kb

    return hierarchical_data

def create_usage_extractor():
    """
    Create a data extractor function specifically for memory usage data.

    Returns:
        callable: Function that extracts data for usage table display
    """
    def usage_extractor(instance_key, instance_data, columns):
        """Extract data for each column from the hierarchical usage data."""
        size = instance_data['size']
        if size is None:
            size_str = NO_SINGLE_SIZE
        elif instance_data['partial']:
            size_str = f"{size:.2f}{PARTIAL_TOTAL}"
        else:
            size_str = f"{size:.2f}"

        # Map column names to data extraction
        column_mapping = {
            'Instance': instance_key,
            'Cumulated Size (KB)': size_str,
            'M': '*' if instance_data['is_memory'] else ''
        }

        return [column_mapping.get(col_name, '') for col_name, _ in columns]

    return usage_extractor

def format_usage_table(prj, data, hierarchical_data, columns=None, border_style='ascii'):
    """
    Format hierarchical memory usage data in a text-based tabular format.

    Args:
        prj: Project object
        data: Data object
        hierarchical_data (dict): Hierarchical memory usage data
        columns (list, optional): List of tuples (column_name, width) to display.
                                If None, uses default columns.
        border_style (str): Border style ('ascii', 'simple', 'minimal')

    Returns:
        str: Formatted table string
    """
    # Default columns if none specified
    if columns is None:
        columns = [
            ('Instance', 0),  # autosize
            ('Cumulated Size (KB)', 0),  # autosize
            ('M', 0)  # autosize
        ]

    # Create table formatter instance
    table = TableFormatter(border_style, max_autosize_width=80)

    # Use the generic library with our custom extractor
    extractor = create_usage_extractor()

    # Sort the hierarchical data to group children under their immediate parents
    # Build a proper hierarchical ordering where children appear right after their parent
    def build_hierarchical_order(data):
        """
        Build a hierarchical order where children appear immediately after their parent.
        """
        ordered_items = []
        processed = set()

        def add_node_and_children(path):
            if path in processed or path not in data:
                return

            # Add this node
            ordered_items.append((path, data[path]))
            processed.add(path)

            # Find and add immediate children
            children = []
            for other_path in data:
                if other_path != path and other_path.startswith(path + '.'):
                    # Check if it's an immediate child (no additional dots after the parent path)
                    remaining_path = other_path[len(path) + 1:]
                    if '.' not in remaining_path:
                        children.append(other_path)

            # Sort children alphabetically and add them
            children.sort()
            for child_path in children:
                add_node_and_children(child_path)

        # Start with the root nodes (shortest paths first)
        root_nodes = sorted([path for path in data.keys()], key=lambda x: (len(x.split('.')), x))

        for root in root_nodes:
            if root not in processed:
                add_node_and_children(root)

        return ordered_items

    # Build the hierarchical order
    sorted_items = build_hierarchical_order(hierarchical_data)

    # Convert to ordered dict for the table formatter
    ordered_data = dict(sorted_items)

    return table.format_dict_table(
        ordered_data,
        columns,
        extractor=extractor,
        title="Per-Instance Memory Usage",
    )

def renderer_meminst(args, prj, data):
    memInsts = {}
    findMemInsts(prj, data, memInsts, data['blockName'])
    out = format_meminsts_table(prj, data, memInsts, columns=None, border_style='ascii')
    if any(memData['wordLinesKey'] == '' for memData in memInsts.values()):
        out += NO_SINGLE_SIZE_NOTE
    return out

def renderer_memusage(args, prj, data):
    memInsts = {}
    findMemInsts(prj, data, memInsts, data['blockName'])
    hierarchical_data = build_hierarchical_usage_data(prj, data, memInsts)
    out = format_usage_table(prj, data, hierarchical_data, columns=None, border_style='ascii')
    if any(entry['partial'] for entry in hierarchical_data.values()):
        out += NO_SINGLE_SIZE_NOTE + PARTIAL_TOTAL_NOTE
    return out

# Recurse sub-blocks to find memory instances across hierarchy
# each level of hierarchy is separated by '.'
def findMemInsts(prj, blockData, memInsts, hier=""):
    if 'memories' in blockData:
        for memName, memData in blockData['memories'].items():
            fullName = hier + "." + memData['memory']
            memInsts[fullName] = memData
    if 'subBlockInstances' in blockData:
        for instKey, instData in blockData['subBlockInstances'].items():
            qalData = prj.getBlockData(instData['instanceTypeKey'])
            instance = instData['instance']
            newHier = hier + "." + instance if hier else instance
            findMemInsts(prj, qalData, memInsts, newHier)
