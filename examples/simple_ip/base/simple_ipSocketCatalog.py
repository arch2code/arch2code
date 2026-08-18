# GENERATED_CODE_PARAM --block=simple_ip
# GENERATED_CODE_BEGIN --template=socketCatalog --section=python
CATALOG = {
    'cpu_main': {
        "port": 'cpu_main',
        "name": 'simple_ip.cpu_main',
        "interfaceType": 'apb',
        "direction": 'dst',
        "role": None,
        "observeName": None,
    },
}

LISTEN_NAMES = ()
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
