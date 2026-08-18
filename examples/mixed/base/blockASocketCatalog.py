# GENERATED_CODE_PARAM --block=blockA
# GENERATED_CODE_BEGIN --template=socketCatalog --section=python
CATALOG = {
    'aStuffIf': {
        "port": 'aStuffIf',
        "name": 'blockA.aStuffIf',
        "interfaceType": 'req_ack',
        "direction": 'src',
        "role": 'drive',
        "observeName": None,
    },
    'cStuffIf': {
        "port": 'cStuffIf',
        "name": 'blockA.cStuffIf',
        "interfaceType": 'rdy_vld',
        "direction": 'src',
        "role": 'drive',
        "observeName": None,
    },
    'startDone': {
        "port": 'startDone',
        "name": 'blockA.startDone',
        "interfaceType": 'notify_ack',
        "direction": 'src',
        "role": 'drive',
        "observeName": None,
    },
    'dupIf': {
        "port": 'dupIf',
        "name": 'blockA.dupIf',
        "interfaceType": 'rdy_vld',
        "direction": 'src',
        "role": 'drive',
        "observeName": None,
    },
    'apbReg': {
        "port": 'apbReg',
        "name": 'blockA.apbReg',
        "interfaceType": 'apb',
        "direction": 'dst',
        "role": None,
        "observeName": None,
    },
}

LISTEN_NAMES = (
    'blockA.aStuffIf',
    'blockA.cStuffIf',
    'blockA.startDone',
    'blockA.dupIf',
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
