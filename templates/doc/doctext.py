from pysrc.table_format import TableFormatter

from pysrc.intf_gen_utils import get_const, get_struct_width

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
            return ""


def create_meminsts_extractor(prj, data):
    """
    Create a data extractor function specifically for memory instances data.

    Returns:
        callable: Function that extracts data for meminsts table display
    """
    def meminsts_extractor(instance_key, instance_data, columns):
        """Extract data for each column from the memory instance data."""
        _w = get_struct_width(instance_data.get('structureKey'), prj.data['structures'])
        _d = get_const(instance_data.get('wordLinesKey'), prj.data['constants'])
        # Map column names to data extraction
        column_mapping = {
            'Instance': instance_key,
            'Memory': instance_data.get('memory', ''),
            'Block': instance_data.get('block', ''),
            'Structure': instance_data.get('structure', ''),
            'Description': instance_data.get('desc', ''),
            'Offset': str(instance_data.get('offset', '')),
            'RegAccess': 'Y' if instance_data.get('regAccess', 0) else 'N',
            'MemType': instance_data.get('memoryType', ''),
            'WordLines': instance_data.get('wordLines', ''),
            'AddressStruct': instance_data.get('addressStruct', ''),
            'Count': str(instance_data.get('count', '')),
            'Local': str(instance_data.get('local', '')),
            'Width' : _w,
            'Depth' : _d,
            'Size(KB)' : f"{(_w * _d) / 8192:.2f}",
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
        _w = get_struct_width(instance_data.get('structureKey'), prj.data['structures'])
        _d = get_const(instance_data.get('wordLinesKey'), prj.data['constants'])
        size_kb = (_w * _d) / 8192  # Convert bits to KB

        # Add the memory instance itself
        hierarchical_data[instance_path] = {
            'size': size_kb,
            'is_memory': True
        }

        # Build the hierarchy by adding parent paths
        path_parts = instance_path.split('.')
        for i in range(len(path_parts) - 1, 0, -1):  # Go from child to parent
            parent_path = '.'.join(path_parts[:i])
            if parent_path not in hierarchical_data:
                hierarchical_data[parent_path] = {
                    'size': 0.0,
                    'is_memory': False
                }
            # Add this instance's size to all its parents
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
        size = instance_data.get('size', 0.0)
        is_memory = instance_data.get('is_memory', False)

        # Map column names to data extraction
        column_mapping = {
            'Instance': instance_key,
            'Cumulated Size (KB)': f"{size:.2f}",
            'M': '*' if is_memory else ''
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
    return format_meminsts_table(prj, data, memInsts, columns=None, border_style='ascii')

def renderer_memusage(args, prj, data):
    memInsts = {}
    findMemInsts(prj, data, memInsts, data['blockName'])
    hierarchical_data = build_hierarchical_usage_data(prj, data, memInsts)
    return format_usage_table(prj, data, hierarchical_data, columns=None, border_style='ascii')

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
