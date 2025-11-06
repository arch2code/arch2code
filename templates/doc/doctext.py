from pysrc.table_format import TableFormatter

from pysrc.intf_gen_utils import get_const, get_struct_width

# args from generator line
# prj object
# data set dict
def render(args, prj, data):
    match args.section:
        case 'meminst':
            return renderer_meminst(args, prj, data)
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
    table = TableFormatter(border_style)

    # Use the generic library with our custom extractor
    extractor = create_meminsts_extractor(prj, data)

    return table.format_dict_table(
        meminsts,
        columns,
        extractor=extractor,
        title="Memory Instances Table",
    )

def renderer_meminst(args, prj, data):
    memInsts = {}
    findMemInsts(prj, data, memInsts, data['blockName'])
    return format_meminsts_table(prj, data, memInsts, columns=None, border_style='ascii')

# Recurse sub-blocks to find memory instances across hierarchy
# each level of hierarchy is separated by '.'
def findMemInsts(prj, blockData, memInsts, hier=""):
    if 'memories' in blockData:
        for memName, memData in blockData['memories'].items():
            fullName = hier + "." + memName
            memInsts[fullName] = memData
    if 'subBlockInstances' in blockData:
        for instKey, instData in blockData['subBlockInstances'].items():
            qalData = prj.getBlockData(instData['instanceTypeKey'])
            instance = instData['instance']
            newHier = hier + "." + instance if hier else instance
            findMemInsts(prj, qalData, memInsts, newHier)
