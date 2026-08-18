# GENERATED_CODE_PARAM --block=axi4s_s_drv
# GENERATED_CODE_BEGIN --template=socketCatalog --section=python
CATALOG = {
    'axis4_t2': {
        "port": 'axis4_t2',
        "name": 'axi4s_s_drv.axis4_t2',
        "interfaceType": 'axi4_stream',
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
