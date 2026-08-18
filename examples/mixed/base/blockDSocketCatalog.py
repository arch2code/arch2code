# GENERATED_CODE_PARAM --block=blockD
# GENERATED_CODE_BEGIN --template=socketCatalog --section=python
CATALOG = {
    'cStuffIf': {
        "port": 'cStuffIf',
        "name": 'blockD.cStuffIf',
        "interfaceType": 'rdy_vld',
        "direction": 'src',
        "role": 'drive',
        "observeName": None,
    },
    'dee0': {
        "port": 'dee0',
        "name": 'blockD.dee0',
        "interfaceType": 'rdy_vld',
        "direction": 'src',
        "role": 'drive',
        "observeName": None,
    },
    'dee1': {
        "port": 'dee1',
        "name": 'blockD.dee1',
        "interfaceType": 'rdy_vld',
        "direction": 'src',
        "role": 'drive',
        "observeName": None,
    },
    'outD': {
        "port": 'outD',
        "name": 'blockD.outD',
        "interfaceType": 'rdy_vld',
        "direction": 'src',
        "role": 'drive',
        "observeName": None,
    },
    'inD': {
        "port": 'inD',
        "name": 'blockD.inD',
        "interfaceType": 'rdy_vld',
        "direction": 'dst',
        "role": 'drive',
        "observeName": None,
    },
    'btod': {
        "port": 'btod',
        "name": 'blockD.btod',
        "interfaceType": 'req_ack',
        "direction": 'dst',
        "role": 'drive',
        "observeName": None,
    },
    'rwD': {
        "port": 'rwD',
        "name": 'blockD.rwD',
        "interfaceType": 'status',
        "direction": 'dst',
        "role": 'observe',
        "observeName": 'blockD.rwD_obs',
    },
    'roBsize': {
        "port": 'roBsize',
        "name": 'blockD.roBsize',
        "interfaceType": 'status',
        "direction": 'src',
        "role": None,
        "observeName": None,
    },
    'blockBTableExt': {
        "port": 'blockBTableExt',
        "name": 'blockD.blockBTableExt',
        "interfaceType": 'memory',
        "direction": 'dst',
        "role": None,
        "observeName": None,
    },
    'blockBTable37Bit': {
        "port": 'blockBTable37Bit',
        "name": 'blockD.blockBTable37Bit',
        "interfaceType": 'memory',
        "direction": 'dst',
        "role": None,
        "observeName": None,
    },
    'blockBTable1': {
        "port": 'blockBTable1',
        "name": 'blockD.blockBTable1',
        "interfaceType": 'memory',
        "direction": 'src',
        "role": None,
        "observeName": None,
    },
    'blockBTableSP': {
        "port": 'blockBTableSP',
        "name": 'blockD.blockBTableSP',
        "interfaceType": 'memory',
        "direction": 'src',
        "role": None,
        "observeName": None,
    },
}

LISTEN_NAMES = (
    'blockD.cStuffIf',
    'blockD.dee0',
    'blockD.dee1',
    'blockD.outD',
    'blockD.inD',
    'blockD.btod',
    'blockD.rwD_obs',
)
SYNC_NAMES = ()

def required_names():
    return list(LISTEN_NAMES) + list(SYNC_NAMES)

def by_port(port):
    return CATALOG[port]

def name_for_port(port):
    return CATALOG[port]["name"]

def observe_name_for_port(port):
    return CATALOG[port]["observeName"]

# GENERATED_CODE_END
