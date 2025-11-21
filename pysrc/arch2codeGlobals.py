from pathlib import Path

# input arguments
version = '0.1.23'
debug = False
defaultInstance = '_noTopInstanceOnCommandLine'

# top level yaml filename passed in without extension
filename = ''

# Error Counter
errorCount = 0
# Warning Counter
warningCount = 0
# Disable color output in error/warning messages (useful for tests)
disableColors = False

# defaults used in multiple places
# path to graphviz outputs
gvdir = './gv_out'
# path to plantuml outputs
pudir = './pu_out'
# path to plantuml jar
pujar = Path('./pu_jar')

# defaults used specifically for diagrams
bgcolor = 'snow'
deleteGV = False
colors = ['#ffffe5', '#f7fcb9', '#d9f0a3', '#addd8e', '#78c679', '#41ab5d', '#238443', '#005a32']

# db handle
db = None
# generic cursor
cur = None
config = None
# will be set to YAMLBASEPATH
yamlBasePath = ""