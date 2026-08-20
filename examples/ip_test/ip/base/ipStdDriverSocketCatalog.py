# GENERATED_CODE_PARAM --block=ipStdDriver
# GENERATED_CODE_BEGIN --template=socketCatalog --section=python
CATALOG = {
    'out0': {
        "port": 'out0',
        "name": 'ipStdDriver.out0',
        "interfaceType": 'push_ack',
        "direction": 'src',
        "role": 'drive',
        "observeName": None,
    },
}

LISTEN_NAMES = (
    'ipStdDriver.out0',
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
