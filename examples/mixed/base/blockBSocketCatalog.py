# GENERATED_CODE_PARAM --block=blockB
# GENERATED_CODE_BEGIN --template=socketCatalog --section=python
CATALOG = {
    'btod': {
        "port": 'btod',
        "name": 'blockB.btod',
        "interfaceType": 'req_ack',
        "direction": 'dst',
        "role": 'drive',
        "observeName": None,
    },
    'startDone': {
        "port": 'startDone',
        "name": 'blockB.startDone',
        "interfaceType": 'notify_ack',
        "direction": 'dst',
        "role": 'drive',
        "observeName": None,
    },
    'dupIf': {
        "port": 'dupIf',
        "name": 'blockB.dupIf',
        "interfaceType": 'rdy_vld',
        "direction": 'dst',
        "role": 'drive',
        "observeName": None,
    },
    'apbReg': {
        "port": 'apbReg',
        "name": 'blockB.apbReg',
        "interfaceType": 'apb',
        "direction": 'dst',
        "role": None,
        "observeName": None,
    },
}

LISTEN_NAMES = (
    'blockB.btod',
    'blockB.startDone',
    'blockB.dupIf',
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
