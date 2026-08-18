# GENERATED_CODE_PARAM --block=dut
# GENERATED_CODE_BEGIN --template=socketCatalog --section=python
CATALOG = {
    'streamIn': {
        "port": 'streamIn',
        "name": 'dut.streamIn',
        "interfaceType": 'push_ack',
        "direction": 'dst',
        "role": 'drive',
        "observeName": None,
    },
    'streamOut': {
        "port": 'streamOut',
        "name": 'dut.streamOut',
        "interfaceType": 'push_ack',
        "direction": 'src',
        "role": 'drive',
        "observeName": None,
    },
}

LISTEN_NAMES = (
    'dut.streamIn',
    'dut.streamOut',
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
