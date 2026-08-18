# GENERATED_CODE_PARAM --block=blockF
# GENERATED_CODE_BEGIN --template=socketCatalog --section=python
CATALOG = {
    'cStuffIf': {
        "port": 'cStuffIf',
        "name": 'blockF.cStuffIf',
        "interfaceType": 'rdy_vld',
        "direction": 'src',
        "role": 'drive',
        "observeName": None,
    },
    'dStuffIf': {
        "port": 'dStuffIf',
        "name": 'blockF.dStuffIf',
        "interfaceType": 'rdy_vld',
        "direction": 'dst',
        "role": 'drive',
        "observeName": None,
    },
    'dSin': {
        "port": 'dSin',
        "name": 'blockF.dSin',
        "interfaceType": 'rdy_vld',
        "direction": 'dst',
        "role": 'drive',
        "observeName": None,
    },
    'dSout': {
        "port": 'dSout',
        "name": 'blockF.dSout',
        "interfaceType": 'rdy_vld',
        "direction": 'src',
        "role": 'drive',
        "observeName": None,
    },
    'rwD': {
        "port": 'rwD',
        "name": 'blockF.rwD',
        "interfaceType": 'status',
        "direction": 'dst',
        "role": 'observe',
        "observeName": 'blockF.rwD_obs',
    },
}

LISTEN_NAMES = (
    'blockF.cStuffIf',
    'blockF.dStuffIf',
    'blockF.dSin',
    'blockF.dSout',
    'blockF.rwD_obs',
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
