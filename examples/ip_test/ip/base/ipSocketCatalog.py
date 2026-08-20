# GENERATED_CODE_PARAM --block=ip
# GENERATED_CODE_BEGIN --template=socketCatalog --section=python
CATALOG = {
    'ipDataIf': {
        "port": 'ipDataIf',
        "name": 'ip.ipDataIf',
        "interfaceType": 'push_ack',
        "direction": 'dst',
        "role": 'drive',
        "observeName": None,
    },
    'regs': {
        "port": 'regs',
        "name": 'ip.regs',
        "interfaceType": 'apb',
        "direction": 'dst',
        "role": None,
        "observeName": None,
    },
}

LISTEN_NAMES = (
    'ip.ipDataIf',
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
