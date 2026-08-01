from typing import Dict, OrderedDict
import pysrc.arch2codeGlobals as g
from pysrc.yamlInclude import YAML
from pysrc.arch2codeHelper import printError, printWarning, printTracebackStack, warningAndErrorReport, printIfDebug, roundup_pow2min4, clog2, convert_value
from pysrc.schema import Schema
import ruamel.yaml as YAMLRAW
import sqlite3
import os
import io
import re
import pickle
import math
import importlib
import importlib.util

from pysrc.merge_utils import merge_with_spec
from pysrc.valueResolver import ValueResolver
import pysrc.evalExpr as evalExpr
import pysrc.yamlReadCache as yamlReadCache

continueOnError = False

# Current user-YAML authoring format. A migrated project carries a single
# top-level `yamlFormat:` field in its project.yaml equal to this value; its
# absence marks a pre-migration (legacy) project that projectCreate refuses to
# build. See plan-yaml-migration.md.
CURRENT_YAML_FORMAT = 2

# yaml = YAML(typ='safe', pure=True)
yaml = YAMLRAW.YAML(typ='rt')

def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

def basePathRelative(fileName, existsError = True):
    modFile = os.path.join(g.yamlBasePath, fileName)
    if existsError:
        if not os.path.exists(modFile):
            printError(f"Unable to find {fileName}, {os.path.abspath(modFile)}")
            exit(warningAndErrorReport())
    return modFile


def existsLoad(myFile):
    if not os.path.exists(myFile):
        modFile = basePathRelative(myFile)
    else:
        modFile = myFile

    # Read via the shared byte cache so a closure file the scan-all pre-pass
    # already read parses from memory instead of a second disk read; the parse
    # is identical to reading from disk.
    return yaml.load(io.BytesIO(yamlReadCache.read(modFile)))

dirMacros = None
# Normalized layout-keyed directory representation (fileGeneration.layout). Built
# in projectCreate (buildLayout), persisted as config LAYOUT, restored in
# projectOpen. The seam reads layoutConfig['segments'][basePathKey]['path'];
# the same segment record carries buildGroup for manifest discovery.
layoutConfig = None


def _expand_with_macros(path, macros):
    """Expand a single leading $macro in path using the provided macros dict."""
    if not path or not macros:
        return path
    if path[0] != '$':
        return path

    pathKey = path[1:].split('/', 1)[0]
    if pathKey in macros:
        return path.replace(f"${pathKey}", macros[pathKey])
    return path


def expandDirMacros(myFile):
    global dirMacros
    if not dirMacros:
        return myFile
    return _expand_with_macros(myFile, dirMacros)

def sanitizeModuleToken(name):
    # Core-owned identifier sanitization for a project/include/block token: map
    # the two characters illegal in a C++ module-name / identifier segment to
    # underscore. Owned here in core (not in the template layer) because
    # projectCreate builds the owner-qualified foreign-Config file stub from it;
    # the template layer's cpp_module_name imports this same primitive so the
    # two cannot drift.
    return name.replace('-', '_').replace('.', '_')

def qualifyModuleIdentity(name, projectName):
    # Project-qualify a module / package / namespace identifier for cross-project
    # uniqueness, deduping when the name already leads with its owning project so
    # a single-project name (or an already-qualified one) stays byte-identical.
    # The '_' boundary is load-bearing: it prevents a false dedup of a name such
    # as 'debayering' under project 'debayer'. Owner comes from the intrinsic
    # per-context CONTEXTOWNINGPROJECT, so the identity is build-independent (a
    # child IP spells the same name standalone and composed).
    #
    # Sanitize both tokens so the returned identifier is a legal SV/C++
    # module/package/namespace name even when the project name carries a '-' or
    # '.' (e.g. 'my-project' -> 'my_project_ip'); the dedup test then compares
    # sanitized-vs-sanitized. sanitizeModuleToken is idempotent, so an
    # already-underscore project name stays byte-identical.
    name = sanitizeModuleToken(name)
    projectName = sanitizeModuleToken(projectName)
    if name == projectName or name.startswith(projectName + '_'):
        return name
    return f'{projectName}_{name}'

def expandNewModulePath(fileDefinition, moduleDir, module, moduleFileStub, layout, missingDirOk = False):
    # layout is the owning project's layoutConfig (PROJECTLAYOUT[owner]); the
    # caller selects it by the object's defining-context owner so a child-owned
    # object's path roots under the child project's own segments.
    fileStub = fileDefinition.get('name', '')

    basePathKey = fileDefinition.get('basePath', '')
    segment = layout['segments'][basePathKey]['path']
    if layout['mode'] == 'hierarchical':
        # decomposition node outer, functional segment inner:
        #   <node>/<segment>[/module]/file. moduleDir is the node's own absolute
        #   directory (derived in processSingleFile); the segment is the bare
        #   node-relative functional name joined onto it.
        if not moduleDir and not os.path.isabs(segment):
            # A node-relative segment with no node directory would abspath
            # against the process cwd and deposit the artifact outside the
            # project tree. Fail loudly so a miswired caller cannot leak to cwd
            # (every caller must supply the object's node dir: block/context/
            # registrar the object's own, project-scope the top context's).
            printError(f"hierarchical path resolution for '{fileStub}' has no "
                       f"node directory for node-relative segment '{segment}'")
            exit(warningAndErrorReport())
        if not os.path.exists(moduleDir) and not missingDirOk:
            printError(f"node path of {moduleDir} does not exist")
        moduleDirAbs = os.path.abspath(os.path.join(moduleDir, segment))
    else:
        # functional segment root outer, decomposition inner (unchanged):
        #   $root/<segment>/<decomp>[/module]/file.
        if not os.path.exists(segment) and not missingDirOk:
            printError(f"path of {segment} does not exist")
        moduleDirAbs = os.path.abspath(os.path.join(segment, moduleDir))
    blockDir = fileDefinition.get('blockDir', False)
    if blockDir:
        moduleDirAbs = os.path.join(moduleDirAbs, module)
    fileName = f"{moduleFileStub}{fileStub}"
    filePath = os.path.join(moduleDirAbs, fileName)
    return filePath

def fileMapCondMatch(fileDefinition, condData):
    # Evaluate a fileMap entry's cond/condAnd predicate against a block's
    # file-generation data row. OR semantics for cond (any true makes the
    # file), AND semantics for condAnd (all must hold), no predicate means
    # always make. This is the single decision the file generator (newModule)
    # and the build-manifest artifact hook share, so
    # the manifest's directory set cannot drift from the files actually emitted.
    cond = fileDefinition.get("cond", None)
    condAnd = fileDefinition.get("condAnd", None)
    makeFile = not cond
    if cond:
        for field, value in cond.items():
            if condData[field] == value:
                makeFile = True
                break
    if condAnd:
        for field, value in condAnd.items():
            if condData[field] != value:
                makeFile = False
                break
    return makeFile

    # if yaml file exists load it, otherwise return empty dict
def loadIfExists(myFile):
    if not os.path.exists(myFile):
        return {}
    with open(myFile) as f:
        ret = yaml.load(f)
    return ret

def mergeProjectConfig(projFile):
    """Merge base/pro/user project config exactly as projectCreate does during
    create and return (a2cRoot, baseProj, proProj, a2cProj, proj), without
    opening the database or running schema/address processing.

    projectCreate.__init__ calls this so create has a single merge flow; it is
    also the seam a text-only maintenance tool (the layout migration) uses to
    read the same merged fileGeneration.fileMap / dirs the generator sees, since
    a project file declares only a subset of the merged fileMap."""
    a2cRoot = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    # Only promote a2cRoot to the parent (so pro/config is merged) when the user
    # project does NOT live inside the current (base) a2cRoot. A project under
    # builder/base/ is base-only; promoting would silently pull in a sibling pro
    # tree on disk (e.g. base examples sitting next to a checked-out pro).
    baseRootAbs = os.path.abspath(a2cRoot)
    userProjAbs = os.path.abspath(projFile)
    userIsUnderBase = (userProjAbs == baseRootAbs or
                       userProjAbs.startswith(baseRootAbs + os.sep))
    if (os.path.exists(os.path.join(a2cRoot, "../pro")) and
            not userIsUnderBase):
        a2cRoot = os.path.join(a2cRoot, "../")
    a2cRoot = os.path.abspath(a2cRoot)
    proProj = loadIfExists(os.path.join(a2cRoot, "pro/config/project.yaml"))
    baseProj = loadIfExists(os.path.join(a2cRoot, "config/project.yaml"))
    userProj = existsLoad(projFile)
    # merge pro with base, then user over that, shallow dict merge by default and
    # configurable behaviour per path via MERGE_SPEC.
    a2cProj = merge_with_spec(baseProj, proProj, projectCreate.MERGE_SPEC, path=())
    proj = merge_with_spec(a2cProj, userProj, projectCreate.MERGE_SPEC, path=())
    return a2cRoot, baseProj, proProj, a2cProj, proj

def resolveFilePath(userDict, a2cDict, key, basePath):
    filePath = ''
    if key in userDict:
        filePath = userDict[key]
    elif key in a2cDict:
        filePath = a2cDict[key]
    filePath = expandDirMacros(filePath)
    return filePath

def camelCase(*words):
    # convert to camelCase leaving first letter
    out = words[0] # we dont want to capitalize the first word by force
    if len(words) > 1:
        for word in words[1:]:
            wordStr = str(word) # make sure input is a string
            if len(wordStr) > 1:
                out = out + wordStr[0].upper() + wordStr[1:]
            elif len(wordStr) == 1:
                out = out + wordStr[0].upper()
            #no need for empty sting case
    return out

def getKeyPriority(data, prioritylist):
    for key in prioritylist:
        ret = data.get(key, None)
        # filter out empty strings or missing values
        if ret:
            return key, ret
    return None, None

def getPortChannelName(row, portKeyName = 'port'):
    _, value = getKeyPriority(row, [portKeyName, 'name', 'interface'])
    return value

def getTypeWidthContext(typeInfo):
    """Return (mode, key) for active width field."""
    mode, _ = getKeyPriority(typeInfo, ['widthLog2', 'widthLog2minus1', 'width'])
    if not mode:
        mode = 'width'

    key = typeInfo.get(f"{mode}Key", None)
    if not key:
        key = None
    return mode, key

def splitQualifiedKey(qualifiedKey, label):
    if not qualifiedKey or '/' not in qualifiedKey:
        printError(f"Internal error: malformed {label} key '{qualifiedKey}' "
                   f"(expected 'name/yamlFile').")
        exit(warningAndErrorReport())
    return qualifiedKey.split('/', 1)

def qualifiedKeyContext(name, qualifiedKey, label):
    prefix = f"{name}/"
    if not name or not qualifiedKey or not qualifiedKey.startswith(prefix):
        printError(f"Internal error: {label} key mismatch: unqualified "
                   f"name '{name}' does not match qualified key "
                   f"'{qualifiedKey}'.")
        exit(warningAndErrorReport())
    context = qualifiedKey[len(prefix):]
    if not context:
        printError(f"Internal error: {label} key '{qualifiedKey}' has no "
                   f"context suffix.")
        exit(warningAndErrorReport())
    return context

def loadModule(filename):
    module = None
    if not os.path.exists(filename):
        printError(f"Unable to find {filename}")
        exit(warningAndErrorReport())
    else:
        # we are importing a python lib
        spec = importlib.util.spec_from_file_location(os.path.splitext(filename)[0], filename)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    return module

# all the project specific stuff is handled in the config class
# this is stored in database during projectCreate and retrieved later by projectOpen
# useful stuff for the generators are stored here
class config:
    data = dict()
    modeRO = True
    def __init__(self, RO = True) -> None:
        self.modeRO = RO
        if not g.cur:
            g.cur = g.db.cursor()
        if not self.modeRO:
            sql = "CREATE TABLE IF NOT EXISTS _config (item, value BLOB, context, bin integer)"
            g.cur.execute(sql)
        sql = "SELECT * from _config"
        g.cur.execute(sql)
        data = g.cur.fetchall()
        for row in data:
            if row['bin']:
                self.data[row['item']] = pickle.loads(row['value'])
            else:
                self.data[row['item']] = row['value']

    # allows storing of strings or binary objects
    def setConfig(self, item, value, bin=False):
        if self.modeRO:
            printError(f"Attempt to write {item} in config in RO mode")
            exit(warningAndErrorReport())
        if isinstance(value, dict) or isinstance(value, list):
            bin = True
        if not bin:
            self.data[item] = value
            sql = f"INSERT OR REPLACE INTO _config (item, value, context, bin) VALUES ('{item}', '{value}', '', FALSE)"
            g.cur.execute(sql)
        else:
            # binary objects are 'pickled' to store them
            # Keep in-memory cache in sync so later stages in the same run
            # (generators) can access the config without reopening the DB.
            self.data[item] = value
            pdata = pickle.dumps(value, pickle.HIGHEST_PROTOCOL)
            g.cur.execute(f"INSERT OR REPLACE INTO _config (item, value, context, bin) values ('{item}', ?, '', TRUE)", (sqlite3.Binary(pdata), ))

    def getConfig(self, item, failOk = False):
        if item not in self.data:
            if failOk:
                return None
            printError(f"Invalid config item {item} not found, or its a binary object")
            value=None
        else:
            value = self.data[item]
        return value


    def delConfig(self, item):
        if self.modeRO:
            printError(f"Attempt to delete {item} in config in RO mode")
            exit(warningAndErrorReport())
        self.data.pop(item)
        sql = f"DETELE FROM _config where item = '{item}'"
        g.cur.execute(sql)

    def clearConfig(self):
        if self.modeRO:
            printError(f"Attempt to clear config in RO mode")
            exit(warningAndErrorReport())
        self.data=dict()
        sql = f"DROP TABLE IF EXISTS _config"
        g.cur.execute(sql)

# hierarchy is defined by who contains who, or who is my parent
# this prevents the need for nested definition
def generateHierarchy(inputInstances, inputBlocks, withContext = False ):
    instances = dict()
    blocks = dict()
    hier = dict()
    hierKey = dict()
    instanceContainer = dict()
    if not withContext:
        # if we are being called from projectCreate, the input dictionaries do not have additional context depth
        # so we need to make it compatible to avoid a bunch of conditionals, and then operate as if it is the nested case
        instanceLoop = {"dummy": inputInstances}
        blockLoop = {"dummy": inputBlocks}
    else:
        instanceLoop = inputInstances
        blockLoop = inputBlocks
    for context, contextInstances in instanceLoop.items():
        for qualInst, row in contextInstances.items():
            container = row['container']
            containerKey = row['containerKey']
            instance = row['instance']
            instanceType = row['instanceType']
            instanceTypeKey = row['instanceTypeKey']
            # the two calling use cases (withContext) are slightly different so use get with fallback to loop key
            instanceKey = row.get('instanceKey', qualInst)
            if instance in instances:
                # duplicate name
                if not isinstance(instances[instance], dict):
                    # this entry is not a dict, so convert it to one
                    temp = instances[instance]
                    instances[instance] = { temp: None}
                instances[instance][instanceKey] = None
            else:
                instances[instance] = instanceKey
            #ensure both parent and child are in the map
            if instanceType not in hier:
                hier[instanceType] = OrderedDict()
            if instanceTypeKey not in hierKey:
                hierKey[instanceTypeKey] = OrderedDict()
            # topInstance is a special case that does not have a container as it is the root of the hierarchy
            if container != "_topInstance":
                if container not in hier:
                    hier[container] = OrderedDict()
                if containerKey not in hierKey:
                    hierKey[containerKey] = OrderedDict()
                hier[container][instance] = row
                hierKey[containerKey][instanceKey] = row
                blocks[container] = containerKey
                instanceContainer[instanceKey] = containerKey
    # create block to blockKey mapping
    for context, contextBlocks in blockLoop.items():
        for qualBlock, row in contextBlocks.items():
            block = row['block']
            # the two calling use cases are slightly different
            blockKey = row.get('blockKey', qualBlock)
            if block in blocks:
                if not isinstance(blocks[block], dict):
                    blocks[block] = {blocks[block]: None}
                blocks[block][blockKey] = None
            blocks[block] = blockKey
    return (hier, hierKey, instances, instanceContainer, blocks)

# project open is the class that loads the database and provides access to the data
# it is used by the generators to access the data
# it additionaly provides some helper functions to make the generators easier to write
# the database contents are stored in the data dict in manner similar to the schema
class projectOpen:
    data = dict() # all database derived data lives here. key = table name. Format corresponds to the schema
    data_by_parent = dict() # nested tables indexed by parent storage key for efficient child lookup
    tables = None
    config = None
    schema = None
    specialContexts = {"_global", "_a2csystem"} # special contexts that should be excluded from includes
    hier = dict()
    hierKey = dict()
    instances = dict() # mapping of instance names (user friendly) to qualified instance names (unique)
    blocks = dict() # mapping of block names (user friendly) to qualified block names (unique)
    rangeOfInstances = dict() # mapping of instance names (user friendly) of only a selected range
    connections = dict() # mapping of connections between the rangeOfInstances
    connectionMaps = dict() # mapping of connectionMaps in rangeOfInstances
    blockContainedConnection = dict()
    yamlContext = dict()
    includeName = dict()
    instanceContainer = None
    filemap = None
    def __init__(self, dbFile) -> None:
        if not os.path.exists(dbFile):
            printError(f"{dbFile} does not exist")
            exit(warningAndErrorReport())
        # for open we open the database read only to allow concurrency via makefile
        openString = f"file:{dbFile}?mode=ro"
        g.db = sqlite3.connect(openString, uri = True)
        if g.debug:
            # in debug mode, dont use the sqlite optimized row factory as its a pain in the debugger
            g.db.row_factory = dict_factory
        else:
            g.db.row_factory = sqlite3.Row
        g.cur = g.db.cursor()
        self.config = config()
        self.schema = Schema()
        self.tables = self.schema.get_table_names()
        g.yamlBasePath = self.config.getConfig('BASEYAMLPATH')
        self.yamlContext = self.config.getConfig('YAMLCONTEXT')
        self.includeName = self.config.getConfig('INCLUDENAME')
        self.contextOwningProject = self.config.getConfig('CONTEXTOWNINGPROJECT')
        self.contextNodeDir = self.config.getConfig('CONTEXTNODEDIR')
        self.reachableInstances = self.config.getConfig('REACHABLEINSTANCES')
        self.contextModuleIdentity = self.config.getConfig('CONTEXTMODULEIDENTITY')
        self.blockModuleName = self.config.getConfig('BLOCKMODULENAME')
        self.filemap = self.config.getConfig('FILEMAP')
        global dirMacros
        dirMacros = self.config.getConfig('DIRS')
        global layoutConfig
        layoutConfig = self.config.getConfig('LAYOUT')
        # Per-owning-project layouts, keyed by projectName (same keys as
        # contextOwningProject). Consumers select PROJECTLAYOUT[owner] to resolve
        # an object's path under the segments of the project that owns it.
        self.projectLayout = self.config.getConfig('PROJECTLAYOUT')
        printIfDebug("Data Loaded")
        self.loadData()
        self.generateHierarchy()
        # Memoization for the per-block config bundle. Read repeatedly per
        # parent block during view assembly; identical for the lifetime of
        # the open database.
        self._blockConfigBundleCache = dict()
        printIfDebug("Project loaded")

    def getSchemaNode(self, table_name):
        """
        Get the schema Node object for a given table name.

        Args:
            table_name: Full table name (e.g., 'interface_defs', 'interface_defsmodports')

        Returns:
            Node object or None if not found
        """
        return self.schema.get_node(table_name)

    def loadData(self):
        # loop through the schema loading all the tables
        for table in self.schema.tables:
            printIfDebug("Loading table: "+table)
            # we need the key for the table
            if table in self.schema.data['comboKey']:
                # if the table was defined using a combo key, then use the key field as is
                # this prevents the issue of additional context making the same key not match - eg for connectionMaps we want matches
                # with connection even if the connection and connectionMap were defined in different files (common case)
                keyName = self.schema.data['key'][table]
            else:
                # otherwise use the context version to ensure uniqueness of entries
                keyName = self.schema.data['key'][table] + 'Key'

            # Load subtables recursively (depth-first) before loading the parent table
            if table in self.schema.data['subTable']:
                self._loadSubTablesRecursive(table, self.schema.data['schema'][table], keyName)

            self.loadTable(table, self.schema.data['schema'][table], keyName)

    def _loadSubTablesRecursive(self, parentTable, parentSchema, parentKeyName, parent_key_chain=None):
        """Recursively load all subtables depth-first

        Args:
            parent_key_chain: List of parent qualified key field names (e.g., ['interface_typeKey', 'modportKey'])
        """
        if parentTable not in self.schema.data['subTable']:
            return

        for subTable in self.schema.data['subTable'][parentTable]:
            printIfDebug(f"  Loading sub table: {subTable}")

            # Get the field name that holds this subtable in the parent schema
            subTableFieldName = self.schema.data['subTable'][parentTable][subTable]
            subTableSchema = parentSchema[subTableFieldName]

            # Get the key for this subtable
            subTableKey = self.schema.data['key'][subTable]

            # Build the extended parent key chain for this subtable
            # Use the auto-derived parent_key_chain from schema (should always be available after _finalize_schema)
            extended_chain = self.schema.data.get('parentKeyChain', {}).get(subTable, [])

            # Recursively load any nested subtables first (depth-first)
            self._loadSubTablesRecursive(subTable, subTableSchema, subTableKey, extended_chain)

            # Now load this subtable with the full parent key chain
            self.loadTable(subTable, subTableSchema, subTableKey, parent_key_chain=extended_chain)

    def _reconstruct_nested_structure(self):
        """
        Reconstruct the nested dictionary structure by attaching loaded subtables
        back to their parent tables.

        This runs after all tables are loaded. For each top-level table, we walk
        through and attach its nested tables.
        """
        printIfDebug("Reconstructing nested structure...")
        print(f"DEBUG: Schema tables = {self.schema.tables}")
        print(f"DEBUG: Schema subTable keys = {list(self.schema.data['subTable'].keys())}")

        # Process each top-level table
        for table in self.schema.tables:
            if table in self.schema.data['subTable']:
                print(f"DEBUG: Processing top-level table '{table}' with subtables: {list(self.schema.data['subTable'][table].keys())}")
                self._attach_subtables_recursive(table, self.data[table], self.schema.data['schema'][table])

    def _attach_subtables_recursive(self, parentTable, parentData, parentSchema):
        """
        Recursively attach subtables to their parent entries.

        Args:
            parentTable: Name of the parent table
            parentData: Dict of parent table entries
            parentSchema: Schema definition for parent table
        """
        if parentTable not in self.schema.data['subTable']:
            return

        for subTable in self.schema.data['subTable'][parentTable]:
            subTableFieldName = self.schema.data['subTable'][parentTable][subTable]
            subTableSchema = parentSchema[subTableFieldName]
            subTableData = self.data.get(subTable, {})

            if not subTableData:
                continue

            # For each parent entry, find and attach its child entries
            for parentKey, parentEntry in parentData.items():
                # Build the grouping key for this parent
                # Get the parent's qualified key fields that children reference
                parent_key_chain = self.schema.data.get('parentKeyChain', {}).get(subTable, [])

                if parent_key_chain:
                    # Build the composite grouping key from parent's qualified key fields
                    # Example: for modportGroups with parent_key_chain=['modportKey'],
                    # we need parentEntry['modportKey'] value
                    composite_parts = []
                    for pk_field in parent_key_chain:
                        if pk_field in parentEntry:
                            composite_parts.append(str(parentEntry[pk_field]))
                        else:
                            # Parent doesn't have this key field, skip
                            break

                    if len(composite_parts) == len(parent_key_chain):
                        grouping_key = '/'.join(composite_parts)
                    else:
                        continue
                else:
                    # No parent key chain, use parent's own key
                    grouping_key = parentKey

                # Find all child entries that belong to this parent
                # Child entries were grouped by composite key during loading
                children = {}
                for childKey, childEntry in subTableData.items():
                    # Skip if childEntry is not a dict (shouldn't happen but be defensive)
                    if not isinstance(childEntry, dict):
                        continue

                    # Check if this child belongs to this parent
                    # The child's grouping key should match or start with parent's grouping_key
                    if parent_key_chain:
                        # Build child's grouping key from its parent key fields
                        child_composite_parts = []
                        for pk_field in parent_key_chain:
                            if pk_field in childEntry:
                                child_composite_parts.append(str(childEntry[pk_field]))

                        if child_composite_parts:
                            child_grouping_key = '/'.join(child_composite_parts)
                            if child_grouping_key == grouping_key:
                                # Extract the child's own key (without parent keys)
                                child_own_key = childEntry.get(self.schema.data['key'][subTable])
                                if child_own_key:
                                    children[child_own_key] = childEntry
                    else:
                        # Simple case: child has outerkey matching parent key
                        outerkey_field = None
                        for field_name, field_type in subTableSchema.items():
                            if field_type == 'outerkey':
                                outerkey_field = field_name
                                break

                        if outerkey_field and childEntry.get(outerkey_field) == parentEntry.get(outerkey_field):
                            child_own_key = childEntry.get(self.schema.data['key'][subTable])
                            if child_own_key:
                                children[child_own_key] = childEntry

                # Attach children to parent if any found
                if children:
                    parentEntry[subTableFieldName] = children

                    # Recursively process these children's subtables
                    self._attach_subtables_recursive(subTable, children, subTableSchema)

    # when parent_key_chain is None we are just creating a simple dictionary
    # when parent_key_chain is not none then the records should be grouped under composite parent key for later reassembly
    def loadTable(self, tableName, schema, keyName, parent_key_chain=None):
        """
        Load table from database and build dict structure

        Args:
            tableName: Name of the table to load
            schema: Schema definition for this table
            keyName: The anchor field name (e.g., 'interface_type')
            parent_key_chain: List of qualified parent key fields for composite grouping
                             (e.g., ['interface_typeKey', 'modportKey'])
        """

        attrib = self.schema.data['attrib'].get(tableName, [])
        columns = schema.copy()
        # figure out which mode to use
        if 'list' in attrib:
            listMode = True
        else:
            listMode = False
        innerKey = ''
        if 'multiple' in attrib:
            multi = True
            # for multi case we are adding as a dict, so need to figure out how to group the records ie what is the dict key
            # Query the schema directly instead of searching through columns
            innerKey = self.schema.data['key'].get(tableName, '')
            if innerKey == '':
                printError(f"For table {tableName} inner key not specified in schema")
                exit(warningAndErrorReport())

        else:
            multi = False
        myTable = OrderedDict()

        node = self.getSchemaNode(tableName)
        if not node:
            printError(f"Table {tableName} has no Node object in schema - this should not happen")
            exit(warningAndErrorReport())
        storage_key_field_qualified = node.get_storage_key_field_name_qualified()
        storage_key_field = node.get_storage_key_field_name()
        sql = f'SELECT * from {tableName} ORDER BY rowid'
        # Get parent storage key field name for data_by_parent indexing (only for nested tables)
        parent_key_field = node.get_parent_storage_key_field_name()
        if not node or not node.storage_key_field_qualified:
            raise ValueError(
                f"Cannot lookup children for table '{tableName}': "
                f"node.storage_key_field_qualified not configured. "
                f"This indicates a schema configuration error."
            )

        g.cur.execute(sql)
        data = g.cur.fetchall()
        firstRow = True
        previousKey = ''
        myList = list()
        myMulti = OrderedDict()
        myRow = dict()

        for row in data:
            # Build the composite key for storing this row

            # Use Node's method to build storage key for nested tables with parent chains
            # For top-level tables (parent_key_chain is None), use simple key
            newKey = node.build_storage_key(row)

            #to deal with lists/nested dicts we need to create record only when the key changes
            if newKey != previousKey:
                if not firstRow:
                    if listMode:
                        myTable[previousKey] = myList
                        myList = list()
                    elif multi:
                        # Multi-entry: individual entries stored per-row, no grouping needed
                        pass
                    else:
                        myTable[previousKey] = myRow
                else:
                    firstRow = False
                myRow = dict()
                previousKey = newKey
            # now go through the row and create the dict
            for col in columns:
                if isinstance(columns[col], dict):
                    # this is a subtable - need to look it up from the already-loaded subtable data
                    subtable_name = tableName + col

                    # Use parent-indexed structure if available
                    if subtable_name in self.data_by_parent:
                        # data_by_parent is always indexed by the qualified parent storage key
                        # Use the precomputed qualified field name from the node
                        lookup_key = row[node.storage_key_field_qualified]
                        myRow[col] = self.data_by_parent[subtable_name].get(lookup_key, None)
                    else:
                        # Top-level tables - use primary data structure
                        subtable_node = self.getSchemaNode(subtable_name)
                        if not subtable_node:
                            printError(f"Subtable {subtable_name} has no Node object in schema - this should not happen")
                            exit(warningAndErrorReport())
                        subtable_lookup_key = subtable_node.build_storage_key(row)
                        myRow[col] = self.data[subtable_name].get(subtable_lookup_key, None)
                else:
                    myRow[col] = row[col]

            # For multi-entry tables, ensure the innerKey is in myRow
            # (it might have been excluded from columns if it was myKeyName)
            if multi and innerKey and innerKey not in myRow:
                myRow[innerKey] = row[innerKey]

            if listMode:
                myList.append(myRow)
                myRow = dict()
            if multi:
                # For multi-entry tables, store individual entries in myTable using qualified keys
                # and also build grouped structure for nested access

                # Determine the qualified key for top-level storage (use row, not myRow)
                top_level_key = row[node.storage_key_field_qualified]

                # Store individual entry in top-level table
                myTable[top_level_key] = myRow

                # Also build parent-indexed structure if this is a nested table
                if parent_key_field:
                    # Check if the parent key field exists in the row (try-except for sqlite3.Row compatibility)
                    try:
                        parent_storage_key = row[parent_key_field]

                        if tableName not in self.data_by_parent:
                            self.data_by_parent[tableName] = {}
                        if parent_storage_key not in self.data_by_parent[tableName]:
                            self.data_by_parent[tableName][parent_storage_key] = {}

                        # Index by anchor field for user-friendly nested access (e.g., 'src', 'dst')
                        # or by storage key for combo/collapsed tables (e.g., 'blockAaStuffIf')
                        if node and node.anchor_field:
                            nested_index_key = myRow[node.anchor_field]
                        else:
                            # For tables without anchor (combo/collapsed), use storage key value
                            nested_index_key = myRow[innerKey]
                        self.data_by_parent[tableName][parent_storage_key][nested_index_key] = myRow
                    except (KeyError, IndexError) as e:
                        # Parent key field not in this row (shouldn't happen for properly configured nested tables)
                        raise ValueError(
                            f"Failed to build data_by_parent for table '{tableName}': {e}. "
                            f"parent_key_field='{parent_key_field}', "
                            f"This indicates a schema configuration error or missing parent key in row."
                        )

                myRow = dict()
        # the last record may need to be added
        if not firstRow:
            if listMode:
                myTable[previousKey] = myList
            elif multi:
                # Multi-entry: already stored individual entries, nothing to do
                pass
            else:
                myTable[previousKey] = myRow

        self.data[tableName] = myTable

    # hierarchy is defined by who contains who, or who is my parent
    # this prevents the need for nested definition
    def generateHierarchy(self):
        (hier, hierKey, qualInstances, instanceContainer, blocks) = generateHierarchy(self.data['instances'], self.data['blocks'])
        self.hier = hier
        self.hierKey = hierKey
        self.instances = qualInstances
        self.instanceContainer = instanceContainer
        self.blocks = blocks

    def getQualTop(self, instanceTop):
        if instanceTop==g.defaultInstance:
            instanceTop = self.config.getConfig('TOPINSTANCE')
        # top instance may be a fully qualified name already - check

        return self.getQualInstance(instanceTop)

    # instance maybe qualified or not, make sure it is
    def getQualInstance(self, instance):
        # top instance may be a fully qualified name already - check
        if instance in self.data['instances']:
            qual = instance
        else:
            #its not a fully qualified name so lets try and convert
            qual = self.qualInstance(instance)
            if isinstance(qual, dict):
                printError(f"The instance specified: {instance} is not a unique instance in the design.\nPlease use a unique instance or a fully qualified instance name instead. Possible fully qualified names for specified instance are:")
                for inst in qual:
                    printWarning(inst)
                exit(warningAndErrorReport())
        return qual

    # convert map of instances
    def getQualInstances(self, instances):
        ret = dict()
        for inst in instances:
            ret[self.getQualInstance(inst)] = 0
        return ret

    # instance maybe qualified or not, make sure it is
    def getQualBlock(self, block):
        # top instance may be a fully qualified name already - check
        if block in self.data['blocks']:
            qual = block
        else:
            if block not in self.blocks:
                printError(f"The block specified: {block} does not exist in the design")
                exit(warningAndErrorReport())
            #its not a fully qualified name so lets try and convert
            if isinstance(self.blocks[block], dict):
                printError(f"The block specified: {block} is not a unique instance in the design.\nPlease use a unique or a fully qualified block name instead. Possible fully qualified names are:")
                for myBlock in self.blocks[block]:
                    printWarning(myBlock)
                exit(warningAndErrorReport())
            qual = self.blocks[block]
        return qual

    def resolveFileOwner(self, params):
        # Absolute ownership resolution for the generator gate. A generated file's
        # owning context is named by the params on its GENERATED_CODE_PARAM line;
        # the owning project is that context's entry in contextOwningProject, which
        # holds each context's declared owning projectName identically whether that
        # project is the current build root or a referenced child. Returns the
        # owning projectName, or None for files that name no owning context
        # (hierarchy/scope framework scaffolds), which are always generated.
        #
        # Branch order is load-bearing: --project MUST be checked before
        # --parent/--block/--context and must not be "simplified" into them.
        # yamlContext keys are build-root-relative, so a child project's
        # standalone build stamps its context files with a child-relative
        # --context spelling that a composed parent build cannot resolve
        # (resolveContextKey exits on a non-exact key rather than falling back to
        # a basename match). --project is the only token that lets the parent
        # identify a child-owned file and skip it.
        if params.project:
            # Project-mode artifact (e.g. rtl.f): the owning projectName is named
            # directly on the GENERATED_CODE_PARAM line, so no context resolution
            # is needed. projectLayout is keyed by projectName (same keys as
            # contextOwningProject values), so an unknown name is a corrupt stamp.
            if params.project not in self.projectLayout:
                printError("The project specified in GENERATED_CODE_PARAM: {} is not a known project.\n"
                    "Possible valid projects are: {}".format(params.project, list(self.projectLayout.keys())))
                exit(warningAndErrorReport())
            return params.project
        if params.parent:
            # Registrar trampoline: parent-owned (lands under the assembler block).
            context = self.data['blocks'][self.getQualBlock(params.parent)]['_context']
        elif params.block:
            context = self.data['blocks'][self.getQualBlock(params.block)]['_context']
        elif params.context:
            # A migrated context file carries --project and resolves through the
            # branch above; this --context branch is the un-migrated fallthrough for
            # an old-form stamp that names only its context (every context listed on
            # one file shares an owner, so the first resolves it). The build-root/
            # basename round-trip was retired, so resolveContextKey requires an exact
            # yamlContext key: an old stamp resolves only when its context spelling
            # already matches this build's key, i.e. `make migrate` is the
            # prerequisite for stamps predating --project.
            context = self.resolveContextKey(params.context[0])
        else:
            return None
        return self.contextOwningProject[context]

    def getModuleFilename(self, filekey, module, fileType):
        fileDefinition = self.filemap.get(filekey, None)
        if not fileDefinition:
            printError(f"File type {filekey} not defined in project file filemap section")
            exit(warningAndErrorReport())
        fileStub = fileDefinition.get('name', '')
        extension = fileDefinition['ext'].get(fileType, None)
        if not extension:
            printError(f"File type {fileType} not defined in filemap->ext")
            exit(warningAndErrorReport())
        fileName = f"{module}{fileStub}.{extension}"
        return fileName

    def _build_enum_lookup(self):
        """Build a lookup dictionary for enum values (lazy initialization)"""
        if hasattr(self, '_enum_lookup'):
            return

        self._enum_lookup = {}

        # Build lookup from typesenum table
        # typesenum is organized as: {'enumType/file.yaml': [list of enum entries]}
        # Each enum entry has 'enumName' and 'value' fields
        if 'typesenum' in self.data:
            for enum_type_key, enum_list in self.data['typesenum'].items():
                if isinstance(enum_list, list):
                    for enum_entry in enum_list:
                        if isinstance(enum_entry, dict):
                            enum_name = enum_entry.get('enumName')
                            enum_value = enum_entry.get('value')
                            context = enum_entry.get('_context', '')

                            if enum_name and context and enum_value is not None:
                                qual_enum_name = f"{enum_name}/{context}"
                                self._enum_lookup[qual_enum_name] = enum_value

    def getConst(self, value, require_int=False, context_msg=None):
        try:
            ret = int(value)
        except (ValueError, TypeError):
            ret = None

            # Try float literal
            try:
                ret = float(value)
            except (ValueError, TypeError):
                pass

            # Look up in constants table using qualified key
            if ret is None and 'constants' in self.data and value in self.data['constants']:
                const_data = self.data['constants'][value]
                if isinstance(const_data, dict):
                    ret = const_data.get('value', None)

            # If not found in constants, look up in enum lookup dictionary
            if ret is None:
                self._build_enum_lookup()
                ret = self._enum_lookup.get(value, None)

            if ret is None:
                printError(f"Unknown constant '{value}'")
                exit(warningAndErrorReport())

        if require_int and isinstance(ret, float):
            msg = f"Constant '{value}' resolves to floating-point value ({ret})"
            if context_msg:
                msg += f", but {context_msg} requires an integer"
            printError(msg)
            exit(warningAndErrorReport())

        return ret

    def resolveTypeWidth(self, typeInfo):
        """Resolve type width to integer from whichever width field is present.

        Handles width, widthLog2, widthLog2minus1, and isSigned adjustment.
        Uses getConst for resolution (projectOpen context).
        Schema validation guarantees all width fields exist in typeInfo.
        """
        isSigned = typeInfo['isSigned']
        mode, key = getTypeWidthContext(typeInfo)
        rawValue = self.getConst(key, require_int=True, context_msg="type width") if key else typeInfo[mode]
        n = int(rawValue)

        if mode == 'widthLog2':
            width = n.bit_length()
            if isSigned:
                width += 1
        elif mode == 'widthLog2minus1':
            width = int(n - 1).bit_length()
            if isSigned:
                width += 1
        else:
            width = n
        return width


    # based on a block get the sub hier tree
    def getSubHier(self, topBlock):
        startBlock = self.getQualBlock(topBlock)
        ret = dict()
        nextLoop = dict()
        ret[startBlock] = 0
        nextLoop[startBlock] = self.hierKey[startBlock]
        while nextLoop:
            todo = nextLoop
            nextLoop = dict()
            for block,instances in todo.items():
                for instance, instanceValue in instances.items():
                    if instanceValue['instanceTypeKey'] not in ret:
                        nextLoop[instanceValue['instanceTypeKey']] = self.hierKey[instanceValue['instanceTypeKey']]
                        ret[instanceValue['instanceTypeKey']] = 0

        #for block in
        return ret

    # based on the list of contexts provided generate easy accessable structure for jinja
    # dataTypeMapping is a list ordered by maxSize which is used to map into platform specific types
    # each list entry should be a dict having the following required and optional keys
    #          'maxSize' : required - field indicating the largest bit width supported
    #             'type' : required - platform specific type string eg bool
    #            'array' : optional - if bitwidth needs to be in an array eg pc largest size = 64 bit so an array is used intead
    # 'arrayElementSize' : optional - if array is used, how many bits per array
    def resolveContextKey(self, name):
        # A context name on a GENERATED_CODE_PARAM line is the canonical
        # yamlContext key. yamlContext, includeName and contextOwningProject all
        # share these keys, so the returned key indexes any of them. Context
        # files carry both --project (owner, resolved directly by
        # resolveFileOwner) and --context stamped to the canonical key by
        # newModule/migration, so render always exact-matches here; no
        # basename/build-root reconciliation is needed. Exits on an unknown name.
        if name in self.yamlContext:
            return name
        printError("The context specified in GENERATED_CODE_PARAM: {} is not a known context.\n"
            "A generated file stamped before --project names its context relative to the build root\n"
            "that scaffolded it, which this build root cannot resolve. Run `make migrate` to re-stamp\n"
            "the existing artifacts with --project and the canonical context key.\n"
            "Possible valid contexts are: {}".format(name, list(self.yamlContext.keys())))
        exit(warningAndErrorReport())

    def getContextData(self, contexts, dataTypeMapping):
        ret = dict()
        enums = dict()
        ret['includeContext'] = dict()
        includes = self.config.getConfig('INCLUDEFILES')
        ret['includeFiles'] = includes
        # Canonicalize each context name (as it may appear on a
        # GENERATED_CODE_PARAM line) to its yamlContext key before use.
        for i, context in enumerate(contexts):
            contexts[i] = self.resolveContextKey(context)
        for context in contexts:
            for k in self.yamlContext[context]:
                ret['includeContext'][k] = 0
        objects = ['constants', 'types', 'structures', 'encoders']
        ret['specialStructures'] = OrderedDict()
        for object in objects:
            ret[object] = OrderedDict()
            for key, value in self.data[object].items():
                if value['_context'] in contexts:
                    if object=='structures':
                        if key in self.data['specialStructures']:
                            ret['specialStructures'][key] = value
                        else:
                            ret[object][key] = value
                    if object=='constants':
                        ret[object][key] = value
                        safeValue = self.getConst(value["value"])
                        declaredType = value['valueType']
                        loc = f"{value['_context']}:{value['lc'].line + 1}" if 'lc' in value else value.get('_context', '?')

                        if declaredType == 'real':
                            if isinstance(safeValue, int):
                                safeValue = float(safeValue)
                                ret[object][key]['value'] = safeValue
                            elif not isinstance(safeValue, float):
                                printError(f"In {loc}, constant '{key}': valueType is 'real' but value is not numeric")
                                exit(warningAndErrorReport())
                        elif declaredType in ('int', 'uint'):
                            if isinstance(safeValue, float):
                                printError(f"In {loc}, constant '{key}': valueType is '{declaredType}' but eval produced a float ({safeValue}). "
                                           f"Use // for integer division, or set valueType: real")
                                exit(warningAndErrorReport())
                            if not isinstance(safeValue, int):
                                printError(f"In {loc}, constant '{key}': valueType is '{declaredType}' but value is not an integer")
                                exit(warningAndErrorReport())
                            if declaredType == 'uint' and safeValue < 0:
                                printError(f"In {loc}, constant '{key}': valueType is 'uint' but value is negative ({safeValue}). "
                                           f"Use valueType: int for signed constants")
                                exit(warningAndErrorReport())
                        ret[object][key]['valueType'] = declaredType
                    if object=='types':
                        if value['enum']:
                            enums[key] = value
                            enums[key]['descSpaces'] = max(0, 20-len(value['type']))
                            for myEnum in value['enum']:
                                enumLen = len(myEnum['enumName'])+len(str(myEnum['value']))
                                myEnum['descSpaces'] = max(0, 20-enumLen)
                        else:
                            ret[object][key] = value
                            bitwidth = self.resolveTypeWidth(value)
                            isSigned = value['isSigned']
                            # loop through ordered list
                            thisType = None
                            typeArraySize = 1
                            for myType in dataTypeMapping:
                                if bitwidth <= myType['maxSize']:
                                    arrayElementSize = myType.get('arrayElementSize', 0)
                                    if arrayElementSize > 0:
                                        # round up to the nearest multiple using integer div, plus one if there is a modulo non zero
                                        typeArraySize = bitwidth // arrayElementSize + (bitwidth % arrayElementSize > 0)
                                    # Select signed or unsigned type based on isSigned flag
                                    thisType = myType['signedType'] if isSigned else myType['unsignedType']
                                    #if we found something terminate the list as we want the smallest type
                                    break
                            if thisType is None:
                                printError(f"Unknown Bitwidth for {key}")
                                exit(warningAndErrorReport())
                            ret[object][key]['platformDataType'] = thisType
                            ret[object][key]['typeArraySize'] = typeArraySize
                            ret[object][key]['realwidth'] = bitwidth
                    if object=='encoders':
                        ret[object][key] = value
                        bits = int(value["totalBits"])
                        for itemKey, itemVal in value['items'].items():
                            if itemVal["numBitsKey"] !="":
                                entryBits = self.getConst(itemVal["numBitsKey"])
                            else:
                                entryBits = int(itemVal["numBits"])
                            encodingMask = ((1 << bits) - 1) ^ ((1 << entryBits) - 1)
                            itemVal['numBitsInt'] = entryBits
                            itemVal['encodingMask'] = encodingMask


        ret['enums'] = enums
        ret['context'] = context
        # Language-neutral identity of the context being rendered. Emitters apply
        # their own spelling: SystemC module/namespace names come from
        # `contextModuleIdentity` (the project-owned C++ linkage identity), the SV
        # package name comes from `includeName` (the raw include stem), while the
        # legacy default-Config struct name and the structure-test class name come
        # from `contextStem` (the context file basename), preserving their
        # existing file-basename source.
        ret['contextModuleIdentity'] = self.contextModuleIdentity[context]
        ret['contextStem'] = os.path.splitext(os.path.basename(context))[0]
        # Per-context RTL output directory, expressed relative to the project's
        # rtl.f location, keyed by include-chain context. The RTL filelist
        # template emits these for +incdir/-y and package lines. A context owned
        # by a referenced child project roots under THAT child's rtl segment
        # (via contextOwningProject + projectLayout), so a cross-project package
        # resolves to the child's rtl/ output rather than its yaml source tree.
        ret['contextRtlDir'] = self._contextRtlDirs(ret['includeContext'])
        # Per-context Config-header inputs. The view here is what
        # `templates/systemc/includes.py` includeConfig() consumes; the
        # template performs no cross-block walks of `prj.data['blocks']`.
        # Names are prefixed with `context` to keep them distinct from the
        # block-view `variantConfigs` field; SystemVerilog generation
        # merges context-view fields over block-view fields via
        # `data.update`, so overlapping names would silently shadow.
        view = self.getContextConfigView(contexts)
        ret['contextVariantConfigs']      = view['variantConfigs']
        ret['contextBlockParamSynthetic'] = view['blockParamSynthetic']
        return ret

    def _contextRtlDirs(self, includeContext):
        # Resolve each include-chain context to the directory holding its
        # generated RTL artifacts (package + library modules), relative to the
        # root project's rtl.f location. The RTL package files land in the
        # `package` fileType's basePath segment. The two layouts resolve this
        # differently (branch below): functional segments are $root-absolute, so
        # a context's rtl subdir mirrors its yaml subdir within the OWNING
        # project's tree (yaml-relative arithmetic); hierarchical segments are
        # bare node-relative names joined onto a node dir at emit time, so both
        # rtl.f and each package are resolved through the emit seam
        # (expandNewModulePath) against their node dirs. Path composition mirrors
        # the newModule/saveIncludeFiles seam (contextOwningProject +
        # projectLayout[owner]).
        fileMap = self.config.getConfig('FILEMAP')
        rootName = self.config.getConfig('PROJECTNAME')
        rootLayout = self.projectLayout[rootName]
        rtlSegKey = fileMap['package']['basePath']
        # A project without an rtl segment emits no rtl.f, so nothing consumes
        # this map; return empty rather than fabricating a directory.
        if rtlSegKey not in rootLayout['segments']:
            return dict()
        rootYaml = rootLayout['yaml']
        ret = dict()
        if rootLayout['mode'] == 'hierarchical':
            # Under hierarchical the rtl segment is a bare node-relative name
            # joined onto a node directory at emit time, so both rtl.f and every
            # context package land at <node>/<rtlSeg>/. Resolve each endpoint
            # through the same seam (expandNewModulePath) that placed the files:
            # rtl.f anchors to the top context's node (mirrors newModule), each
            # context package to its own node (mirrors saveIncludeFiles). The
            # yaml-relative arithmetic used for functional cannot apply here
            # because the segment path is a bare node-relative name, not a
            # $root-absolute directory. Each context's node dir comes from the
            # persisted per-context map (CONTEXTNODEDIR), which covers types-only
            # contexts that emit an RTL package but define no block.
            topContext = self.config.getConfig('TOPCONTEXT')
            if topContext is None:
                # A definitions-only project (no topInstance) emits no rtl.f, so
                # this map has no consumer; the functional branch tolerates the
                # same case by never anchoring on a topInstance.
                return dict()
            rtlDotFdir = os.path.dirname(expandNewModulePath(
                fileMap['rtlDotF'], self.contextNodeDir[topContext], '', '',
                rootLayout, missingDirOk=True))
            for context in includeContext:
                ownerLayout = self.projectLayout[self.contextOwningProject[context]]
                includeName = self.includeName[context]
                pkgDir = os.path.dirname(expandNewModulePath(
                    fileMap['package'], self.contextNodeDir[context], includeName,
                    includeName, ownerLayout, missingDirOk=True))
                ret[context] = os.path.relpath(pkgDir, rtlDotFdir)
            return ret
        rtlDotFdir = rootLayout['segments'][rtlSegKey]['path']
        for context in includeContext:
            owner = self.contextOwningProject[context]
            ownerLayout = self.projectLayout[owner]
            absYaml = os.path.normpath(os.path.join(rootYaml, context))
            subdir = os.path.dirname(os.path.relpath(absYaml, ownerLayout['yaml']))
            absRtlDir = os.path.normpath(
                os.path.join(ownerLayout['segments'][rtlSegKey]['path'], subdir))
            ret[context] = os.path.relpath(absRtlDir, rtlDotFdir)
        return ret

    def getContextConfigView(self, contexts):
        # Single-pass context Config view. Walks the blocks whose primary
        # `_context` matches one of the supplied contexts exactly once and
        # returns both Config-header inputs:
        #   variantConfigs:     per-variant descriptors aggregated across
        #                       parameterizable blocks. Each entry is
        #                       `{qualBlock, descriptor}` so the template
        #                       renders the descriptor while keeping block
        #                       provenance for diagnostics. Intra-block dedup
        #                       (`duplicateOf`) is preserved on the descriptor;
        #                       the template skips duplicates.
        #   blockParamSynthetic: block params declared via `params:` without a
        #                       backing parameterizable constant. Each appears
        #                       as a field on per-variant Config structs but has
        #                       no default value in `data['constants']`, so this
        #                       view supplies the Config member type contract.
        ctx_set = set(contexts) if isinstance(contexts, (list, set, tuple)) else {contexts}
        constants_by_name = {
            const_row['constant']
            for const_row in self.data['constants'].values()
            if const_row['isParameterizable']
            and const_row['_context'] in ctx_set
        }
        variantConfigs = []
        synthetic = dict()
        for qualBlock, blockRow in self.data['blocks'].items():
            # Group a block's Config emission under its canonical config context
            # (where its Config struct is emitted), not its declaring context.
            # Non-parameterizable blocks have an empty configContext and never
            # match a context set.
            if blockRow['configContext'] not in ctx_set:
                continue
            bundle = self.getBlockConfigView(qualBlock)
            if bundle['isParameterizable']:
                for desc in bundle['variantConfigs']:
                    variantConfigs.append({'qualBlock': qualBlock, 'descriptor': desc})
            for param_row in blockRow.get('params', []) or []:
                name = param_row['param']
                if name in constants_by_name or name in synthetic:
                    continue
                synthetic[name] = {'valueType': 'uint', 'maxValue': 0}
        return {'variantConfigs': variantConfigs, 'blockParamSynthetic': synthetic}

    # do some preproccessing to assemble subset of data easily accessed by templates
    # from perspective of qualBlock
    # subBlocks will be referenced if in the set of instances
    # this would be easier in SQL..
    def getBlockData(self, qualBlock, trimRegLeafInstance=False, excludeInstances=set()):
        blockDataSet = {'connections','memoryConnections', 'registerConnections', 'connectionMaps', 'connectionPorts', 'memoryPorts',
                        'registerPorts', 'connectionMapPorts', 'ports', 'connectDouble', 'connectSingle', 'subBlocks', 'includeContext',
                        'classIncludeContext', 'configIncludeContext', 'foreignConfigModules',
                        'addressDecode', 'variants', 'declaredVariants', 'interfaceTypes', 'prunedConnections', 'interface_defs', 'interface_type_mappings',
                        'interface_type_mappings_qualified'}
        ret = dict()
        # create some of the simple returns
        ret['includeFiles'] = self.config.getConfig('INCLUDEFILES')
        ret['qualBlock'] = qualBlock
        ret['blockInfo'] = self.data['blocks'][qualBlock]
        ret['temp'] = dict()
        ret['temp']['structs'] = dict()
        ret['temp']['consts'] = dict()
        ret['temp']['registerInterfaceTypes'] = dict()
        for k in blockDataSet:
            ret[k] = dict()
        ret['addressDecode']['hasDecoder'] = False
        # assemble the instance information. This is the instances of the qualBlock and any contained instances
        self.getBDInstances(qualBlock, ret, trimRegLeafInstance, excludeInstances)
        # get all the register and memory information
        self.getBDRegistersMemories(qualBlock, ret)
        # based on memories and registers, do we need address decoding etc
        self.getBDAddressDecode(ret)
        # address bus info
        self.getBDAddressBus(ret)
        # memory connections
        self.getBDMemoryConnections(ret)
        # register connections
        if ret['enableRegConnections']:
            self.getBDRegisterConnections(ret)
            if not ret['blockInfo']['isRegHandler']:
                ret['registers'] = dict()
        # connection maps
        self.getBDConnectionMaps(ret)
        # regular connections
        self.getBDConnections(ret, allowSingleEnded=(len(excludeInstances)!=0))
        # annotate cross-interface binds in the language-agnostic view
        self.getBDCrossInterfaceBinds(ret)
        # pre-resolve per-channel Config override for SystemC channel
        # typing so template utilities do not perform cross-block lookups
        self.getBDChannelConfigOverrides(ret)
        # build final connection info
        self.getBDConnectionsFinal(ret)
        # Zero-instance exported / library leaf: no design connection sourced the
        # boundary ports, so synthesise them from the block's declared `ports:`
        # before port dedup / includes / interface-def collection run.
        if not ret['instances'] and self.data['blocks'][qualBlock].get('ports'):
            self.getBDDefinitionPorts(ret, qualBlock)
        # deduplicate the ports
        self.getBDPorts(ret)
        # module-local parameterized declaration set, derived and persisted by
        # projectCreate.deriveParameterizedDeclSets(). Resolved before getBDIncludes
        # so the include computation can pull in contexts transitively referenced
        # by the emitted decl set.
        self.getBDParameterizedDecls(ret)
        # figure out includes
        self.getBDIncludes(ret)
        # collect interface definitions for all interface types used in the block
        self.getBDInterfaceDefs(ret)
        self.getBDConfigInfo(ret)
        # Surface per-block register-bus data on the view; routers without
        # authored addressBlock rows get an equivalent view from ADDRESS_CONFIG.
        self.getBDAddressBlockView(ret)
        # Verilated SV wrapper design-unit names, single-sourced from the fileMap.
        self.getBDSvWrapperNames(ret)
        ret.pop('temp') # remove temp data

        return ret

    def getBDParameterizedDecls(self, ret):
        # Per-block module-local parameterized declaration set, derived and
        # persisted by projectCreate.deriveParameterizedDeclSets() into the
        # non-schema blockParameterizedDecls table. Queried directly per block
        # (the table is not loaded into prj.data) and joined to the types /
        # structures rows for the declaration bodies. Emission order is the
        # persisted orderIndex (types/sub-structures before the structures that
        # use them) for emitters that declare these module-local.
        qualBlock = ret['qualBlock']
        g.cur.execute("SELECT declKind, declKey, orderIndex FROM blockParameterizedDecls "
                      "WHERE blockKey = ? ORDER BY orderIndex", (qualBlock,))
        decls = list()
        for row in g.cur.fetchall():
            declKey = row['declKey']
            if row['declKind'] == 'type':
                body = self.data['types'][declKey]
            elif row['declKind'] == 'structure':
                body = self.data['structures'][declKey]
            else:  # constant: eval-derived parameterizable constant (module-local localparam)
                body = self.data['constants'][declKey]
            decls.append({'declKind': row['declKind'], 'declKey': declKey, 'body': body})
        ret['parameterizedDecls'] = decls

    def getBDSvWrapperNames(self, ret):
        # Verilated SV wrapper design-unit names, single-sourced from the fileMap
        # so a wrapper's emitted module name and its scaffolded filename share one
        # tail/ext: expandNewModulePath builds the filename as moduleFileStub +
        # fileMap 'name', and the module name is the SAME composition, never
        # re-spelled as a code literal and never derived back from the filename.
        # The body module name is the block stub + wrapper tail; the per-variant
        # tops name-qualify the same tail with persisted identity tokens (block,
        # variant, and — for a parent-owned foreign top — the declaring project,
        # sanitized the same way as the foreign-Config stub). The `.svh` include
        # name adds the body entry's ext.
        wrapTail = self.filemap['vlSvWrap']['name']
        bodyExt = self.filemap['vlSvWrapBody']['ext']['svh']
        foreignTail = self.filemap['vlSvWrapForeign']['name']
        scTail = self.filemap['vlScWrap']['name']
        scExt = self.filemap['vlScWrap']['ext']['hdr']
        blockName = ret['blockName']
        project = self.config.getConfig('PROJECTNAME')
        bodyModule = f'{blockName}{wrapTail}'
        # Keyed over the block's DECLARED variants: one standalone SV top exists
        # per declared variant (the .sv scaffold set), independent of which
        # variants an instance selects. vlRegistrar only LOOKS UP these dicts by
        # an instance-bound variant (a subset), so the superset keying leaves its
        # output unchanged while giving an inheriting-only leaf's trampoline the
        # top name it needs.
        variantTops = {v: f'{blockName}_{v}{wrapTail}' for v in ret['declaredVariants']}
        foreignVariantTops = {
            v: f'{sanitizeModuleToken(project)}_{blockName}_{v}{foreignTail}'
            for v in ret['declaredVariants']}
        ret['svWrapper'] = {
            'bodyModule': bodyModule,
            'bodyInclude': f'{bodyModule}.{bodyExt}',
            'variantTops': variantTops,
            'foreignVariantTops': foreignVariantTops,
            # SystemC verilated wrapper class + its include, from the vlScWrap
            # fileMap name/ext (the wrapper this block's VlRegistrar instantiates).
            'scWrapperModule': f'{blockName}{scTail}',
            'scWrapperInclude': f'{blockName}{scTail}.{scExt}',
            # Verilated DUT class + header for each SV top. Verilator's fixed
            # V<top>[.h] output convention applied to the view-sourced top name.
            'dutClass': f'V{bodyModule}',
            'dutHeader': f'V{bodyModule}.h',
            'variantDutClasses': {v: f'V{t}' for v, t in variantTops.items()},
            'variantDutHeaders': {v: f'V{t}.h' for v, t in variantTops.items()},
            'foreignVariantDutClasses': {v: f'V{t}' for v, t in foreignVariantTops.items()},
            'foreignVariantDutHeaders': {v: f'V{t}.h' for v, t in foreignVariantTops.items()},
        }

    def getBDConfigInfo(self, ret):
        # View assembly: read persisted truths and derive view-side fields.
        # Persisted by projectCreate.calcBlockConfigInfo().
        qualBlock = ret['blockInfo']['blockKey']
        block_row = self.data['blocks'][qualBlock]
        ret['isParameterizable'] = bool(block_row['isParameterizable'])
        ret['hasOwnParams'] = bool(block_row.get('params'))
        ret['defaultConfig'] = block_row['defaultConfig']
        ret['variantConfigs'] = self._buildVariantConfigDescriptors(
            qualBlock
        ) if ret['isParameterizable'] else []

    def getBlockConfigView(self, qualBlock):
        # Internal view-assembly helper: constant-time per-block bundle of
        # config-info fields used while building the language-agnostic
        # block and context views. Templates and template utilities do
        # NOT call this; they consume the equivalent fields surfaced on
        # the block / context views (`subBlockTypes`,
        # `subBlockInstances` entries, context view `variantConfigs` /
        # `blockParamSynthetic`).
        cached = self._blockConfigBundleCache.get(qualBlock)
        if cached is not None:
            return cached
        block_row = self.data['blocks'][qualBlock]
        defaultConfig = block_row['defaultConfig']
        is_parameterizable = bool(block_row['isParameterizable'])
        has_own_params = bool(block_row.get('params'))
        variant_configs = self._buildVariantConfigDescriptors(qualBlock) \
            if is_parameterizable else []
        bundle = {
            'isParameterizable': is_parameterizable,
            'hasOwnParams':      has_own_params,
            'defaultConfig':     defaultConfig,
            'variantConfigs':    variant_configs,
        }
        self._blockConfigBundleCache[qualBlock] = bundle
        return bundle

    def _resolveInstanceConfigFields(self, instanceData, bundle=None):
        # Neutral per-instance Config selection for a child instance: the
        # selected per-variant descriptor (or None), the child block's config
        # flags, and its persisted default Config name. This is the language-
        # neutral currency; the C++ struct-name / template-argument spelling is
        # done in the template layer (cpp_config_struct_name / cpp_config_arg)
        # from these components.
        #
        # Behavioral limitation: the descriptor is resolved from the child's own
        # variant binding (frozen here), not from the parent's `Config`
        # template parameter. A contained child's Config does NOT follow the
        # parent's Config, so a Config-strict interface link from a
        # multi-variant parent to a parameterized child is unsupported. Use a
        # single-variant child, a Config-agnostic interface, or a thunker bind.
        #
        # `descriptor` is None when the block is not parameterizable, or when it
        # binds no per-variant override (its emitted type collapses onto
        # `defaultConfig`).
        type_key = instanceData['instanceTypeKey']
        if bundle is None:
            bundle = self.getBlockConfigView(type_key)
        is_parameterizable = bundle['isParameterizable']
        has_own_params     = bundle['hasOwnParams']
        default_config     = bundle['defaultConfig']
        variant_configs    = bundle['variantConfigs']

        if instanceData['inheritContainerParam']:
            # Contained-block config inheritance: type this instance with the
            # CONTAINER block's active Config template symbol (`Config`) rather
            # than the child's own variant/default. Because a contained child
            # renders inside the container's templated class scope, C++ template
            # instantiation resolves the concrete struct (including the
            # transitive variant case) at the container's own site; no config
            # value is plumbed. The child keeps its own params/DefaultConfig for
            # standalone use. Preconditions are enforced at db-create in
            # calcBlockConfigInfo (validate_inherit_container_params). The
            # template layer spells `Config` off the contracted inheritContainer
            # flag.
            return {
                'isParameterizable':   is_parameterizable,
                'hasOwnParams':        has_own_params,
                'defaultConfig':       default_config,
                'descriptor':          None,
                'foreignConfigModule': None,
                'inheritContainer':    True,
            }

        descriptor = None
        foreign_config_module = None
        if is_parameterizable:
            variant = instanceData['variant']
            consumer_project = self.contextOwningProject[instanceData['_context']]
            desc = self._selectVariantDescriptor(variant_configs, variant, consumer_project)
            if desc is not None and desc['values']:
                descriptor = desc
                if desc['isForeign']:
                    # Neutral identity of the owner-qualified foreign Config
                    # module (`<project>.<child>.config`); the template spells the
                    # module name and emits the import.
                    foreign_config_module = {'project': desc['declaringProject'],
                                             'block': desc['block']}

        return {
            'isParameterizable': is_parameterizable,
            'hasOwnParams':      has_own_params,
            'defaultConfig':     default_config,
            'descriptor':        descriptor,
            'foreignConfigModule': foreign_config_module,
            'inheritContainer':  False,
        }

    def _selectVariantDescriptor(self, variant_configs, variant, consumerProject):
        # Pick the one descriptor a consumer in `consumerProject` binds for
        # `variant`. A variant declared BY the consumer's own project (foreign to
        # the child, but that consumer's immediate assembler) wins so the consumer
        # binds its own owner-qualified Config; otherwise the same-project (child-
        # owned, bare-name) descriptor is used. Returns None when the block does
        # not declare the variant.
        same_project = None
        for desc in variant_configs:
            if desc['variant'] != variant:
                continue
            if desc['isForeign']:
                if desc['declaringProject'] == consumerProject:
                    return desc
            else:
                same_project = desc
        return same_project

    def getRegistrarConfigView(self, childQualBlock, parentBlock):
        # Per-variant Config selection for a parent-owned registrar trampoline of
        # a reused child. The registrar registers each variant under the parent's
        # own factory projectName, so it must bind the Config the parent's own
        # instances bind: the consumer project is the parent's owning project.
        # Returns the per-variant neutral descriptor (or None -> defaultConfig),
        # the block defaultConfig, and the neutral (project, child) identities of
        # the foreign registrar-domain Config modules the trampoline TU must
        # import; the template spells each Config struct and module name.
        parentQual = self.getQualBlock(parentBlock)
        consumerProject = self.contextOwningProject[self.data['blocks'][parentQual]['_context']]
        descriptors = self._buildVariantConfigDescriptors(childQualBlock)
        defaultConfig = self.data['blocks'][childQualBlock]['defaultConfig']
        variantDescriptors = dict()
        foreignConfigModules = dict()
        for variant in sorted({desc['variant'] for desc in descriptors}):
            desc = self._selectVariantDescriptor(descriptors, variant, consumerProject)
            if desc is not None and desc['values']:
                variantDescriptors[variant] = desc
                if desc['isForeign']:
                    key = (desc['declaringProject'], desc['block'])
                    foreignConfigModules[key] = {'project': desc['declaringProject'],
                                                 'block': desc['block']}
            else:
                variantDescriptors[variant] = None
        return {'variantDescriptors': variantDescriptors,
                'defaultConfig': defaultConfig,
                'foreignConfigModules': [foreignConfigModules[k]
                                         for k in sorted(foreignConfigModules)]}

    def getForeignConfigData(self, childQualBlock, parentBlock):
        # Emission inputs for one owner-qualified foreign-Config header: the
        # foreign per-variant descriptors of a reused child that are declared by
        # the parent's owning project, plus the child's config-context member
        # constants and synthetic block params. Placed in the parent's
        # registrar domain; only the declaring assembler project emits it.
        parentQual = self.getQualBlock(parentBlock)
        ownerProject = self.contextOwningProject[self.data['blocks'][parentQual]['_context']]
        block_row = self.data['blocks'][childQualBlock]
        config_context = block_row['configContext']
        descriptors = [desc for desc in self._buildVariantConfigDescriptors(childQualBlock)
                       if desc['isForeign'] and desc['declaringProject'] == ownerProject
                       and desc['duplicateOf'] is None and desc['values']]
        params = [const_data for const_data in self.data['constants'].values()
                  if const_data['_context'] == config_context
                  and const_data['isParameterizable']]
        constant_names = {const_data['constant'] for const_data in params}
        synthetic = dict()
        for param_row in block_row.get('params', []) or []:
            name = param_row['param']
            if name in constant_names or name in synthetic:
                continue
            synthetic[name] = {'valueType': 'uint', 'maxValue': 0}
        return {'descriptors': descriptors, 'params': params,
                'blockParamSynthetic': synthetic}

    def _resolveConnectionConfigOverride(self, connVal):
        # Pre-resolve the per-connection Config override used by SystemC
        # channel emission. Returns the winning end's neutral Config selection
        # (or None); the channel template spells the struct name from it. The
        # choice prefers a leaf-parameterizable end (a block with its own
        # `params:`); on ties prefer dst; fall back to a non-leaf
        # parameterizable end. Cross-interface consumer ends are excluded
        # because the thunker resolves the consumer Config separately.
        ends = connVal['ends']
        cross_keys = {
            flagged['endKey']
            for flagged in (connVal.get('crossInterfaceEnds') or [])
        }
        leaf_choice = None
        transit_choice = None
        for end_key, end_data in ends.items():
            if end_key in cross_keys:
                continue
            inst_key = end_data.get('instanceKey')
            if not inst_key:
                continue
            inst_data = self.data['instances'][inst_key]
            configSelection = self._resolveInstanceConfigFields(inst_data)
            if not configSelection['isParameterizable']:
                continue
            if configSelection['hasOwnParams']:
                if leaf_choice is None or end_data['direction'] == 'dst':
                    leaf_choice = configSelection
            elif transit_choice is None:
                transit_choice = configSelection
        return leaf_choice or transit_choice

    def _buildVariantConfigDescriptors(self, qualBlock):
        # Per-variant Config descriptors for a parameterizable block. Each
        # declared variant maps to one Config struct. Anonymous variants
        # use <block>Config; named variants use <block><Variant>Config. Direct
        # overrides from parametersvariants are applied; eval re-resolution
        # under variant overrides is deferred.
        #
        # The variant set is the block's declared variant set: every variant
        # the block specifies in its `parameters:` section produces one Config
        # struct, whether or not the current project instantiates it. A block
        # owns all the variants it declares, so a variant referenced only by a
        # downstream project that reuses this block still finds its Config in
        # the block's own Config header. Bound-parameter overrides come from the
        # same declared source.
        #
        # Each descriptor carries NEUTRAL identity only; the C++ struct-name
        # string is spelled in the template layer (cpp_variant_config_name /
        # cpp_descriptor_config_name) from these components, never here in core:
        #   {'variant': str,              # this variant's own label (selection key)
        #    'declaringProject': str,     # project that declared the binding
        #    'block': str,                # block-name component of the struct name
        #    'isForeign': bool,           # foreign -> owner-qualified struct name
        #    'values': {constName: resolvedValue, ...},
        #    'emitVariant': str,          # variant whose struct this one emits as
        #    'useDefault': bool,          # emitted name is the block defaultConfig
        #    'duplicateOf': None | dict}  # non-None marks a non-canonical descriptor
        #
        # Every declared variant is canonical (duplicateOf=None, useDefault=False,
        # emitVariant=variant): the config structs map 1:1 onto the declared
        # variant set with no dedup fold, so each variant gets a distinctly
        # variant-named struct even when its values equal the block default. The
        # 'useDefault' / 'duplicateOf' / 'emitVariant' fields are retained on the
        # descriptor contract that consumers read; they no longer vary.
        block_row = self.data['blocks'][qualBlock]
        if not bool(block_row['isParameterizable']):
            return []
        block_name = block_row['block']
        # The Config struct's fields are the parameterizable constants of the
        # block's canonical config context (where its parameterizable
        # declarations live), not necessarily the block's own declaring
        # context. These coincide for IP-root blocks and differ for a block
        # declared in an including file (e.g. a testbench block bound to the IP).
        config_context = block_row['configContext']
        # Declared variant set. A parameterizable block that declares no
        # variants (parameterizable only transitively through its children)
        # produces no per-variant struct here; its context still emits the
        # shared default Config.
        #
        # Source the bindings from the LEAF parametersvariantsparams table,
        # whose combo key carries projectName, not the projectName-blind nested
        # `parameters` view (keyed block -> variant -> bare param): in a composed
        # build two projects binding the same (block, variant) param collapse
        # onto one entry in the nested view (last loaded wins), so only the
        # last project's descriptors would survive. Variant-parameter
        # completeness (validateVariantParameterCompleteness) guarantees every
        # declared variant binds every param, so the leaf rows recover the full
        # declared variant set that the early return keys off.
        block_binding_rows = [row for row in self.data['parametersvariantsparams'].values()
                              if row['blockKey'] == qualBlock]
        if not block_binding_rows:
            return []
        # A variant binding is FOREIGN when its declaring project differs from
        # the project that owns the block's config context (an assembler declared
        # a variant of a child owned by another project). Same-project and default
        # variants keep their bare name in the block's context config header;
        # foreign variants get an owner-qualified struct
        # `<declaringProject>_<block><Variant>Config` emitted into that assembler's
        # registrar-domain header. On a monolithic build every declaring project
        # is the root project, so nothing is foreign and output is byte-identical.
        owner_project = self.contextOwningProject[config_context]
        # Parameterizable constants in the block's primary context. These are
        # the Config struct's fields. Eval-derived constants appear here too;
        # they retain their default-resolved 'value' since variant-aware eval
        # re-resolution is deferred.
        param_constants = []
        for const_data in self.data['constants'].values():
            if const_data['_context'] != config_context:
                continue
            if not const_data.get('isParameterizable', False):
                continue
            param_constants.append(const_data)
        param_constant_names = {const_data['constant'] for const_data in param_constants}
        # Block params declared via `params:` but with no backing constant in
        # the context's parameterizable-constants table are folded into the
        # Config struct as plain fields. Their value source is the variant
        # override; there is no constant default. Variants that do not override
        # such a field receive 0 as a tripwire for any caller that reads
        # through the legacy default fallback.
        block_param_names = []
        for param_row in block_row.get('params', []) or []:
            name = param_row.get('param')
            if not name or name in param_constant_names:
                continue
            block_param_names.append(name)

        # Rows grouped by declaring project. Descriptor construction runs once
        # per declaring project so two projects declaring the same local variant
        # produce two distinct owner-qualified Configs. The same-project group is
        # processed first so its bare-named descriptors keep their emission
        # order; foreign groups follow in sorted project order.
        rows_by_project = OrderedDict()
        for row in block_binding_rows:
            rows_by_project.setdefault(row['projectName'], []).append(row)
        projects_ordered = ([owner_project] if owner_project in rows_by_project else []) + \
            sorted(p for p in rows_by_project if p != owner_project)

        descriptors = []
        for declaring_project in projects_ordered:
            is_foreign = declaring_project != owner_project
            # Bound-parameter overrides keyed by (variant, paramName), scoped to
            # this declaring project's rows. 'value' may be a literal or the name
            # of a referenced constant; resolve through self.data['constants'] so
            # emission gets a numeric literal.
            overrides = dict()
            declared = set()
            for row in rows_by_project[declaring_project]:
                declared.add(row['variant'])
                overrides[(row['variant'], row['param'])] = self._resolveBindingValueOpen(row)
            for variant in sorted(declared):
                values = dict()
                for const_data in param_constants:
                    const_name = const_data['constant']
                    if (variant, const_name) in overrides:
                        values[const_name] = overrides[(variant, const_name)]
                    else:
                        values[const_name] = const_data['value']
                for name in block_param_names:
                    values[name] = overrides.get((variant, name), 0)
                # Every declared variant gets its own canonical struct, 1:1 with
                # the declared variant set: no fold onto the shared context
                # default and no fold of byte-identical siblings. A variant whose
                # resolved values equal the block default therefore still emits a
                # distinctly variant-named struct (equal in content to
                # <context>DefaultConfig but a distinct C++ type).
                descriptors.append({
                    'variant':          variant,
                    'declaringProject': declaring_project,
                    'block':            block_name,
                    'isForeign':        is_foreign,
                    'values':           values,
                    'emitVariant':      variant,
                    'useDefault':       False,
                    'duplicateOf':      None,
                })
        return descriptors

    def _lookupInterfaceTypeKey(self, intf_type):
        """Simple lookup for interface type qualified key when not from interfaces table
        For types like 'memory' etc. that are constructed, not from interfaces table.
        """
        all_interface_defs = self.data.get('interface_defs', {})

        if intf_type in all_interface_defs:
            return intf_type
        for parent_key, mappings_dict in all_interface_defs.items():
            if mappings_dict['interface_type'] == intf_type:
                return parent_key
        return None

    def getBlockDataHier(self, qualBlock, trimRegLeafInstance=False, excludeInstances=set()):
        def recurse_block(block, trimRegLeafInstance, excludeInstances, visited=None):
            if visited is None:
                visited = set()
            if block in visited:
                return None  # Prevent infinite recursion on cyclic references
            visited.add(block)
            data = self.getBlockData(block, trimRegLeafInstance, excludeInstances)
            for subBlockKey in list(data['subBlocks'].keys()):
                subData = recurse_block(subBlockKey, trimRegLeafInstance, excludeInstances, visited)
                data['subBlocks'][subBlockKey] = subData
            return data
        return recurse_block(qualBlock, trimRegLeafInstance, excludeInstances)

    def getBDGetIntfStructs(self, ret, intfData={}, intfKey=''):
        if not intfData:
            intfData = self.data['interfaces'][intfKey]
        if intfData['structures']:
            for structInfo in intfData['structures']:
                ret['temp']['structs'][structInfo['structureKey']] = 0
        # Store qualified interface type key for direct lookup later
        # The parser already stores this as interfaceTypeKey after validation
        intf_type = intfData['interfaceType']
        intf_type_key = intfData.get('interfaceTypeKey', None)
        ret['interfaceTypes'][intf_type] = intf_type_key

    def getBDDeclaredPortInterfaceKey(self, instanceKey, portName):
        instData = self.data['instances'][instanceKey]
        blockData = self.data['blocks'][instData['instanceTypeKey']]
        return self._resolveDeclaredPortInterfaceKey(blockData, portName)

    def _resolveDeclaredPortInterfaceKey(self, blockData, portName):
        # Resolve a block's declared `ports:` row to a qualified interfaceKey
        # from the block's own declaring context. Shared by the instance-driven
        # cross-interface path (getBDDeclaredPortInterfaceKey) and the
        # zero-instance definition-driven port synthesis (getBDDefinitionPorts).
        declaredPort = (blockData.get('ports') or {}).get(portName)
        if not declaredPort:
            return ''
        interfaceName = declaredPort.get('interface')
        if not interfaceName:
            return ''
        preferredContext = declaredPort['_context'] or blockData['_context']
        interfaceKey = f"{interfaceName}/{preferredContext}" if preferredContext else ''
        if interfaceKey in self.data['interfaces']:
            return interfaceKey
        for key, row in self.data['interfaces'].items():
            if row.get('interface') == interfaceName:
                return key
        return ''

    def _resolveSvInstanceParams(self, childTypeKey, variant, parentParamNames):
        # Build the param-override list for a sub-block instance's SV #(...).
        # For each child block param, emit either the parent param SYMBOL (when
        # the parent module declares a same-named param, so the value flows down
        # from the parent's own instantiation) or the child's bound literal.
        # Returns an ordered list of {'param', 'spelling'}; empty when the child
        # block has no params.
        childBlock = self.data['blocks'][childTypeKey]
        if not childBlock['params']:
            return []
        # Variant bindings, keyed by the child's param name. A reg-handler
        # inherits the parent's params with no own variant bindings; in that
        # case there are no rows and every param must forward the parent symbol.
        variantValues = dict()
        childVariants = self.data['parameters'].get(childTypeKey, {}).get('variants', {})
        variantEntry = childVariants.get(variant)
        if variantEntry:
            for row in variantEntry['params'].values():
                variantValues[row['param']] = row['value']
        result = []
        for paramRow in childBlock['params']:
            paramName = paramRow['param']
            if paramName in parentParamNames:
                spelling = paramName
            else:
                spelling = str(variantValues[paramName])
            result.append({'param': paramName, 'spelling': spelling})
        return result

    def _resolveBindingValueOpen(self, row):
        # projectOpen-time resolution of a parametersvariants binding row to a
        # concrete value. 'value' is a literal for a literal binding, or the name
        # of the referenced constant for a symbol binding (valueKey is then the
        # qualified const key); symbol bindings resolve through the loaded
        # self.data['constants'] so a standalone consumer — e.g. a per-variant
        # HDL wrapper, which is a top module with no parent scope — emits a
        # numeric literal instead of an out-of-scope parent symbol. (Parse-time
        # validation uses projectCreate._resolveVariantBindingValue instead.)
        valueKey = row.get('valueKey', '') or ''
        if valueKey:
            constData = self.data['constants'].get(valueKey)
            if constData is not None:
                return constData.get('value', row['value'])
        return row['value']

    def getBDInstances(self, qualBlock, ret, trimRegLeafInstance, excludeInstances):
        qualBlockInstances = dict()
        containedInstances = dict()
        containerBlocks = dict()
        excluded = dict()
        hasExcluded = 0
        for inst_key, inst_data in self.data['instances'].items():
            if inst_data.get('containerKey') == qualBlock:
                if inst_data['instance'] in excludeInstances:
                    hasExcluded = 1
                    excluded[inst_key] = inst_data
                    continue
                containedInstances[inst_key] = inst_data
                if self.data['blocks'][inst_data['instanceTypeKey']]['isRegHandler']:
                    ret['regHandler'] = inst_key
            if inst_data.get('instanceTypeKey') == qualBlock:
                qualBlockInstances[inst_key] = inst_data
                containerBlocks[inst_data['containerKey']] = 0
                if inst_data['variant'] != '':
                    # Under the variant != '' guard, postParseChecks guarantees
                    # the (block, variant) row exists; index it directly so a
                    # missing entry surfaces as the projectCreate/postParse defect
                    # it would be rather than being masked by an empty binding set.
                    variantEntry = self.data['parameters'][qualBlock]['variants'][
                        inst_data['variant']]
                    binding_rows = variantEntry['params']
                    filtered_variants_data = {
                        k: {**v, 'resolvedValue': self._resolveBindingValueOpen(v)}
                        for k, v in binding_rows.items()}
                    ret['variants'][inst_data['variant']] = filtered_variants_data
        # Declared-variant view: every variant the block DECLARES (independent of
        # whether an instance selects it), each binding row enriched with its
        # resolved literal value — the same shape and enrichment as ret['variants']
        # above. A parameterized hasVl leaf reached only via inheritContainerParam
        # is never instance-bound to a variant, so its instantiated ret['variants']
        # is empty; the standalone per-variant SV wrapper trampoline (one .sv per
        # DECLARED variant, scaffolded from getQualBlockVariants) sources its
        # variant set and resolved binding values from here so it emits a correct
        # parameterized top rather than falling through to the non-parameterizable
        # render path.
        for variantEntry in self.data['parameters'].get(qualBlock, {}).get('variants', {}).values():
            ret['declaredVariants'][variantEntry['variant']] = {
                k: {**v, 'resolvedValue': self._resolveBindingValueOpen(v)}
                for k, v in variantEntry['params'].items()}
        # A block with zero instances is a valid render target for an exported /
        # library leaf that its owning project never instantiates (projectCreate
        # gates which blocks are allowed to be uninstantiated). The rest of this
        # function tolerates the empty case: subBlockInstances/containerBlocks
        # stay empty and the boundary ports are synthesised from the block
        # definition later (getBDDefinitionPorts).
        ret['instances'] = qualBlockInstances
        ret['enableRegConnections'] = True
        if trimRegLeafInstance and 'regHandler' in ret:
            # if the only contained instance is the regHandler then remove it
            if (len(containedInstances) + hasExcluded) == 1:
                containedInstances = dict()
                ret['enableRegConnections'] = False
        ret['subBlockInstances'] = containedInstances
        ret['containerBlocks'] = containerBlocks
        ret['blockName'] = self.data['blocks'][qualBlock]['block']
        # Emit-only project-qualified module name (blockName stays the lookup key).
        ret['blockModuleName'] = self.blockModuleName[qualBlock]
        # Sibling view: per child block type, surface the config facts
        # templates need for forward-declaring child Base classes
        # (`hasOwnParams`) and for resolving per-instance Config struct
        # names. Indexed by the child block's qualified key.
        ret['subBlockTypes'] = dict()
        # Parent-module param names in scope at this instantiation site. A child
        # instance param whose name matches a parent param forwards the parent
        # SYMBOL (.CHILD_PARAM(PARENT_PARAM)); the parent variant supplies the
        # value at the parent's own instantiation. Only params with no matching
        # parent param fall back to the child's bound literal value.
        parentParamNames = {p['param'] for p in (self.data['blocks'][qualBlock]['params'] or [])}
        # The assembling project's name scopes the generated createInstance
        # factory lookup for every child (see below).
        assemblerProject = self.config.getConfig('PROJECTNAME')
        for inst, instInfo in containedInstances.items():
            childTypeKey = instInfo['instanceTypeKey']
            ret['subBlocks'][childTypeKey] = instInfo['instanceType']
            # Emit-only project-qualified module name of the instantiated block
            # (instanceType stays the lookup key).
            instInfo['instanceTypeModuleName'] = self.blockModuleName[childTypeKey]
            instInfo['svInstanceParams'] = self._resolveSvInstanceParams(
                childTypeKey, instInfo['variant'], parentParamNames)
            if childTypeKey not in ret['subBlockTypes']:
                bundle = self.getBlockConfigView(childTypeKey)
                ret['subBlockTypes'][childTypeKey] = {
                    'instanceType':      instInfo['instanceType'],
                    'blockModuleName':   self.blockModuleName[childTypeKey],
                    'isParameterizable': bundle['isParameterizable'],
                    'hasOwnParams':      bundle['hasOwnParams'],
                    'defaultConfig':     bundle['defaultConfig'],
                }
            # Pre-resolve per-instance Config fields so templates do not
            # call back into project-level helpers during rendering.
            childBundle = self.getBlockConfigView(childTypeKey)
            configFields = self._resolveInstanceConfigFields(instInfo, bundle=childBundle)
            instInfo['instanceConfigSelection']          = configFields
            instInfo['instanceTypeIsParameterizable'] = configFields['isParameterizable']
            instInfo['instanceTypeHasOwnParams']   = configFields['hasOwnParams']
            instInfo['instanceTypeDefaultConfig']  = configFields['defaultConfig']
            # When the child binds a foreign (assembler-declared) variant, its
            # owner-qualified Config lives in a registrar-domain module the
            # container TU must import; aggregate the neutral (project, child)
            # identities for this block (deduped, one module per owning project).
            foreignConfigModule = configFields['foreignConfigModule']
            if foreignConfigModule:
                key = (foreignConfigModule['project'], foreignConfigModule['block'])
                ret['foreignConfigModules'][key] = foreignConfigModule
            # projectName the generated createInstance lookup must target for
            # this child. The factory key is (blockType, variant, projectName).
            #  * parameterizable child -> assembler: a parent-owned registrar
            #    trampoline re-registers it under the assembler, so the lookup
            #    must match the assembler.
            #  * plain (non-parameterizable) child owned by another project ->
            #    owner: it self-registers only under its owning project and gets
            #    no trampoline, so the assembler must target the owner. This
            #    preserves the projectName disambiguation (no re-registration
            #    under the assembler, which could collide).
            #  * plain same-project child -> assembler (== owner, unchanged).
            childOwner = self.contextOwningProject[self.data['blocks'][childTypeKey]['_context']]
            if (not configFields['isParameterizable']) and childOwner != assemblerProject:
                instInfo['createInstanceProjectName'] = childOwner
            else:
                instInfo['createInstanceProjectName'] = assemblerProject
        if hasExcluded == 0 and len(excludeInstances) > 0:
            printError(f"--excludeInst={excludeInstances} did not find any of the instances to exclude in block {qualBlock}")
            exit(warningAndErrorReport())
        # Pre-resolve per-instance Config fields for the excluded DUT
        # instance(s) too. The tbExternal template inherits
        # `<DUT>Inverted<Config>`, whose template argument is the DUT's
        # per-instance Config, not the (possibly param-less) testbench-top
        # block's. Mirror the contained-instance resolution above.
        for inst, instInfo in excluded.items():
            childBundle = self.getBlockConfigView(instInfo['instanceTypeKey'])
            configFields = self._resolveInstanceConfigFields(instInfo, bundle=childBundle)
            instInfo['instanceConfigSelection']             = configFields
            instInfo['instanceTypeIsParameterizable'] = configFields['isParameterizable']
            instInfo['instanceTypeHasOwnParams']      = configFields['hasOwnParams']
            instInfo['instanceTypeDefaultConfig']     = configFields['defaultConfig']
            # Emit-only project-qualified module name of the excluded DUT block
            # (instanceType stays the lookup key). The tbExternal template's
            # `<DUT>.base` import must match the DUT's own qualified export.
            instInfo['instanceTypeModuleName'] = self.blockModuleName[instInfo['instanceTypeKey']]
        ret['excludedInstances'] = excluded

    def getBDRegistersMemories(self, qualBlock, ret):
        # figure out which memories are either in this block or accessible through registers
        block = qualBlock
        isRegHandler = ret['blockInfo']['isRegHandler']
        if isRegHandler:
            # for register handler blocks we want the registers from the parent block
            block = ret['instances'][next(iter(ret['instances']))]['containerKey'] # note there should be a 1:1 relationship for reg handler
            decodeBlock = block
            # figure out an instance of the parent block
            # we will use this to get the address group for the address decode
            for k, v in self.data['instances'].items():
                if v['instanceTypeKey'] == decodeBlock:
                    addressGroup = v['addressGroup']
                    break
        else:
            decodeBlock = qualBlock
            if ret['instances']:
                instanceInfo = ret['instances'][next(iter(ret['instances']))] # we only need one instance for the info as all instances must have similar config.. TODO add more checks
                addressGroup = instanceInfo['addressGroup']
            else:
                # Zero-instance exported leaf: there is no instance to sample an
                # addressGroup from. It is only consumed below when hasDecoder,
                # and such a leaf has no FW-accessible registers/memories.
                addressGroup = None

        for designObject in ['registers', 'memories']:
            data = dict()
            for obj, objInfo in self.data[designObject].items():
                if objInfo['blockKey'] == block:
                    data[obj] = dict(objInfo)
                    ret['temp']['structs'][objInfo['structureKey']] = 0
                    # handle any object specific special cases
                    if (designObject == 'memories'):
                        ret['temp']['consts'][objInfo['wordLinesKey']] = 0
                        if objInfo['regAccess']:
                            ret['addressDecode']['hasDecoder'] = True # we have memories that need FW access
                        else:
                            if isRegHandler:
                                # for a regHandler we only want memories that have regAccess
                                data.pop(obj)

                    else:  # registers
                        data[obj]['bytes'] = (self.data['structures'][objInfo['structureKey']]['width'] + 7) >> 3 # round up to whole byte
                        # Surface worst-case bytes alongside nominal bytes for parameterized structures.
                        _struct = self.data['structures'][objInfo['structureKey']]
                        if _struct.get('isParameterizable') and _struct.get('maxBitwidth'):
                            data[obj]['maxBytes'] = (_struct['maxBitwidth'] + 7) >> 3
                        else:
                            data[obj]['maxBytes'] = data[obj]['bytes']
                        # Check if this is a memory register
                        if objInfo.get('regType') == 'memory':
                            if objInfo.get('wordLinesKey'):
                                ret['temp']['consts'][objInfo['wordLinesKey']] = 0
                            if objInfo.get('addressStructKey'):
                                ret['temp']['structs'][objInfo['addressStructKey']] = 0
                        ret['addressDecode']['hasDecoder'] = True #register = AddressDecoder
            ret[designObject] = data

        if ret['addressDecode']['hasDecoder']:
            ret['addressDecode']['addressBits'] = (self.data['blocks'][decodeBlock]['maxAddress']).bit_length()
            ret['addressDecode']['addressGroup'] = addressGroup

    def getBDAddressDecode(self, ret):
        # Is this block an apbDecode router that performs APB bus routing?
        # The router's own block row carries `addressBlock:`. The router
        # instance is resolved by post-parse container-locality (see
        # postParseRegisterPorts.py) and is the single instance of this
        # block type, so any element of ret['instances'] identifies it.
        isApbRouter = False
        qualBlock = ret['qualBlock']
        blockRow = self.data['blocks'][qualBlock]
        addressBlock = blockRow.get('addressBlock')
        if addressBlock:
            qualDecoder = next(iter(ret['instances']))
            instanceWithRegApb = self.config.getConfig("INSTANCES_WITH_REGAPB", failOk=True)
            if instanceWithRegApb is None:
                printError('No instances with register interface found in db: missing or invalid register post processing script')
                exit(warningAndErrorReport())
            isApbRouter = True
            ret['addressDecode']['addressGroupData'] = dict(addressBlock)
            ret['addressDecode']['addressGroup'] = addressBlock.get('addressGroup')
            ret['addressDecode']['containerBlock'] = self.instanceContainer[qualDecoder]
            ret['addressDecode']['instanceWithRegApb'] = instanceWithRegApb
        ret['addressDecode']['isApbRouter'] = isApbRouter

    # memory connections
    def getBDMemoryConnections(self, ret):
        # go through memory connections and collect if either src or dest
        qualBlock = ret['qualBlock']
        qualBlockInstances = ret['instances']
        isRegHandler = ret['blockInfo']['isRegHandler']
        containedInstances = ret['subBlockInstances']
        for memConn, val in self.data['memoryConnections'].items():
            if val['blockKey'] == qualBlock and val['instanceKey'] in containedInstances:
                # the connection is to a memory inside the target block so we will need a channel and bindings
                ret['memoryConnections'][memConn] = dict(val)
                ret['memoryConnections'][memConn]['interfaceName'] = val['memory']+'_'+val['port']
                if (val['instance'] != ''):
                    # we are connecting to an instance so lets add the instance type for the template
                    ret['memoryConnections'][memConn]['instanceTypeKey'] = self.data['instances'][val['instanceKey']]['instanceType']
                else:
                    # for local mode where we are not connecting to an instance ensure we dont get a key missing error
                    ret['memoryConnections'][memConn]['instanceTypeKey'] = ''
                ret['temp']['structs'][self.data['memories'][val['memoryBlockKey']]['structureKey']] = 0
                ret['temp']['consts'][self.data['memories'][val['memoryBlockKey']]['wordLinesKey']] = 0
            if val['instanceKey'] in qualBlockInstances:
                # we are the instance getting a memory connection so this means we have a port
                memInfo = self.data['memories'][val['memoryBlockKey']]
                ret['memoryPorts'][memConn] = dict(memInfo, **val) # merge the two dicts
                ret['memoryPorts'][memConn]['interfaceName'] = val['memory']
                ret['memoryPorts'][memConn]['direction'] = 'src'
                ret['memoryPorts'][memConn]['interfaceType'] = 'memory'
                if (val['instance'] != ''):
                    ret['memoryPorts'][memConn]['instanceTypeKey'] = self.data['instances'][val['instanceKey']]['instanceType']
                else:
                    ret['memoryPorts'][memConn]['instanceTypeKey'] = ''
                ret['temp']['structs'][self.data['memories'][val['memoryBlockKey']]['structureKey']] = 0
                ret['temp']['consts'][self.data['memories'][val['memoryBlockKey']]['wordLinesKey']] = 0

        for mem, memInfo in ret['memories'].items():
            # we also need to create a port for any memory that has regAccess as the register block will need to connect to it
            if memInfo['regAccess']:
                interfaceName = memInfo['memory']+ '_reg'
                ret['temp']['structs'][memInfo['structureKey']] = 0
                if isRegHandler:
                    ret['memoryPorts'][interfaceName] = dict(memInfo)
                    ret['memoryPorts'][interfaceName]['interfaceName'] = interfaceName
                    ret['memoryPorts'][interfaceName]['direction'] = 'src'
                    ret['memoryPorts'][interfaceName]['interfaceType'] = 'memory'
                else:
                    if ret['enableRegConnections']:
                        # we also need to create a memory connection for the register block to connect to the memory
                        ret['memoryConnections'][interfaceName] = dict(memInfo)
                        ret['memoryConnections'][interfaceName]['interfaceName'] = interfaceName
                        ret['memoryConnections'][interfaceName]['instanceKey'] = ret['regHandler']
                        ret['memoryConnections'][interfaceName]['instance'] = ret['subBlockInstances'][ret['regHandler']]['instance']
                        ret['memoryConnections'][interfaceName]['instanceTypeKey'] = ret['subBlockInstances'][ret['regHandler']]['instanceType']
                        ret['memoryConnections'][interfaceName]['direction'] = 'src'
        if isRegHandler:
            ret['memoriesParent'] = ret['memories']
            ret['memories'] = dict()

        # Add memory interface type if we have any memory ports or connections
        if ret['memoryPorts'] or ret['memoryConnections']:
            ret['interfaceTypes']['memory'] = self._lookupInterfaceTypeKey('memory')

    # register connections
    regMapReg   = { 'rw': 'src', 'ro': 'dst', 'ext': 'src', 'memory': 'src' } # mapping of the register type to the registerBlock port direction
    regMapBlock = { 'rw': 'dst', 'ro': 'src', 'ext': 'dst', 'memory': 'dst' } # mapping of the register type to the block port direction
    def getBDRegisterConnections(self, ret):
        block = ret['qualBlock']
        qualBlockInstances = ret['instances']
        containedInstances = ret['subBlockInstances']
        isRegHandler = ret['blockInfo']['isRegHandler']
        regHandlerKey = ret.get('regHandler', None)
        regHandler = ''
        connected_regs = dict()
        if regHandlerKey:
            regHandler = self.data['instances'][regHandlerKey]['instance']
        if isRegHandler:
            # for a register handler the registerConnections are in the parent
            block = ret['instances'][next(iter(ret['instances']))]['containerKey']
        for regConn, val in self.data['registerConnections'].items():
            if val['blockKey'] == block and val['instanceKey'] in containedInstances:
                reg_name = val['register']
                connected_regs[reg_name] = 0
                regType =  ret['registers'][val['registerBlockKey']]['regType']
                ifType = 'reg_' + regType
                regInfo = ret['registers'][val['registerBlockKey']]
                ret['temp']['structs'][regInfo['structureKey']] = 0
                # Track register-based interface types for later processing
                ret['temp']['registerInterfaceTypes'][ifType] = 0
                if isRegHandler:
                    ret['registerPorts'][regConn] = dict(regInfo, **val)
                    ret['registerPorts'][regConn]['direction'] = self.regMapReg.get(ret['registers'][val['registerBlockKey']]['regType'], None)
                    ret['registerPorts'][regConn]['interfaceType'] = ifType
                else:
                    connKey = regInfo['register']
                    if connKey not in ret['registerConnections']:
                        output = dict(regInfo, **val)
                        inst = val['instance']
                        output['ends'] = dict()
                        output['ends'][inst] =          {'instance': inst,       'portName': reg_name, 'direction': self.regMapBlock[regType]}
                        output['ends'][regHandlerKey] = {'instance': regHandler, 'portName': reg_name, 'direction': self.regMapReg[regType]}
                        output['interfaceType'] = ifType
                        output['interfaceName'] = reg_name
                        ret['registerConnections'][connKey] = output
                    else:
                        inst = val['instance']
                        ret['registerConnections'][connKey]['ends'][inst] = {'instance': inst, 'portName': reg_name, 'direction': self.regMapBlock[regType]}
            if val['instanceKey'] in qualBlockInstances:
                portName = val['register']
                connected_regs[portName] = 0
                regInfo = self.data['registers'][val['registerBlockKey']]
                ret['registerPorts'][portName] = dict(regInfo, **val) # merge the two dicts
                regType = regInfo['regType']
                ret['registerPorts'][portName]['direction'] = self.regMapBlock.get(regType, None)
                ifType = 'reg_' + regType
                ret['registerPorts'][portName]['interfaceType'] = ifType
                # Track register-based interface types for later processing
                ret['temp']['registerInterfaceTypes'][ifType] = 0
                ret['temp']['structs'][regInfo['structureKey']] = 0
        # handle implied register connections. These interfaces connect any unconnected registers to the block
        implied_reg = dict()
        for reg_key, reg_data in ret['registers'].items():
            reg = reg_data['register']
            regType = reg_data['regType']

            # Extra memory registers handling
            if regType == 'memory':
                # Track structs and consts for memory registers
                ret['temp']['structs'][reg_data['structureKey']] = 0
                if reg_data.get('addressStructKey'):
                    ret['temp']['structs'][reg_data['addressStructKey']] = 0
                if reg_data.get('wordLinesKey'):
                    ret['temp']['consts'][reg_data['wordLinesKey']] = 0

            # Handle regular registers
            if reg not in connected_regs:
                ifType = 'reg_' + regType
                implied_reg[reg] = dict(reg_data)
                implied_reg[reg]['interfaceType'] = ifType
                if isRegHandler:
                    implied_reg[reg]['direction'] = self.regMapReg[regType]
                else:
                    implied_reg[reg]['interfaceName'] = reg
                    implied_reg[reg]['ends'] = dict()
                    # The implied register is owned by qualBlock itself (these
                    # rows are filtered by blockKey == qualBlock in
                    # getBDRegistersMemories), routed to the in-container reg
                    # handler. The non-handler end is qualBlock's own register
                    # boundary, NOT a contained child. `qualBlockInstances` is
                    # every instance of this block type project-wide; picking
                    # next(iter(...)) there would name an out-of-scope instance
                    # (a sibling-container reuse, e.g. uBridgeIp0) and leak it
                    # into this module. The boundary end is keyed and named by
                    # the block itself so it stays in-scope and never
                    # impersonates a sibling instance; the in-scope handler
                    # (regHandlerKey, containerKey == qualBlock) is the other
                    # end.
                    boundaryKey = ret['qualBlock']
                    boundaryName = ret['blockName']
                    implied_reg[reg]['ends'][boundaryKey] = {'instance': boundaryName, 'portName': reg, 'direction': self.regMapBlock[regType]}
                    implied_reg[reg]['ends'][regHandlerKey] = {'instance': regHandler, 'portName': reg, 'direction': self.regMapReg[regType]}
                # Track register-based interface types for later processing
                ret['temp']['registerInterfaceTypes'][ifType] = 0
                ret['temp']['structs'][reg_data['structureKey']] = 0
        if isRegHandler:
            ret['registerPorts'].update(implied_reg)
        else:
            ret['registerConnections'].update(implied_reg)
    # connection maps
    def getBDConnectionMaps(self, ret):
        qualBlock = ret['qualBlock']
        qualBlockInstances = ret['instances']
        containedInstances = ret['subBlockInstances']
        for connMapKey, connMap in self.data['connectionMaps'].items():
            # note we check that a valid qualBlock connects to a contained instance in case it was pruned (regBlock)
            if connMap['blockKey'] == qualBlock and connMap['instanceKey'] in containedInstances:
                ret['connectionMaps'][connMapKey] = dict(connMap)
                ret['connectionMaps'][connMapKey]['interfaceName'] = connMap['portName']
                ret['connectionMaps'][connMapKey]['parentPortName'] = connMap['portName']
                self.getBDGetIntfStructs(ret, intfKey=connMap['interfaceKey'])
            if connMap['instanceKey'] in qualBlockInstances:
                # use portName as the key to deduplicate the port definitions
                portName = connMap['instancePortName']
                portView = dict(connMap)
                declaredInterfaceKey = self.getBDDeclaredPortInterfaceKey(connMap['instanceKey'], portName)
                if declaredInterfaceKey:
                    # The child side of a cross-interface connectionMap is
                    # typed by the child's declared port interface. Keeping
                    # the parent interface here leaks parent-only contexts
                    # into reusable leaf block headers.
                    portView['interfaceKey'] = declaredInterfaceKey
                    portView['interface'] = self.data['interfaces'][declaredInterfaceKey]['interface']
                ret['connectionMapPorts'][portName] = portView
                self.getBDGetIntfStructs(ret, intfKey=portView['interfaceKey'])

    # regular connections
    def getBDConnections(self, ret, allowSingleEnded=False):
        # iterate through all the connections for the instances of interest
        ports = dict()
        qualBlockInstances = ret['instances']
        containedInstances = ret['subBlockInstances']
        excludeInstances = ret['excludedInstances']
        connections = dict()
        prunedConnections = dict()
        for conn, connVal in self.data['connections'].items():
            connectionCount = 0
            isPort = False
            tempPorts = dict()
            pop_ends = []
            for end, endVal in connVal['ends'].items():
                if endVal['instanceKey'] in containedInstances:
                    connections[conn] = dict(connVal)
                    connectionCount += 1
                if endVal['instanceKey'] in qualBlockInstances:
                    isPort = True
                    tempPorts[end] = endVal
                if endVal['instanceKey'] in excludeInstances:
                    pop_ends.append(end)
                    # Capture the excluded (DUT) end's Config selection before
                    # the end is popped. A pruned cross-interface boundary needs
                    # it as the up/parent-side Config: once the DUT end is gone
                    # the surviving-end classifier cannot recover the DUT's
                    # typing, so the boundary thunker payload would emit an
                    # unresolved template parameter.
                    prunedConnections[conn] = excludeInstances[endVal['instanceKey']]['instanceConfigSelection']
            # filter out any excluded instances after looping
            for end in pop_ends:
                connVal['ends'].pop(end)
            if isPort:
                # shallow copy
                ports[conn] = dict(connVal)
                # replace ends with our pruned version
                ports[conn]['ends'] = tempPorts
            if connectionCount == 1 and not allowSingleEnded:
                printError(f"Connection {conn} is only connected to one contained instance in block {ret['qualBlock']}. Connections must be between two contained instances")
                exit(warningAndErrorReport())
            if connectionCount > 0 and isPort:
                printError(f"Connection {conn} is connected to both a contained instance and the parent instance in block {ret['qualBlock']}. Connections must be between two contained instances")
                exit(warningAndErrorReport())
            if connectionCount > 1 or isPort:
                # Get interfaceTypeKey from the interfaces table (already has qualified key)
                intfInfo = self.data['interfaces'][connVal['interfaceKey']]
                intf_type = intfInfo['interfaceType']
                ret['interfaceTypes'][intf_type] = intfInfo.get('interfaceTypeKey', None)
        for conn, connVal in connections.items():
            # create jinja friendly names
            _, connVal['interfaceName'] = getKeyPriority(connVal, ['interfaceName', 'srcport', 'name', 'interface'])
            intfInfo = self.data['interfaces'][connVal['interfaceKey']]
            self.getBDGetIntfStructs(ret, intfData=intfInfo)
            connVal['interfaceType'] = intfInfo['interfaceType']
            for end, endVal in connVal['ends'].items():
                endVal['name'] = endVal['portName']
        # move all the pruned connections to a separate dict, carrying the
        # excluded (DUT) end's Config selection for boundary-thunker typing
        for conn in prunedConnections:
            connMoved = connections.pop(conn)
            connMoved['excludedEndConfig'] = prunedConnections[conn]
            ret['prunedConnections'][conn] = connMoved

        ret['connections'] = connections
        ret['connectionPorts'] = ports

    def getBDDefinitionPorts(self, ret, qualBlock):
        # Zero-instance render path. A hasMdl block that its owning project never
        # instantiates (an exported / library leaf) has no design connection to
        # source its boundary ports from, so getBDConnections leaves
        # ret['connectionPorts'] empty and getBDPorts would emit a portless
        # module. Synthesise, from each declared `ports:` row, the
        # connection-shaped entry getBDConnections produces for an
        # instance-driven port (one 'parent' end), so the unchanged getBDPorts
        # emits the declared boundary. Called only when ret['instances'] is
        # empty, so instantiated blocks are unaffected.
        # SCOPE: connection-interface `ports:` rows only. registerPorts: and
        # memory ports are not synthesised here — those render from the router /
        # register-handler connectivity the post-parse pass builds around a real
        # instance, which does not exist in the zero-instance case.
        blockRow = self.data['blocks'][qualBlock]
        for portName, portRow in blockRow['ports'].items():
            interfaceKey = self._resolveDeclaredPortInterfaceKey(blockRow, portName)
            if not interfaceKey:
                printError(f"Unable to resolve interface '{portRow['interface']}' for declared "
                           f"port {portName} of uninstantiated block {qualBlock}")
                exit(warningAndErrorReport())
            intfInfo = self.data['interfaces'][interfaceKey]
            direction = portRow['direction']
            end = {'portName': portName, 'direction': direction, 'name': portName,
                   'instanceKey': 'parent', 'isPort': True}
            ret['connectionPorts'][portName] = {
                'interfaceKey': interfaceKey,
                'interface': intfInfo['interface'],
                'interfaceName': intfInfo['interface'],
                'interfaceType': intfInfo['interfaceType'],
                'direction': direction,
                'ends': {portName: end},
            }
            self.getBDGetIntfStructs(ret, intfKey=interfaceKey)

    def getBDCrossInterfaceBinds(self, ret):
        # projectCreate.validatePorts() performs the expensive structural
        # compatibility checks. This view pass only records already-valid
        # semantic facts so language templates do not need to re-walk raw
        # project tables to discover cross-interface binds.
        def structureMap(interfaceRow):
            structs = dict()
            structures = interfaceRow.get('structures', []) or []
            if isinstance(structures, dict):
                structures = structures.values()
            for item in structures:
                structureType = item.get('structureType')
                if structureType is None:
                    continue
                structs[structureType] = {
                    'structure': item.get('structure', ''),
                    'structureKey': item.get('structureKey', ''),
                }
            return structs

        def blockHasOwnParams(typeKey):
            return bool(self.data['blocks'][typeKey].get('params'))

        def resolveInterfaceKey(interfaceName, preferredContext):
            if not interfaceName:
                return ''
            interfaceKey = f"{interfaceName}/{preferredContext}" if preferredContext else ''
            if interfaceKey in self.data['interfaces']:
                return interfaceKey
            for key, row in self.data['interfaces'].items():
                if row.get('interface') == interfaceName:
                    return key
            return ''

        def resolveInstanceConfig(instanceData):
            typeKey = instanceData['instanceTypeKey']
            blockRow = self.data['blocks'][typeKey]
            if not blockRow['isParameterizable']:
                return None
            # Foreign-aware selection (owner-qualified name for the consumer's
            # own assembler-declared variant); the thunker payload must spell the
            # exact same Config type the child instance is cast to. Neutral
            # selection only; the template spells the struct name.
            return self._resolveInstanceConfigFields(instanceData)

        def resolveConnectionConfig(connVal, excludeEndKey=''):
            # When annotating a cross-interface bind, the "parent" payload
            # of the thunker is the producer's (up-side) typing. Skip the
            # consumer end being annotated so the surviving leaf end (the
            # producer) governs the parent-side Config. With no exclude
            # key supplied the historical dst-prefer behaviour applies.
            leafChoice = None
            transitChoice = None
            for endKey, endData in (connVal.get('ends', {}) or {}).items():
                if excludeEndKey and endKey == excludeEndKey:
                    continue
                instKey = endData.get('instanceKey')
                if not instKey:
                    continue
                instData = self.data['instances'].get(instKey)
                if not instData:
                    continue
                typeKey = instData['instanceTypeKey']
                configSelection = resolveInstanceConfig(instData)
                if not configSelection:
                    continue
                if blockHasOwnParams(typeKey):
                    # Match channel typing: prefer dst when both ends are
                    # leaf-parameterizable and therefore disagree.
                    if leafChoice is None or endData.get('direction') == 'dst':
                        leafChoice = configSelection
                elif transitChoice is None:
                    transitChoice = configSelection
            return leafChoice or transitChoice

        def resolveInterfaceDef(interfaceRow):
            interfaceType = interfaceRow.get('interfaceType', '')
            context = interfaceRow.get('_context', '')
            if not interfaceType:
                return None
            qualifiedKey = f"{interfaceType}/{context}" if context else ''
            if qualifiedKey in self.data.get('interface_defs', {}):
                return self.data['interface_defs'][qualifiedKey]
            for intfDef in self.data.get('interface_defs', {}).values():
                if intfDef.get('interface_type') == interfaceType:
                    return intfDef
            return None

        def buildThunkerView(parentInterface, childInterface, parentConfigSelection, childConfigSelection):
            parentStructures = structureMap(parentInterface)
            childStructures = structureMap(childInterface)
            interfaceType = parentInterface.get('interfaceType', '')
            interfaceDef = resolveInterfaceDef(parentInterface)
            if not interfaceDef:
                printError("Unable to build cross-interface thunker view: "
                           f"interface_defs entry for '{interfaceType}' was not found.")
                exit(warningAndErrorReport())
            scChannel = interfaceDef.get('sc_channel') or {}
            channelType = scChannel.get('type') or interfaceType
            parameters = interfaceDef.get('parameters') or {}
            structureTypes = [
                param for param, paramInfo in parameters.items()
                if paramInfo.get('datatype') == 'struct'
            ]

            if not structureTypes:
                return None

            payloads = []
            for side, structures, configSelection in [
                ('parent', parentStructures, parentConfigSelection),
                ('child', childStructures, childConfigSelection),
            ]:
                for structureType in structureTypes:
                    structure = structures.get(structureType)
                    if not structure:
                        printError(
                            "Unable to build cross-interface thunker view: "
                            f"{side} interface '{structureType}' payload is missing.")
                        exit(warningAndErrorReport())
                    payloads.append({
                        'side': side,
                        'structureType': structureType,
                        'structure': structure['structure'],
                        'structureKey': structure['structureKey'],
                        'configSelection': configSelection,
                    })

            return {
                'protocol': interfaceType,
                'channelType': channelType,
                'payloads': payloads,
            }

        addressBusInterfaceTypes = {
            row.get('interface_type')
            for row in self.data.get('interface_defs', {}).values()
            if isinstance(row, dict) and row.get('addressBus')
        }

        def registerBusChildBind(childBlockKey, portName):
            # A routed leaf's register-bus ingress is not declared in
            # `ports:`. Its child interface is read from the leaf-to-handler
            # connectionMap the post-parse pass emitted (block: this leaf,
            # port: the leaf-side register-bus port), so projectOpen reads the
            # resolved design rather than the leaf's parse-time `registerPorts:`
            # construct. The addressBus filter keeps a datapath connectionMap on
            # the same leaf from being mistaken for the register bus.
            for cm in self.data['connectionMaps'].values():
                if cm.get('blockKey') != childBlockKey or cm.get('port') != portName:
                    continue
                interfaceKey = cm.get('interfaceKey')
                if not interfaceKey:
                    continue
                ifaceRow = self.data['interfaces'].get(interfaceKey)
                if ifaceRow and ifaceRow.get('interfaceType') in addressBusInterfaceTypes:
                    return interfaceKey, ifaceRow.get('interface')
            return None

        def annotate(connVal, endKey, instanceKey, portName, instanceName, inferredDirection,
                     parentConfigOverride=None):
            if connVal['_context'] == '_global':
                return None
            parentInterfaceKey = connVal.get('interfaceKey') or ''
            parentInterface = self.data['interfaces'].get(parentInterfaceKey)
            if not parentInterface:
                return None
            parentInterfaceName = parentInterface.get('interface')
            if not parentInterfaceName:
                return None
            instanceData = self.data['instances'].get(instanceKey)
            if not instanceData:
                return None
            childBlockKey = instanceData['instanceTypeKey']
            childBlock = self.data['blocks'][childBlockKey]
            declaredPort = (childBlock.get('ports') or {}).get(portName)
            if declaredPort:
                childInterfaceName = declaredPort.get('interface')
                declaredDirection = declaredPort.get('direction')
                if not childInterfaceName or childInterfaceName == parentInterfaceName:
                    return None
                childInterfaceKey = resolveInterfaceKey(
                    childInterfaceName,
                    declaredPort['_context'] or childBlock['_context'])
                if not childInterfaceKey:
                    printError(
                        f"Block {ret['qualBlock']} binds {instanceName}.{portName} "
                        f"to interface '{childInterfaceName}', but the interface "
                        f"could not be resolved while building the block view.")
                    exit(warningAndErrorReport())
            else:
                registerBind = registerBusChildBind(childBlockKey, portName)
                if not registerBind:
                    return None
                childInterfaceKey, childInterfaceName = registerBind
                declaredDirection = None
                if childInterfaceName == parentInterfaceName:
                    return None
            childInterface = self.data['interfaces'][childInterfaceKey]
            childConfigSelection = resolveInstanceConfig(instanceData)
            # For a pruned tb/DUT boundary the up-side (parent) end is the
            # excluded DUT instance, no longer present in connVal['ends']; its
            # Config is supplied explicitly. Otherwise the parent Config is the
            # connection's surviving up-side end.
            if parentConfigOverride is not None:
                parentConfigSelection = parentConfigOverride
            else:
                parentConfigSelection = resolveConnectionConfig(connVal, excludeEndKey=endKey)
            thunkerView = buildThunkerView(
                parentInterface, childInterface, parentConfigSelection, childConfigSelection)
            if not thunkerView:
                return None
            # The thunker member types reference the child interface's
            # structures, so the surrounding container must include the child
            # interface's defining context. getBDConnections only gathers
            # structures from the connection's parent interface; absent this
            # annotation, generated containers carrying cross-interface thunker
            # members would miss the <childContext>Config.h include.
            self.getBDGetIntfStructs(ret, intfData=childInterface)
            return {
                'endKey': endKey,
                'instanceKey': instanceKey,
                'instance': instanceName,
                'childBlockKey': childBlockKey,
                'childBlock': childBlock.get('block', ''),
                'portName': portName,
                'direction': declaredDirection or inferredDirection or 'dst',
                'parentInterfaceKey': parentInterfaceKey,
                'parentInterface': parentInterfaceName,
                'parentInterfaceType': parentInterface.get('interfaceType', ''),
                'parentStructures': structureMap(parentInterface),
                'childInterfaceKey': childInterfaceKey,
                'childInterface': childInterfaceName,
                'childInterfaceType': childInterface.get('interfaceType', ''),
                'childStructures': structureMap(childInterface),
                'childVariant': instanceData.get('variant', '') or '',
                'thunker': thunkerView,
            }

        for connVal in ret['connections'].values():
            crossInterfaceEnds = []
            for endKey, endVal in connVal.get('ends', {}).items():
                bind = annotate(
                    connVal,
                    endKey,
                    endVal.get('instanceKey') or '',
                    endVal.get('portName') or '',
                    endVal.get('instance') or '',
                    endVal.get('direction') or '',
                )
                if bind:
                    endVal['crossInterface'] = bind
                    crossInterfaceEnds.append(bind)
            if crossInterfaceEnds:
                connVal['crossInterfaceEnds'] = crossInterfaceEnds

        # Pruned connections are the tb/DUT boundary connections getBDConnections
        # moved out of `connections` because their DUT end is an excluded
        # instance (--excludeInst). Their surviving (contained) end can still be a
        # cross-interface bind whose declared port interface differs from the
        # connection interface; without classifying it the tbExternal would bind
        # the surviving instance port to the inherited DUT-boundary port unadapted.
        # Classification runs here (after the prune at getBDConnections) over the
        # surviving ends only, attaching the same crossInterfaceEnds annotation the
        # connectDouble path produces so the thunker emission carries to the
        # boundary.
        for connVal in ret['prunedConnections'].values():
            crossInterfaceEnds = []
            for endKey, endVal in connVal.get('ends', {}).items():
                bind = annotate(
                    connVal,
                    endKey,
                    endVal.get('instanceKey') or '',
                    endVal.get('portName') or '',
                    endVal.get('instance') or '',
                    endVal.get('direction') or '',
                    parentConfigOverride=connVal['excludedEndConfig'],
                )
                if bind:
                    endVal['crossInterface'] = bind
                    crossInterfaceEnds.append(bind)
            if crossInterfaceEnds:
                connVal['crossInterfaceEnds'] = crossInterfaceEnds

        # Also walk connection-port views so block views whose only
        # exposure to a cross-interface bind is via the boundary port
        # (i.e. the consumer-side end appears only in connectionPorts,
        # not in `connections`) still observe the annotation. Without
        # this pass the consumer's port generation in getBDPorts cannot
        # detect that the port should be typed by the child's declared
        # interface rather than the parent connection's interface.
        for connVal in ret.get('connectionPorts', {}).values():
            crossInterfaceEnds = []
            for endKey, endVal in connVal.get('ends', {}).items():
                if 'crossInterface' in endVal:
                    crossInterfaceEnds.append(endVal['crossInterface'])
                    continue
                bind = annotate(
                    connVal,
                    endKey,
                    endVal.get('instanceKey') or '',
                    endVal.get('portName') or '',
                    endVal.get('instance') or '',
                    endVal.get('direction') or '',
                )
                if bind:
                    endVal['crossInterface'] = bind
                    crossInterfaceEnds.append(bind)
            if crossInterfaceEnds and not connVal.get('crossInterfaceEnds'):
                connVal['crossInterfaceEnds'] = crossInterfaceEnds

        for connMap in ret['connectionMaps'].values():
            bind = annotate(
                connMap,
                '',
                connMap.get('instanceKey') or '',
                connMap.get('instancePortName') or '',
                connMap.get('instance') or '',
                connMap.get('direction') or '',
            )
            if bind:
                connMap['crossInterface'] = bind
                connMap['crossInterfaceEnds'] = [bind]

    connMapping = { 'connectDouble': ['connections', 'registerConnections'],
                    'connectSingle': ['connectionMaps', 'memoryConnections'] }

    def getBDChannelConfigOverrides(self, ret):
        # Annotate every emitted channel with the SystemC Config override
        # the connected leaf-parameterizable end implies. Templates read
        # `configOverride` directly through `sc_struct_type_name` and do
        # not re-walk instance / variant / parameter tables. Runs after
        # `getBDCrossInterfaceBinds` so cross-interface ends are excluded
        # from the override selection.
        for source in ('connections', 'registerConnections'):
            for connVal in ret[source].values():
                connVal['configOverride'] = self._resolveConnectionConfigOverride(connVal)

    def getBDConnectionsFinal(self, ret):
        # deduplicate the channels
        duplicateCheck = dict()
        duplicateList = []
        for connType, connSources in self.connMapping.items():
            for connSource in connSources:
                ret[connType][connSource] = dict()
                for conn, connVal in ret[connSource].items():
                    channel = connVal['interfaceName']
                    index = 0
                    if channel in duplicateCheck:
                        if connVal['interfaceKey'] != duplicateCheck[channel]['connInfo']['interfaceKey']:
                            printError(f"Connection {conn} in {connSource} has the same channel name {channel} as another connection but different interface types "
                                       f"{self.data['interfaces'][connVal['interfaceKey']]['interfaceType']} and "
                                       f"{self.data['interfaces'][duplicateCheck[channel]['connInfo']['interfaceKey']]['interfaceType']}. Please rename one of the channels")
                            exit(warningAndErrorReport())
                        if connType != duplicateCheck[channel]['connType'] or connSource != duplicateCheck[channel]['connSource']:
                            printError(f"Connection {conn} in {connSource} has the same channel name {channel} as another connection but different connection types "
                                       f"{connType} and {duplicateCheck[channel]['connType']}. Please rename one of the channels")
                            exit(warningAndErrorReport())
                        count = duplicateCheck[channel]['count']
                        if count == 1:
                            duplicateList.append(channel)
                        duplicateCheck[channel]['conns'][conn] = count
                        index = count
                        duplicateCheck[channel]['count'] = count + 1
                    else:
                        duplicateCheck[channel] = {'connType': connType, 'connSource': connSource, 'connInfo': connVal, 'conns': {conn: 0}, 'count': 1}
                    ret[connType][connSource][conn] = dict(connVal)
                    ret[connType][connSource][conn]['channelCount'] = 1
                    ret[connType][connSource][conn]['index'] = index
        for channel in duplicateList:
            connType = duplicateCheck[channel]['connType']
            connSource = duplicateCheck[channel]['connSource']
            channelCount = duplicateCheck[channel]['count']
            for conn, connDisambiguate in duplicateCheck[channel]['conns'].items():
                ret[connType][connSource][conn]['channelCount'] = channelCount


    def getBDPorts(self, ret):
        # iterate through the port definitions to deduplicate
        ports = dict()
        newPorts = dict()
        for conn, connVal in ret['connectionPorts'].items():
            for end, endVal in connVal['ends'].items():
                portName = endVal['portName']
                self.getBDAddPort(ports, newPorts, portName, endVal)
                temp = dict(connVal, **ports[portName])
                # When this end has a bottom-up declared port whose interface
                # differs from the connection's (a cross-interface bind), the
                # port itself is typed by the child's declared interface.
                # Channel typing remains the connection's parent interface;
                # the per-protocol thunker bridges the two. Without this swap,
                # the consumer's port would emit with the producer's structure
                # type.
                crossBind = endVal.get('crossInterface')
                if crossBind and crossBind.get('childInterfaceKey'):
                    temp['connection']['interfaceKey'] = crossBind['childInterfaceKey']
                    self.getBDGetIntfStructs(ret, intfKey=crossBind['childInterfaceKey'])
                else:
                    temp['connection']['interfaceKey'] = connVal['interfaceKey']
                    self.getBDGetIntfStructs(ret, intfKey=connVal['interfaceKey'])
                ports[portName] = temp
        ret['ports']['connections'] = dict(ports)
        portTypes = {'connectionMapPorts': {'dest': 'connectionMaps', 'portName': 'instancePortName'},
                     'registerPorts': {'dest': 'registers', 'portName': 'register'},
                     'memoryPorts': {'dest': 'memories', 'portName': 'memory'}}
        for connType, portType in portTypes.items():
            newPorts = dict()
            for conn, connVal in ret[connType].items():
                self.getBDAddPort(ports, newPorts, connVal[portType['portName']], connVal)
            ret['ports'][portType['dest']] = dict(newPorts)

    def getBDAddPort(self, ports, newPorts, portName, connVal):
        instanceKey = connVal.get('instanceKey', 'parent')
        if portName not in ports:
            ports[portName] = dict()
            ports[portName]['connection'] = dict(connVal)
            ports[portName]['instance'] = {instanceKey: 0}
            ports[portName]['name'] = portName
            ports[portName]['direction'] = connVal.get('direction', 'src') # default to src for memory case
            newPorts[portName] = dict(ports[portName])
        else:
            if instanceKey in ports[portName]['instance']:
                printError(f"Duplicate port definition found for {portName} instance {instanceKey}")
                exit(warningAndErrorReport())
            else:
                ports[portName]['instance'][instanceKey] = 0

    def _resolveRouterUpstreamInterface(self, blockRow, upstreamPort):
        # Look up the interface bound to the router's upstream port.
        # New-schema routers do not author `ports:` for their upstream
        # port. The router's addressBlock names the addressBus interface
        # by port convention, and multiple APB-shaped interfaces may be
        # visible in the router's load-time scope.
        ports = blockRow.get('ports') or {}
        portRow = ports.get(upstreamPort)
        if portRow is not None:
            return portRow.get('interface')

        routerContext = blockRow['_context']
        # interface_defs is flat-keyed in projectOpen (keyed by
        # interface_typeKey); each value is the row directly.
        addressBusTypes = set()
        for row in self.data.get('interface_defs', {}).values():
            if isinstance(row, dict) and row.get('addressBus'):
                addressBusTypes.add(row.get('interface_type'))
        for context in self.yamlContext.get(routerContext, {}):
            ifaceRow = self.data.get('interfaces', {}).get(f"{upstreamPort}/{context}")
            if (
                ifaceRow
                and ifaceRow.get('interfaceType') in addressBusTypes
            ):
                return ifaceRow.get('interface')
        ifaceRow = self.data.get('interfaces', {}).get(f"{upstreamPort}/_a2csystem")
        if (
            ifaceRow
            and ifaceRow.get('interfaceType') in addressBusTypes
        ):
            return ifaceRow.get('interface')
        return None

    def _registerBusInterfacePort(self, ret):
        # Returns (interfaceName, portName) for the block's register-bus
        # surface, read from the design projectCreate produced. Routers
        # source the port from addressBlock.upstreamPort. Synthesised
        # register handlers (isRegHandler) and routed leaves both read the
        # leaf-to-handler connectionMap the post-parse pass emitted — the
        # handler from its instance side, the leaf from its block side.
        # `registerPorts:` is a parse-time construct that projectCreate
        # consumes to infer this connectivity; projectOpen does not read it.
        qualBlock = ret['qualBlock']
        blockRow = self.data['blocks'][qualBlock]
        addressBlock = blockRow.get('addressBlock')

        if ret['addressDecode']['isApbRouter'] and addressBlock:
            port = addressBlock['upstreamPort']
            interface = self._resolveRouterUpstreamInterface(blockRow, port)
            return interface, port

        if blockRow.get('isRegHandler'):
            # The synthesised handler block does not author
            # `registerPorts:` (that map is reserved for user-authored
            # leaf declarations). Its register-bus interface and port
            # come from the leaf-to-handler connectionMap that the
            # post-parse pass emitted: `block:` names the owning leaf,
            # `instance:` names this handler instance, `interface:`
            # carries the leaf-scoped register-bus interface, and
            # `instancePortName` carries the handler's canonical port
            # name (registerDecoderPort, e.g. `apbReg`). The
            # connectionMap's `port:` field is the leaf-side authored
            # port name and is *not* the handler's port.
            for cm in self.data.get('connectionMaps', {}).values():
                instKey = cm.get('instanceKey')
                if not instKey:
                    continue
                instRow = self.data['instances'].get(instKey)
                if instRow is None:
                    continue
                if instRow.get('instanceTypeKey') != qualBlock:
                    continue
                interface = cm.get('interface')
                port = cm.get('instancePortName') or cm.get('instancePort') or interface
                if interface:
                    return interface, port

        # A routed leaf reads its register-bus interface and port from the
        # leaf-to-handler connectionMap the post-parse pass emitted (block:
        # this leaf). This is the same row whether the leaf authored
        # registerPorts: or had its register bus inferred from the serving
        # router — projectOpen reads the resolved design, not the authored
        # construct.
        return self._leafRegisterBusFromHandlerMap(qualBlock)

    def _leafRegisterBusFromHandlerMap(self, qualBlock):
        # Read the (interface, port) the post-parse pass resolved onto a
        # routed leaf's leaf-to-handler connectionMap (the map whose
        # `block:` is this leaf). The resolved interface row must be
        # addressBus: true so a datapath cross-interface map on the same leaf
        # is not mistaken for the register bus. Returns None when the leaf has
        # no synthesised register handler.
        addressBusTypes = set()
        for row in self.data.get('interface_defs', {}).values():
            if isinstance(row, dict) and row.get('addressBus'):
                addressBusTypes.add(row.get('interface_type'))
        for cm in self.data.get('connectionMaps', {}).values():
            if cm.get('blockKey') != qualBlock:
                continue
            interfaceKey = cm.get('interfaceKey')
            if not interfaceKey:
                continue
            ifaceRow = self.data['interfaces'][interfaceKey]
            if ifaceRow.get('interfaceType') in addressBusTypes:
                interface = ifaceRow['interface']
                return interface, cm.get('port') or interface
        return None

    def getBDAddressBlockView(self, ret):
        qualBlock = ret['qualBlock']
        blockRow = self.data['blocks'][qualBlock]

        # Router blocks expose their authored addressBlock through this view;
        # isApbRouter is true only when the block authors addressBlock:.
        # Non-router blocks see no addressBlock.
        if not ret['addressDecode'].get('isApbRouter'):
            return

        ret['addressBlock'] = dict(blockRow['addressBlock'])

    def getBDAddressBus(self, ret):
        if ret['addressDecode']['isApbRouter'] or ret['addressDecode']['hasDecoder']:
            ret['addressDecode']['registerBusStructs'] = dict()
            (interfaceName, portName) = self._registerBusInterfacePort(ret)
            # registerBusInterface names the interface definition used
            # for type/structure lookup. registerBusPort names the port
            # object templates bind or read on the block-data view.
            ret['addressDecode']['registerBusInterface'] = interfaceName
            ret['addressDecode']['registerBusPort'] = portName
            interfaceInfo = [x for x in self.data['interfaces'].values() if x.get('interface') == interfaceName]
            if not interfaceInfo:
                printError(f"Register Bus Interface {interfaceName} does not match any yaml"
                           f"defined interface definitions. This is necessary to define what interface type is used for registers")
                exit(warningAndErrorReport())
            for regIf in interfaceInfo:
                for item in regIf['structures']:
                    ret['addressDecode']['registerBusStructs'].update( { item['structureType'] : item['structure'] } )

    def getBDIncludes(self, ret):
        sourceContexts = self.extractContext(ret['temp']['structs'], ret['temp']['consts'])
        for sourceContext in sourceContexts:
            if sourceContext not in self.specialContexts:
                ret['includeContext'][sourceContext] = 0

        # A parameterizable block emits its FULL module-local parameterized-decl
        # set (e.g. video_bayer_t), which can redeclare a context type that
        # transitively references a type in ANOTHER package (video_bayer_t ->
        # video_frame_t in isp_types). That other package is imported, not
        # redeclared, but nothing on the register/port surface references it
        # directly, so it would be dropped from the import/include list. Pull in
        # the contexts reachable from the decl-set struct keys via the same
        # recursive extractContext walk; over-inclusion is a harmless extra import.
        declStructs = dict()
        for decl in ret['parameterizedDecls']:
            if decl['declKind'] == 'structure':
                declStructs[decl['declKey']] = 0
        for sourceContext in self.extractContext(declStructs, dict()):
            if sourceContext not in self.specialContexts:
                ret['includeContext'][sourceContext] = 0

        classStructs = dict()
        classConsts = dict()

        def addStructKey(structKey):
            if structKey:
                classStructs[structKey] = 0

        def addConstKey(constKey):
            if constKey:
                classConsts[constKey] = 0

        def addInterfaceStructs(intfKey):
            if not intfKey:
                return
            intfData = self.data['interfaces'].get(intfKey)
            if not intfData:
                return
            for structInfo in intfData.get('structures', []) or []:
                addStructKey(structInfo.get('structureKey'))

        for regData in ret.get('registers', {}).values():
            if regData.get('regType') != 'memory':
                addStructKey(regData.get('structureKey'))
            else:
                addStructKey(regData.get('structureKey'))
                addStructKey(regData.get('addressStructKey'))
                addConstKey(regData.get('wordLinesKey'))

        for memData in ret.get('memories', {}).values():
            addStructKey(memData.get('structureKey'))
            addConstKey(memData.get('wordLinesKey'))

        for memData in ret.get('memoryConnections', {}).values():
            addStructKey(memData.get('structureKey'))
            addStructKey(memData.get('addressStructKey'))

        for channelGroup in ret.get('connectDouble', {}).values():
            for connData in channelGroup.values():
                addInterfaceStructs(connData.get('interfaceKey'))
                addStructKey(connData.get('structureKey'))
                addStructKey(connData.get('addressStructKey'))
                for crossBind in connData.get('crossInterfaceEnds', []) or []:
                    for payload in (crossBind.get('thunker') or {}).get('payloads', []) or []:
                        addStructKey(payload.get('structureKey'))

        for connMapData in ret.get('connectionMaps', {}).values():
            for crossBind in connMapData.get('crossInterfaceEnds', []) or []:
                for payload in (crossBind.get('thunker') or {}).get('payloads', []) or []:
                    addStructKey(payload.get('structureKey'))

        if ret['addressDecode'].get('isApbRouter') or ret['addressDecode'].get('hasDecoder'):
            # The router's upstream interface determines the register-bus
            # structures pulled into the class declaration. Walk the resolved
            # interface rather than the global table directly.
            regBusInterface = ret['addressDecode'].get('registerBusInterface')
            if regBusInterface:
                for intfData in self.data['interfaces'].values():
                    if intfData.get('interface') == regBusInterface:
                        for item in intfData.get('structures', []) or []:
                            addStructKey(item.get('structureKey'))

        classContexts = self.extractContext(classStructs, classConsts)
        for sourceContext in ret['includeContext']:
            if sourceContext in classContexts and sourceContext not in self.specialContexts:
                ret['classIncludeContext'][sourceContext] = 0
        for sourceContext in classContexts:
            if sourceContext not in ret['classIncludeContext'] and sourceContext not in self.specialContexts:
                ret['classIncludeContext'][sourceContext] = 0

        # Config headers are a distinct include surface from structure/type
        # context includes. Class declarations, trampolines, testbenches, and
        # Verilated wrappers spell concrete Config policy names; collect those
        # contexts once in the block view so templates do not need to re-query
        # project-wide data.
        if ret['blockInfo'].get('params'):
            # The block's Config struct is emitted in its canonical config
            # context, which differs from its declaring context when the block
            # is defined in a file that includes the IP root.
            config_context = ret['blockInfo']['configContext']
            if config_context and config_context not in self.specialContexts:
                ret['configIncludeContext'][config_context] = 0
        # Child instance shared_ptr declarations name the child's per-variant
        # Config (e.g., `ipLeafBase<ipLeafVariantLeaf0Config>`). The child's
        # class header lives in the child block's own context, but its Config
        # struct is defined in the child's canonical config context. Without
        # aggregating those contexts here the parent's class-declaration TU
        # cannot resolve the Config struct name. The aggregation is bounded by
        # subBlockInstances whose child block is itself parameterizable.
        for inst_data in (ret.get('subBlockInstances') or {}).values():
            type_key = inst_data.get('instanceTypeKey')
            if not type_key:
                continue
            child_block = self.data.get('blocks', {}).get(type_key)
            if not child_block:
                continue
            if not child_block.get('isParameterizable', False):
                continue
            child_context = child_block['_context']
            if child_context and child_context not in self.specialContexts:
                ret['includeContext'][child_context] = 0
            child_config_context = child_block['configContext']
            if child_config_context and child_config_context not in self.specialContexts:
                ret['configIncludeContext'][child_config_context] = 0

    def getBDInterfaceDefs(self, ret):
        """Collect interface definitions for all interface types used in the block

        Creates a simple mapping from interface type aliases to canonical interface types.
        This allows 'reg_ro' to map to 'status', etc.
        """
        # Get interface_defs from loaded data
        all_interface_defs = self.data.get('interface_defs', {})

        # Build simple mapping: alias -> qualified canonical interface type
        # by filtering interface_defs that have mappedFrom data
        # Example: {'reg_ro': 'status/_a2csystem', 'reg_rw': 'control/_a2csystem', ...}
        type_mappings = {}
        type_mappings_qualified = {}
        for qual_key, intf_def in all_interface_defs.items():
            if 'mappedFrom' in intf_def and intf_def['mappedFrom']:
                for mapping_key, mapping_data in intf_def['mappedFrom'].items():
                    if 'mapped_type' in mapping_data:
                        mapped_type = mapping_data['mapped_type']
                        # Only include mappings for register interface types we're using
                        if mapped_type in ret['temp']['registerInterfaceTypes']:
                            type_mappings[mapped_type] = intf_def['interface_type']
                            type_mappings_qualified[mapped_type] = qual_key
                            ret['interfaceTypes'][intf_def['interface_type']] = qual_key

        ret['interface_type_mappings'] = type_mappings
        for intf_type, qual_key in ret['interfaceTypes'].items():
            ret['interface_defs'][intf_type] = all_interface_defs[qual_key]

    def extractContext(self, structs, consts):
        ret = dict()
        todo = structs
        while todo:
            nextLoop = dict()
            for structKey in todo:
                struct = self.data['structures'][structKey]
                ret[struct['_context']] = 0
                for field, fieldData in struct['vars'].items():
                    if fieldData['varTypeKey']:
                        context = qualifiedKeyContext(
                            fieldData['varType'], fieldData['varTypeKey'],
                            f"structure field '{field}' varType")
                        ret[context] = 0
                    elif fieldData['subStructKey']:
                        context = qualifiedKeyContext(
                            fieldData['subStruct'], fieldData['subStructKey'],
                            f"structure field '{field}' subStruct")
                        ret[context] = 0
                        nextLoop[fieldData['subStructKey']] = 0
                    if fieldData['arraySizeKey']:
                        context = qualifiedKeyContext(
                            fieldData['arraySize'], fieldData['arraySizeKey'],
                            f"structure field '{field}' arraySize")
                        ret[context] = 0
            todo = nextLoop
        for const in consts:
            if '/' in const:
                _name, context = splitQualifiedKey(const, 'constant')
                ret[context] = 0
        return ret

    # create dictionary of blocks and the connections that they contain within the scope of instances
    def setContainedConnections(self, top, instances):
        self.blockContainedConnection[self.data['instances'][top]['instanceTypeKey']] = dict()
        for instance in instances:
            self.blockContainedConnection[self.data['instances'][instance]['instanceTypeKey']] = dict()
        for conn,connVal in self.data['connections'].items():
            for end, endVal in connVal['ends'].items():
                if endVal['direction']=='src':
                    src = endVal['instanceKey']
                    srcContainer = self.data['instances'][src]['containerKey']
                else:
                    dst = endVal['instanceKey']
                    dstContainer = self.data['instances'][dst]['containerKey']
            # in context of interest?
            if src in instances and dst in instances:
                if srcContainer != dstContainer:
                    printError(f"Src {src} and dst {dst} for connection {conn} not between peers")
                    exit(warningAndErrorReport())
                self.blockContainedConnection[self.data['instances'][src]['containerKey']][conn] = connVal

    def resolveConnectionEnd(self, end, hier, nestedPort = None):
        ret = None
        # end could be initial real connection or a nested hierarchical mapping
        # try getting port used for real connection
        if nestedPort is None:
            port = end.get('portId', None)
        else:
            port = nestedPort

        this = self.data['connectionMaps'].get(port, None)
        if this:
            # this is a connection that has been mapped (if the hierarchy includes the instance within range limitations)

            # check if we even have more hierarchy to decend down
            moreHier = hier['more']
            if moreHier:
                # we have some nested hier
                nestedHier = moreHier.get(this['instanceKey'], None)
                if nestedHier:
                    if this['instancePort']:
                        nextPort = nestedHier['instanceTypeKey'] + this['instancePort']
                    else:
                        nextPort = nestedHier['instanceTypeKey'] + this['port']
                    # continue down the rabbit hole
                    ret = self.resolveConnectionEnd(this, nestedHier, nestedPort=nextPort)
        # eventually there is no more rabbit hole or no more connection maps, so get the name
        if not ret:
            ret = hier['hierarchyName']
        return ret

    def resolveConnectionEnds(self, parent, hier, connKey, connVal):
        ret = dict()
        for dir, end in connVal['ends'].items():
            # this should always be safe at the top
            subHier = hier['more'][end['instanceKey']]
            ret[end['direction']] = self.resolveConnectionEnd(end, subHier)
        return ret

    def getHierConnections(self, parent, hierInst, flatInstances):
        connections = list()
        # based on the parent instance, what is the parent block type
        parentBlock = self.data['instances'][parent]['instanceTypeKey']
        # there can only be connections if there are contained instances which might be depth limited
        if hierInst['more']:
            # get all the connections contained by parent
            if parentBlock in self.blockContainedConnection:
                for conn, connVal in self.blockContainedConnection[parentBlock].items():
                    ret =  self.resolveConnectionEnds(hierInst['hierarchyName'], hierInst, conn, connVal)
                    ret['structures'] = self.data['interfaces'][connVal['interfaceKey']]['structures']
                    ret['interface']  = self.data['interfaces'][connVal['interfaceKey']]['interface']
                    ret['desc']       = self.data['interfaces'][connVal['interfaceKey']]['desc']
                    connections.append(ret)
            # now recurse the contained instances if there are any

            for inst, subHier in hierInst['more'].items():
                ret = self.getHierConnections(inst, subHier, flatInstances)
                connections = connections + ret
        return connections

    def setRangeOfInstances(self, startInstance, depth):
        # iterativly recurse the structure. Every interation builds set of newInstances the next level down
        toProcess = [startInstance]
        for d in range(depth):
            newInstances = OrderedDict()
            for inst in toProcess:
                newInstances.update( self.getHier(inst) )

            self.rangeOfInstances.update(newInstances)
            toProcess = newInstances

    # Return a dictionary of instances
    #  each instance is a dictionary as well that contains the following keys
    #       instanceType
    #       color
    #       hierarchyName - this is a long hierarchical name in cases of larger depth
    #       more          - this dictionary if None means no more instances contained
    #                         otherwise another dictionary of instances are inside
    #
    # The result is a dictionary of instance keys in heirarchical form
    def setRangeOfInstancesByHier(self, startInstance, depth):
        newInstances = self.addHierEntry(startInstance, '')
        newInstances['more'] = self.recursiveHier(startInstance, (self.hierKey[self.data['instances'][startInstance]['instanceTypeKey']]), 0, depth)

        return newInstances

    def addHierEntry(self, inst, parentName):
        ret = dict()
        ret['instanceType']  = self.data['instances'][inst]['instanceType']
        ret['instanceTypeKey']  = self.data['instances'][inst]['instanceTypeKey']
        ret['color']         = self.data['instances'][inst]['color']
        ret['desc']          = self.data['blocks'][self.blocks[ret['instanceType']]]['desc']
        if len(parentName)>0:
            ret['hierarchyName'] = parentName+'.'+inst
        else:
            ret['hierarchyName'] = inst
        return ret

    # This is a helper furnction for setRangeOfInstancesByHier
    # This function helps build the recursive dictionary(s) while managing the depth chosen
    def recursiveHier(self, parentName, instances, currentDepth, depth):
        currentDepth = currentDepth + 1
        newInstances = dict()
        for inst in instances:
            newInstances[inst] = self.addHierEntry(inst, parentName)
            if (len(self.hierKey[self.data['instances'][inst]['instanceTypeKey']]) > 0 and currentDepth != depth):
                newInstances[inst]['more'] = self.recursiveHier(parentName+'.'+inst, (self.hierKey[self.data['instances'][inst]['instanceTypeKey']]), currentDepth, depth)
            else:
                newInstances[inst]['more'] = None

        return newInstances

    # Returns the contexts for a single block / instance
    def getContexts(self, instance):
        contexts = []
        i = self.qualInstance(instance)
        for k, v in self.yamlContext[self.data['instances'][i]['_context']].items():
            contexts.append(k)

        return (contexts)

    # if no instance list provided it will use internal rangeOfInstances
    # create the set of connection and connectionMap
    def initConnections(self, instances=None):
        if instances is None:
            instances = self.rangeOfInstances
        # create instance for connection and block for connectionMap structures from rangeOfInstances
        blocks = dict()
        for instance in instances:
            self.connections[instance] = OrderedDict()
            block = self.data['instances'][instance]['instanceTypeKey']
            blocks[block] = None
            self.connectionMaps[block] = OrderedDict()

        self.connections['_external'] = OrderedDict()
        external = dict()
        previousKey = ""
        for connKey, connection in self.data['connections'].items():
            capture = False
            # there are 4 cases
            # both src and destination are of interest
            # either source or dst are of interest (2 cases)
            # neither are of interest
            # the main problem is that when just 1 is mentioned, it can be of either order
            for dir, dirconn in connection['ends'].items():
                # is a instance of interest mentioned
                if dirconn['instanceKey'] in instances:
                    # put the merge of the two dicts into the connection map
                    self.connections[dirconn['instanceKey']][connKey] = {**dirconn, **connection}
                    # delete the ends as redundant
                    del self.connections[dirconn['instanceKey']][connKey]['ends']
                    # detect if we are on the second part of one sided capture (the not capture ensures the second part)
                    if connKey==previousKey and not capture:
                        self.connections['_external'][connKey] = external[connKey]
                    previousKey = connKey
                    capture = True
                else:
                    if capture:
                        # we are on second part of one sided capture
                        self.connections['_external'][connKey] = dirconn
                    previousKey = connKey
                    external[connKey] = dirconn
        # scan through all the connectionMaps and gather any that are for the set of blocks of interest
        # group by block
        for connMapKey, connMap in self.data['connectionMaps'].items():
            block = connMap['blockKey']
            if block in blocks:
                self.connectionMaps[block][connMapKey] = connMap

    def getHier(self, instance):
        ret = OrderedDict()
        #instance can be qualified or un qualified
        # if its an unqualified name, then convert to qualified or assume its already qualified if not found
        qualInstance = self.instances.get(instance, instance)
        if isinstance(qualInstance, dict):
            printError(f'Unqualified name provided that was not unique:"{instance}" ')
            exit(warningAndErrorReport())

        if qualInstance not in self.data['instances']:
            printError(f'Invalid instance:"{instance}" is not part of design')
            exit(warningAndErrorReport())
        block = self.data['instances'][qualInstance]['instanceTypeKey']
        return (self.hierKey[block].copy())

    def qualInstance(self, instance):
        ret = self.instances.get(instance, None)
        if ret is None:
            printError(f'Invalid instance:"{instance}" is not part of design')
            exit(warningAndErrorReport())
        return ret

    def getQualBlockVariants(self, qualBlock):
        variants = []
        variantData = self.data['parameters'].get(qualBlock, {}).get('variants', {})
        for _, data in variantData.items():
            if data['variant'] not in variants:
                variants.append(data['variant'])
        return(variants)

# this class is used to create the database based on the schema
# it also contains the logic to validate the yaml files against the schema
# it also contains the logic to validate the addressControl file
# it should be noted that the data is held in dictionarys during the parsing process
# but unlilke the user representation, it is held in context form to allow
# input to be scope checked. The context is removed during the save to the database
class projectCreate:
    proj = None
    a2cProj = None
    schemaYaml = None
    schema = None
    data = dict()
    flatData = dict()
    addressControl = None
    topInstance = None
    counterGroup = OrderedDict() # for counter group current values
    counterGroupControl = OrderedDict() # for counter group control info
    counterData = OrderedDict() # record allocation of values
    counterReverseField = None
    addressObjects = OrderedDict()
    yamlAllFiles = OrderedDict()
    yamlUnread = list()
    yamlRaw = dict()
    yamlDependancies = OrderedDict()
    yamlContext = OrderedDict() #dict containing precalculated contexts by file
    enums = dict() # contains enums by yamlfile scope
    qualEnums = dict() # contains enums by qualified name
    # section are simple, custom or something inbetween.
    #simple sections dont need any special handling - no auto fields
    simpleSections = {"types", "blocks", "variables", "interfaces", "instances", 'connectionMaps', "structures", "memories", "registers", "memoryConnections", "registerConnections", "parameters" }
    #custom section require complete custom section handling including the main loop
    customSections = {"connections", "ipParameters"}
    # any section inbetween has a per entry handler
    ignoreSections = {"include", "flows", "includeName", "blockDir" } # note all project file field are added later
    generatorTemplates = {"cppConfig", "svConfig", "docConfig" }
    dontValidate = {'_topInstance'} # list of keys that should not be validated if validator is present
    stdFields = {"context"}
    specialContexts = {"_global", "_a2csystem"} # special contexts that should be excluded from includes
    errorState = False
    includeName = dict()
    # Per-context owning projectName, keyed identically to includeName. Files in
    # the root project's own closure map to the root PROJECTNAME; a context
    # reached through a referenced child project file maps to that child's
    # projectName (see readRaw ownership BFS).
    contextOwningProject = dict()
    includeValid = dict()
    includeSections = {"types", "structures", "constants"}
    # ipParameters constants captured per file as they are parsed, so the
    # block-param linkage can be validated after a file's section loop
    # completes. Keyed by yamlFile, then by constant name.
    ipParametersConstants = OrderedDict()
    hier = None
    hierKey = None
    instances = None
    instanceContainer = None
    blocks = None
    a2cRoot = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) #parent directory of pysrc
    yamlDir = None
    # Merge behaviour for combining base and pro project defaults.
    # By default, dictionaries are shallow-merged and lists are overridden.
    # Paths can opt into different strategies (see merge_with_spec helper).
    MERGE_SPEC = {
        # fileGeneration is merged shallow by default, but we allow
        # additional depth for specific children via their own spec.
        ("fileGeneration",): "dict_shallow",
        ("dirs",): "dict_shallow",
        # Merge fileMap at the key level (base and pro keys combined),
        # but keep each individual map entry shallow.
        ("fileGeneration", "fileMap"): "dict_shallow",
        # Templates are merged shallow - pro/user can override base templates.
        ("templates",): "dict_shallow",
        ("postProcess",): "list_override",
    }

    def __init__(self, projFile, dbFile):

        # Start each projectCreate with an empty YAML byte cache so a stale hit
        # never leaks across multiple projectCreate calls in one process (unit
        # tests). Pre-scan reads (project.yaml, schema) then hit disk; the
        # scan-all pre-pass repopulates it for readRaw's closure parse.
        yamlReadCache.clear()

        if os.path.exists(dbFile):
            os.remove(dbFile)

        g.db = sqlite3.connect(dbFile)
        if g.debug:
            g.db.row_factory = dict_factory
        else:
            g.db.row_factory = sqlite3.Row
        g.cur = g.db.cursor()
        #initialize the config object
        self.config = config(RO = False)
        # _parserResolver: parse-time-only ValueResolver, owned by the
        # YAML parser. processSingleFile rebinds it on entry to a resolver
        # bound to the file currently being parsed; the orchestrator
        # methods (processYamls, postYamlExternalScript, generateAddressEnums)
        # null it at the end of each phase. Its purpose is to amortize one
        # resolver per file across the many parse-time call sites (auto
        # handlers, processSimple eval evaluation, _constants finalization).
        # Post-parse code (calcAddresses, future derivations) must construct
        # its own ValueResolver instead of reaching through this attribute;
        # the parser does not own the post-parse lifecycle and the per-file
        # `.context` would be stale / wrong outside a processSingleFile frame.
        self._parserResolver = None
        # Parsed eval IR nodes by (yamlFile, constant name), populated when an
        # eval constant is parsed in processSimple and consumed by _constants.
        # Transient to this projectCreate; only the canonical string persists.
        self._evalNodes = {}
        # Per referenced child project file, its raw content and the absolute
        # directory of the child project file (so its dirs: resolve relative to
        # the child file, mirroring the root's relative-to-project-file rule).
        # Keyed by the child's projectName; populated by readRaw and consumed by
        # buildProjectLayout to produce that project's $root-resolved layout.
        self.childProjectRaw = {}
        # Selected provider file (context key) per referenced projectName. A
        # second, lexically-different provider path for the same declared
        # projectName is a duplicate-provider error unless an ancestor
        # projectOverrides entry redirects one of them. Populated by readRaw.
        self.projectProviders = {}
        global dirMacros
        #load project file from command line
        self._userProjRaw = existsLoad(projFile)
        # Remember the user-supplied project file path so address-policy
        # diagnostics can name it (project.yaml may be renamed per-example).
        self.projFile = projFile
        # Absolute root project path captured before any chdir, so the scan-all
        # pre-pass (run after cwd moves to the project dir) resolves it correctly.
        self._rootProjFileAbs = os.path.abspath(projFile)
        # Merge base/pro/user project config. mergeProjectConfig owns the pro-vs-base
        # a2cRoot promotion and the merge precedence; the raw base/pro inputs are kept
        # so configTemplates() can merge template config files with user > pro > base.
        (self.a2cRoot, self._a2cBaseProj, self._a2cProProj,
         self.a2cProj, self.proj) = mergeProjectConfig(projFile)
        dirMacros = { "a2c" : self.a2cRoot }
        self.config.setConfig('A2CROOT', self.a2cRoot)
        self.config.setConfig('A2CPROJ', self.a2cProj)
        # Refuse to build an un-migrated project before any address or eval
        # processing runs. This is the sole detector of a pre-migration project.
        self._gateYamlFormat()
        # save the global base path referenced by project file location
        g.yamlBasePath = os.path.dirname(os.path.abspath(projFile))
        os.chdir(os.path.dirname(os.path.abspath(projFile)))
        schemaFile = resolveFilePath(self.proj, self.a2cProj, "dbSchema", self.a2cRoot )
        # read schema file referenced by project
        self.schemaYaml = existsLoad(schemaFile)
        # initialize schema base on the schema file
        self.schema = Schema(self.schemaYaml, schemaFile)
        self.counterReverseField = self.schema.counter_reverse_field

        # Normalize project-level address policy before instance auto fields
        # allocate IDs from those groups.
        self.loadProjectAddressPolicy()
        # A design project names its root instance with topInstance. A
        # definitions-only project (types/interfaces/constants shared across
        # projects, with no instances or blocks of its own) has no root
        # instance; topInstance is then omitted and stays None. Instance-,
        # hierarchy-, and address-driven passes iterate the (empty) instance
        # table and are natural no-ops for such a project.
        if 'topInstance' in self.proj:
            self.topInstance = self.proj['topInstance']
        self.projectDirs()
        self.validateLayout()
        self.buildLayout()
        self.configTemplates()
        #anything except for specific keys in the project file are all saved to the config for later use
        # this also allows user additions to the project file to make it through to the generators
        self.createProjectConfig()
        # save the base yaml path as well incase needed by the generators
        self.config.setConfig('BASEYAMLPATH', g.yamlBasePath)
        # create all the databases based on the schema
        self.createDatabase(self.schema.data['schema'])
        # Load system files first (from a2cProj - base/pro config)
        systemFiles = []
        if "systemFiles" in self.a2cProj:
            # Use a2cRoot directly as the base path since it's already set correctly
            systemFiles = self.getFileList(self.a2cProj, self.a2cRoot)[0]

        # Then load user project files
        (userFiles, userInclude, userProjectSlot) = self.getFileList(self.proj, g.yamlBasePath)

        # Seed the file-read BFS. Each queue entry is (file, viaProjectFiles,
        # inheritedOverrides): system files and the root project's include
        # closure are not project-file candidates; only the root's
        # projectFiles: entries can open a child project (resolved in readRaw).
        # inheritedOverrides carries the projectOverrides declared by ancestor
        # project files (highest ancestor wins); the root project seeds them.
        # File OWNERSHIP is derived from the scan-all reconcile after readRaw
        # (_deriveOwnershipFromScan), independent of BFS traversal order.
        rootOverrides = self._mergeOverrides(self.proj, '.', {})
        self.yamlUnread = [(f, False, rootOverrides) for f in systemFiles]
        self.yamlUnread += [(f, f in userProjectSlot, rootOverrides) for f in userFiles]
        self.systemFiles = set(systemFiles)  # Track which are system files
        # Scan-all pre-pass (side-effect-free): resolves the full projectFiles:/
        # include: reference closure INCLUDING the own closure of every
        # override-redirected child-project copy, and reconciles physically
        # distinct copies of one logical project onto one master. readRaw
        # consumes its member-level alias so only master copies are parsed, and
        # ownership/logical-key derivation below reads its reconciled result.
        # The scanner populates yamlReadCache during its walk; readRaw's
        # existsLoad parses those bytes from memory instead of a second disk read.
        # Function-local import: projectScan imports processYaml at module scope
        # (it binds projectCreate methods), so a module-scope import here would
        # be circular.
        from pysrc.projectScan import ProjectScanner
        self.scanResult = ProjectScanner(self._rootProjFileAbs).scan()
        #read all the files into project
        self.readRaw()
        # derive per-context ownership and logical key from the scan-all result
        # (the single, multi-copy-reconciled ownership implementation)
        self._deriveOwnershipFromScan()
        # derive the per-owning-project directory layouts (root + any children)
        self.buildProjectLayout()
        # process all files
        self.processYamls()
        # all files fully parsed: validate the whole-project ipParameters linkage
        self._validateIpParametersLinkage()
        # run any user provided post processing
        self.postYamlExternalScript()
        # create database indexes
        self.generateIndexes()
        # perform all address calculations
        self.calcAddresses()
        # derive per-block config info (isParameterizable, defaultConfig)
        # from a one-shot structure walk and persist on the blocks row
        self.calcBlockConfigInfo()
        # derive the owner-qualified foreign per-variant Config header set (one
        # durable fact shared by the build manifest and the newModule scaffold)
        self.calcForeignConfigHeaders()
        # derive the per-block module-local parameterized declaration set and
        # persist it into the non-schema blockParameterizedDecls table
        self.deriveParameterizedDeclSets()
        # generate address enums and types
        self.generateAddressEnums()
        # check include files are valid
        self.saveIncludeFiles()
        # The project's top context: the defining context of the topInstance's
        # block. Its include chain spans the whole build, so it keys the single
        # per-project (mode: project) artifact, the rtl.f verilator file list.
        # A definitions-only project (no topInstance) has no top context.
        # Persisted before runCreateArtifacts so the build manifest consumes it.
        topContext = None
        if self.topInstance is not None:
            blockByKey = {row['blockKey']: row for row in self.flatData['blocks'].values()}
            for instRow in self.flatData['instances'].values():
                if instRow['container'] == '_topInstance':
                    topContext = blockByKey[instRow['instanceTypeKey']]['_context']
                    break
        self.config.setConfig('TOPCONTEXT', topContext, bin=True)
        # run late artifact creators that consume the completed project state
        self.runCreateArtifacts()
        # save the schema as well to the config
        self.validatePorts()
        self.schema.save()
        self.config.setConfig('YAMLCONTEXT', self.yamlContext, bin=True) # save the structure of the yaml contexts for header usages
        self.config.setConfig('INCLUDENAME', self.includeName, bin=True) # save the structure of the yaml contexts for header usages
        self.config.setConfig('CONTEXTOWNINGPROJECT', self.contextOwningProject, bin=True) # per-context owning projectName, keyed identically to includeName
        # Per-context node directory (the seam saveIncludeFiles uses to place each
        # context's generated artifacts), keyed identically to includeName. Covers
        # types-only contexts that have no block, so a projectOpen view can resolve
        # a block-less context's node dir without a data['blocks'] row.
        self.config.setConfig('CONTEXTNODEDIR', {ctx: data['dir'] for ctx, data in self.includeValid.items()}, bin=True)
        # instanceKeys contained (transitively) by this build's topInstance.
        # Consumers that enumerate the whole instance table (address emission)
        # intersect with this set so a referenced child project's standalone
        # harness instances, present in the flat table but outside this build's
        # design tree, are excluded. A single-project build reaches every
        # instance, so the intersection is a no-op. Rebuild the hierarchy first
        # so synthesized register-handler instances (added by post-parse) are
        # reflected in the containment walk.
        # A design project (one that declares instances) must name its root
        # instance; only a definitions-only project (no instances) may omit
        # topInstance. Checked here, after instances are parsed, so a missing
        # topInstance fails clearly at database creation instead of surfacing
        # late during generation as an obscure "_top is not part of design".
        if self.topInstance is None and self.data['instances']:
            raise ValueError(
                f"Project '{self.proj.get('projectName', '<project>')}' declares "
                f"instances but is missing topInstance:. A design project must name its "
                f"root instance; only a definitions-only project (no instances or "
                f"blocks) may omit topInstance.")
        self.generateHierarchy()
        self.config.setConfig('REACHABLEINSTANCES', self.reachableInstanceKeys(), bin=True)
        # derive per-context and per-block module/package identities and enforce
        # their cross-build uniqueness
        self.deriveModuleIdentities()

        g.db.commit()
        g.db.close()
        printIfDebug("Process Complete")

    def deriveModuleIdentities(self):
        # Per-context C++ module/namespace linkage identity, keyed identically to
        # includeName. Role A emitters (the SystemC `export module` and namespace
        # names) spell this identity; it is deliberately separate from the raw
        # include stem, which continues to name generated files and SystemVerilog
        # packages so those stay unqualified.
        #
        # The identity is the include stem project-qualified by the context's
        # intrinsic owner (CONTEXTOWNINGPROJECT), with a prefix dedup: a context
        # whose stem already equals or leads with its owning project stays
        # byte-identical, every genuinely cross-named context gets prefixed.
        # Because the owner is intrinsic (not the current build root), a context
        # spells the same C++ module name and SystemVerilog package name whether
        # built standalone or imported by a referencing parent project, so the
        # owning file's `export module <id>;` and a referencing file's
        # `import <id>;` always match. The raw include stem continues to name
        # generated files (filenames stay unqualified); only the in-file
        # identifier is qualified.
        self.contextModuleIdentity = {}
        for context, stem in self.includeName.items():
            self.contextModuleIdentity[context] = qualifyModuleIdentity(
                stem, self.contextOwningProject[context])
        self.config.setConfig('CONTEXTMODULEIDENTITY', self.contextModuleIdentity, bin=True)

        # A context's module/package identity names its generated SystemC module
        # and namespace and its SystemVerilog package. Two distinct contexts
        # sharing one identity would emit the same module/package name and
        # silently clobber each other's generated output, so reject it here.
        identityToContext = {}
        for context, identity in self.contextModuleIdentity.items():
            prior = identityToContext.get(identity)
            if prior is not None:
                printError(f"Module/package identity '{identity}' is used by "
                           f"two distinct contexts: '{prior}' (project "
                           f"'{self.contextOwningProject[prior]}') and '{context}' "
                           f"(project '{self.contextOwningProject[context]}'). "
                           f"Module and package names must be unique across all "
                           f"contexts in a build; give one context a distinct "
                           f"includeName.")
                exit(warningAndErrorReport())
            identityToContext[identity] = context

        # Per-block SystemVerilog module-name identity, keyed by blockKey and
        # analogous to contextModuleIdentity: the block name project-qualified by
        # its owning context with the same prefix dedup. Emit-only — the plain
        # blockName / instanceType stay the internal lookup keys. Consumed by the
        # module begin-declaration, the generator-owned endmodule, parent
        # instantiation, and the HDL wrapper's DUT instantiation so a same-named
        # block from two projects does not collide. The HDL wrapper's own
        # body/top module names stay plain: they are the filename-coupled
        # verilated tops (A2C_VL_TOP / --top-module derive from the unqualified
        # filename basename).
        blockByKey = {row['blockKey']: row for row in self.flatData['blocks'].values()}
        self.blockModuleName = {}
        for blockKey, blockRow in blockByKey.items():
            self.blockModuleName[blockKey] = qualifyModuleIdentity(
                blockRow['block'], self.contextOwningProject[blockRow['_context']])
        self.config.setConfig('BLOCKMODULENAME', self.blockModuleName, bin=True)

        # Two distinct blocks resolving to one qualified module name would emit
        # the same SystemVerilog module and silently clobber each other, so reject
        # it here (parallel to the context-identity gate above).
        moduleNameToBlock = {}
        for blockKey, moduleName in self.blockModuleName.items():
            prior = moduleNameToBlock.get(moduleName)
            if prior is not None:
                priorRow = blockByKey[prior]
                thisRow = blockByKey[blockKey]
                printError(f"SystemVerilog module name '{moduleName}' is used by "
                           f"two distinct blocks: '{priorRow['block']}' (project "
                           f"'{self.contextOwningProject[priorRow['_context']]}') and "
                           f"'{thisRow['block']}' (project "
                           f"'{self.contextOwningProject[thisRow['_context']]}'). "
                           f"Module names must be unique across all blocks in a "
                           f"build; rename one block.")
                exit(warningAndErrorReport())
            moduleNameToBlock[moduleName] = blockKey

    def _resolveDirMacros(self, dirsDict, baseDir):
        # Resolve a project's dirs: block into an absolute macro dict, seeded
        # with the shared a2c root. Paths are relative to baseDir (the project
        # file's directory) exactly as the root project's dirs resolve against
        # its own file location; a child project therefore roots under its own
        # directory. Returns a fresh dict so per-project resolution never
        # aliases the module-global dirMacros.
        macros = {"a2c": self.a2cRoot}
        if not dirsDict:
            return macros
        if 'root' not in dirsDict:
            self.logError("Definition for project root directory missing in project file. This should reflect the root of all generated files and is relative to project file")
        # Build macros in an order-independent way: resolve entries only once
        # their referenced macro (if any) is available.
        pending = dict(dirsDict)
        resolved_this_pass = True
        while pending and resolved_this_pass:
            resolved_this_pass = False
            # Iterate over a *copy* so we can pop items as they are resolved.
            for name, raw_path in list(pending.items()):
                # Use currently known macros (existing + newly resolved)
                expanded = _expand_with_macros(raw_path, macros)
                # If expansion still starts with '$' then we have an unresolved
                # dependency on another macro – skip for now.
                if expanded and expanded[0] == '$':
                    continue
                macros[name] = os.path.abspath(os.path.join(baseDir, expanded))
                pending.pop(name)
                resolved_this_pass = True
        # Any remaining entries could not be resolved because their macro target
        # is missing or circular; keep previous behaviour (store the raw path,
        # abspath'd) but flag an error.
        for name, raw_path in pending.items():
            self.logError(
                f"Could not fully resolve directory macro '{name}' "
                f"with path '{raw_path}' – leaving unresolved macro in path."
            )
            macros[name] = os.path.abspath(os.path.join(baseDir, raw_path))
        return macros

    def projectDirs(self):
        global dirMacros
        # The root project's dirs resolve relative to its project file location,
        # which is the current working directory (chdir'd in __init__).
        dirMacros = self._resolveDirMacros(self.proj.get('dirs'), g.yamlBasePath)
        self.config.setConfig('DIRS', dirMacros)

    # Valid project layout modes (see fileGeneration.layout in config/project.yaml).
    LAYOUT_MODES = ('functional', 'hierarchical')

    def validateLayout(self):
        # fileGeneration.layout selects the directory layout axis ordering. The
        # base config supplies the default ('functional'), so the merged project
        # config always carries it; reject any other value early.
        if 'fileGeneration' in self.proj:
            mode = self.proj['fileGeneration']['layout']
            if mode not in self.LAYOUT_MODES:
                self.logError(
                    f"fileGeneration.layout must be one of {self.LAYOUT_MODES}, "
                    f"got '{mode}'")

    # Keys in hierarchicalDirs that locate project-scope artifacts rather than a
    # fileMap basePath segment: the authored-YAML subdir of a node (yaml), the
    # project container for generated orphan artifacts (prj), the per-project
    # build dir (rundir), and the user-owned build config (include). rundir and
    # include are $root-anchored and stay at the project root (Q-L3 amended).
    LAYOUT_CONVENTION_KEYS = ('yaml', 'prj', 'rundir', 'include')

    def _buildLayoutFor(self, dirMacros, fileGeneration):
        # Normalize one project's resolved dirs (dirMacros) + fileGeneration into
        # the layout-keyed shape the seam (expandNewModulePath) and build views
        # consume. functional placement is the project's resolved dirs:,
        # hierarchical placement is the fileGeneration.hierarchicalDirs defaults.
        # Selected by layout:. Called once per project (root + each child) so
        # each project's segments root under its own $root.
        mode = fileGeneration['layout']
        buildGroups = fileGeneration['buildGroups']
        fileMapBasePaths = {fileDef['basePath']
                            for fileDef in fileGeneration['fileMap'].values()}
        for key in fileMapBasePaths:
            if key not in buildGroups:
                self.logError(
                    f"fileGeneration.buildGroups must define basePath segment "
                    f"'{key}'")

        def buildGroupForSegment(key):
            if key not in buildGroups:
                return None
            return buildGroups[key]

        if mode == 'functional':
            # functional segments ARE the project's resolved $root-rooted dirs,
            # so the seam emits byte-identical paths. Conventions match today's
            # tree: authored YAML under arch/yaml, project artifacts at root.
            segments = {key: {'path': path, 'buildGroup': buildGroupForSegment(key)}
                        for key, path in dirMacros.items()}
            conventions = {
                'yaml':    os.path.join(dirMacros['root'], 'arch', 'yaml'),
                'prj':     dirMacros['root'],
                'rundir':  os.path.join(dirMacros['root'], 'rundir'),
                'include': os.path.join(dirMacros['root'], 'include'),
            }
        else:  # hierarchical
            hdirs = fileGeneration['hierarchicalDirs']
            segments = {}
            conventions = {}
            for key, raw in hdirs.items():
                # $root-anchored conventions (prj, rundir) resolve to absolute;
                # bare node-relative segment names stay relative and are joined
                # onto the node directory at emit time.
                expanded = _expand_with_macros(raw, dirMacros)
                value = os.path.abspath(expanded) if expanded != raw else raw
                if key in self.LAYOUT_CONVENTION_KEYS:
                    conventions[key] = value
                else:
                    segments[key] = {
                        'path': value,
                        'buildGroup': buildGroupForSegment(key),
                    }
            # vl_wrap HDL wrappers are node-relative like every other block
            # segment: mode: block emits each wrapper beside its block. The
            # whole-design verilation build-output dir (obj_dir + lib) is
            # project-scope, derived in createBuildManifest (prj + segment).
        return {
            'mode':        mode,
            'segments':    segments,
            # Project root, layout-agnostic: functional exposes it as a segment,
            # hierarchical does not, so callers read it here in both modes.
            'root':        dirMacros['root'],
            'buildGroups': sorted({group for group in buildGroups.values()
                                   if group is not None}),
            'yaml':        conventions['yaml'],
            'prj':         conventions['prj'],
            'rundir':      conventions['rundir'],
            'include':     conventions['include'],
        }

    def buildLayout(self):
        # Persist the root project's layout as config LAYOUT so generators read
        # it on projectOpen. This stays the module-global root layout used by
        # parse-time placement; PROJECTLAYOUT (built after readRaw) additionally
        # holds one such layout per owning project for per-owner path selection.
        global layoutConfig
        layoutConfig = self._buildLayoutFor(dirMacros, self.proj['fileGeneration'])
        self.config.setConfig('LAYOUT', layoutConfig)

    def buildProjectLayout(self):
        # PROJECTLAYOUT: dict(projectName -> layoutConfig), one entry per owning
        # project (the root plus each referenced child project file), keyed by
        # the same projectName stored in CONTEXTOWNINGPROJECT. Each value has the
        # exact shape _buildLayoutFor produces, but with segments resolved under
        # THAT project's own $root, so object path resolution selects the owning
        # project's segments. On a monolithic project there is exactly one entry
        # and PROJECTLAYOUT[rootProjectName] is the root global layoutConfig.
        global layoutConfig
        rootProjectName = self.config.getConfig('PROJECTNAME')
        self.projectLayout = {rootProjectName: layoutConfig}
        for childName, childInfo in self.childProjectRaw.items():
            # Give the child the same merged view the root got (base/pro
            # defaults overlaid by the child's own project file), then resolve
            # its dirs relative to the child project file and build its layout.
            childProj = merge_with_spec(self.a2cProj, childInfo['raw'],
                                        projectCreate.MERGE_SPEC, path=())
            childMacros = self._resolveDirMacros(childProj.get('dirs'),
                                                 childInfo['projectFileDir'])
            self.projectLayout[childName] = self._buildLayoutFor(
                childMacros, childProj['fileGeneration'])
        self.config.setConfig('PROJECTLAYOUT', self.projectLayout, bin=True)

    def createProjectConfig(self):
        # save anything in project file to config except named items
        notConfig = {"projectFiles", "dirs", "systemFiles", "templates"}
        toSave = {'TOPINSTANCE': '_top', "PROJECTNAME": "Nameless"} #initialize to some defaults as appropriate
        for item in self.proj:
            # to allow later processing of nested project files we need to ensure the lower level parser ignores them by adding them to the set
            self.ignoreSections.add(item)
            if item not in notConfig:
                toSave[item.upper()] = self.proj[item]
        for item in toSave:
            self.config.setConfig(item, toSave[item])
        for item in self.a2cProj:
            self.ignoreSections.add(item)

    def configTemplates(self):
        # Reject deprecated config file references before template selection.
        deprecated_keys = {'cppConfig', 'svConfig', 'docConfig'}
        found_deprecated = deprecated_keys & self._userProjRaw.keys()
        if found_deprecated:
            self.logError(
                f"Template configuration has changed. The following keys are no longer supported: {', '.join(found_deprecated)}.\n"
                f"Please migrate your template mappings to a unified 'templates:' section in your project.yaml file.\n"
                f"For most projects this means just delete these keys to get the default system template mappings.\n"
                f"Only add user-defined template mappings if you need to add or override the defaults.\n"
                f"See the base config files (builder/base/config/project.yaml or builder/config/project.yaml) for examples.\n"
                f"The 'templates:' section should combine all template mappings from cppConfig, svConfig, and docConfig\n"
                f"into a single dictionary with template name as key and template file path as value."
            )
            return

        # Extract unified templates from merged project config
        # The templates have already been merged via merge_with_spec (base -> pro -> user)
        templates = self.proj.get('templates', {})

        if not templates:
            self.logWarning("No templates defined in project configuration. Code generation may fail.")
            templateConfig = {'templates': {}}
        else:
            # Expand macros in template file paths
            expanded_templates = {}
            for template_name, template_path in templates.items():
                expanded_path = expandDirMacros(template_path)
                expanded_templates[template_name] = os.path.abspath(expanded_path)

            templateConfig = {'templates': expanded_templates}

        self.config.setConfig('TEMPLATES', templateConfig)

    def logError(self, msg):
        self.errorState = True
        printError(msg)
        if not continueOnError:
            exit(warningAndErrorReport())

    def logWarning(self, msg):
        self.errorState = False
        printWarning(msg)

    def postYamlExternalScript(self):
        if "postProcess" in self.proj:
            self.generateHierarchy()
            # create 'fake' global context to allow processing
            self.yamlContext['_global'] = {key: None for key in self.yamlContext}
            self.yamlContext['_global']['_global'] = None
            for script in self.proj["postProcess"]:
                fileName = basePathRelative(expandDirMacros(script))
                scriptCode = loadModule(fileName)
                newData = scriptCode.postProcess(self)
                if newData:
                    self.processSingleFile("_global", sections=newData)
            del self.yamlContext['_global']
        g.db.commit()
        # Phase complete; see processYamls() for the rationale.
        self._parserResolver = None

    def runCreateArtifacts(self):
        if "createArtifacts" in self.proj:
            for script in self.proj["createArtifacts"]:
                fileName = basePathRelative(expandDirMacros(script))
                scriptCode = loadModule(fileName)
                scriptCode.create(self)
        g.db.commit()

    def generateIndexes(self):
        for table in self.schema.tables:
            for index in self.schema.data['indexes'][table]:
                sql = f"CREATE INDEX idx_{table}_{index} ON {table} (\"{index}\")"
                g.cur.execute(sql)

    def createDatabase(self, schema, level=""):

        for table, cols in schema.items():
            self.createTable(level+table, cols)

    def createTable(self, table, cols):

        col = comma = ""
        for field in cols:
            if isinstance(cols[field], dict):
                self.createTable(table+field, cols[field])
            else:
                col = f"{col}{comma}\"{field}\"" # field is quoted to allow for sql reserved words
                comma = ", "
        self.schema.data['colsSQL'][table] = col
        sql = f"CREATE TABLE {table} ({col})"
        g.cur.execute(sql)
        self.data[table] = dict()
        if self.schema.data['flat'][table]:
            self.flatData[table] = OrderedDict()

    def addFlatRecord(self, section, row):
        # Incrementally maintained flat index for sections with
        # _attribs: [flat]. Mirrors self.data[section][context][name]
        # keyed by the section's qualified storage key. Duplicate
        # qualified keys are a parse-state bug (the producer should
        # never re-emit the same row, even structurally identical)
        # and are reported.
        if not self.schema.data['flat'][section]:
            return
        node = self.schema.get_node(section)
        keyField = node.get_storage_key_field_name_qualified()
        flatKey = row[keyField]
        flatSection = self.flatData[section]
        if flatKey in flatSection:
            printError(f"Duplicate flat key {flatKey} found in section {section}")
            exit(warningAndErrorReport())
        flatSection[flatKey] = row

    def generateHierarchy(self):
        (hier, hierKey, qualInstances, instanceContainer, blocks) = generateHierarchy(self.data['instances'], self.data['blocks'], withContext=True)
        self.hier = hier
        self.hierKey = hierKey
        self.instances = qualInstances
        self.instanceContainer = instanceContainer
        self.blocks = blocks

    def reachableInstanceKeys(self):
        """Return the set of instanceKeys that participate in this build's
        design hierarchy, i.e. everything contained (transitively) by the
        project's topInstance.

        When a referenced child project is parsed into the same database, its
        own standalone top and the instances beneath it are present in the
        flat instance table but are not contained by this build's topInstance;
        they are excluded here so passes that reason about the design tree see
        only the active build's graph. For a single-project build every
        instance descends from the topInstance, so the result is every
        instance and this filtering is a no-op.

        Reachability follows block containment via hierKey (containerBlockKey
        -> contained instances): the topInstance rows anchor the walk and each
        contained instance's block expands to its own contained instances.
        """
        reachable = set()
        blockQueue = list()
        for instanceKey, instRow in self.flatData['instances'].items():
            if instRow['container'] == '_topInstance':
                reachable.add(instanceKey)
                blockQueue.append(instRow['instanceTypeKey'])
        seenBlocks = set()
        while blockQueue:
            blockKey = blockQueue.pop()
            if blockKey in seenBlocks:
                continue
            seenBlocks.add(blockKey)
            for childInstanceKey, childRow in self.hierKey.get(blockKey, {}).items():
                reachable.add(childInstanceKey)
                blockQueue.append(childRow['instanceTypeKey'])
        return reachable

    def getFileList(self, data, basePath, dependencies=None):
        todoNorm = list()
        incNorm = list()
        # normalized paths that arrived via the projectFiles: slot; the only
        # slot that may introduce a child project (systemFiles/include entries
        # are never treated as project-file candidates by the ownership BFS).
        projectSlotNorm = set()
        dep_set = set()
        if dependencies:
            dep_set = set(sum(dependencies.values(), []))
        if not data:
            return (todoNorm, incNorm, projectSlotNorm)
        # Handle systemFiles (needs macro expansion)
        if "systemFiles" in data:
            systemF = data["systemFiles"]
            for f in systemF:
                # Expand macros like $a2c before resolving path
                expandedPath = expandDirMacros(f)
                todoNorm.append(os.path.relpath(os.path.join(basePath, expandedPath), g.yamlBasePath))
        if "projectFiles" in data:
            todo = data["projectFiles"]
            for f in todo:
                norm = os.path.relpath(os.path.join(basePath, f), g.yamlBasePath)
                todoNorm.append(norm)
                projectSlotNorm.add(norm)
        if "include" in data:
            inc = data["include"]
            for f in inc:
                if os.path.basename(f) == f and f in dep_set:
                    incNorm.append(f)
                else:
                    incNorm.append(os.path.relpath(os.path.join(basePath, f), g.yamlBasePath))
            todoNorm.extend(incNorm)
        return(todoNorm, incNorm, projectSlotNorm)

    def _isChildProjectFile(self, raw):
        # Positive project-file classifier. A referenced file is a child project
        # only when its raw content carries the full project-file sentinel set
        # (projectName + dirs + fileGeneration). The a2c base config carries
        # dirs/fileGeneration but no projectName, and regular design files carry
        # none of these, so neither is misclassified. The caller additionally
        # gates on arrival via the projectFiles: slot.
        if not raw:
            return False
        return all(key in raw for key in ("projectName", "dirs", "fileGeneration"))

    def _mergeOverrides(self, raw, declDir, inherited):
        # Merge the projectOverrides declared by one project file over the map
        # inherited from its ancestors. An ancestor's entry for a projectName is
        # never displaced by a descendant's (highest applicable ancestor wins).
        # Each override path is absolute or relative to the declaring project
        # file and is normalized LEXICALLY to a context key (no symlink deref),
        # mirroring getFileList's include/projectFiles normalization. The value
        # is (targetContextKey, declaringDir) so provider selection and error
        # reporting can name the declaration.
        merged = dict(inherited)
        overrides = raw.get('projectOverrides')
        if not overrides:
            return merged
        for projName, path in overrides.items():
            if projName in merged:
                # Sibling/descendant override of an already-selected projectName
                # is ignored: the highest ancestor's selection is authoritative.
                continue
            targetKey = os.path.relpath(os.path.join(declDir, path), g.yamlBasePath)
            merged[projName] = (targetKey, declDir)
        return merged

    def _selectProvider(self, refKey, projName, inheritedOverrides):
        # Resolve the provider context key for a child-project reference. Absent
        # an ancestor override for projName the referenced file is the provider;
        # otherwise the ancestor override redirects to its target, which MUST
        # itself declare the requested projectName. Owns the missing-target and
        # name-mismatch errors.
        if projName not in inheritedOverrides:
            return refKey
        targetKey, declDir = inheritedOverrides[projName]
        if not os.path.exists(targetKey):
            printError(f"projectOverrides in '{declDir}' selects '{targetKey}' "
                       f"for projectName '{projName}', but that file does not "
                       f"exist.")
            exit(warningAndErrorReport())
        targetRaw = existsLoad(targetKey)
        if not self._isChildProjectFile(targetRaw) or targetRaw['projectName'] != projName:
            declared = targetRaw.get('projectName') if targetRaw else None
            printError(f"projectOverrides in '{declDir}' selects '{targetKey}' "
                       f"for projectName '{projName}', but that file declares "
                       f"projectName '{declared}'.")
            exit(warningAndErrorReport())
        return targetKey

    def readRaw(self):
        # Read files until nothing is left to do. Each queue entry carries
        # whether it arrived via a projectFiles: slot (the only slot that can
        # open a child project) and the provider-override map inherited from its
        # ancestor projects. Ownership is NOT decided here: _deriveOwnershipFromScan()
        # reads it from the scan-all reconcile after every file is read.
        while self.yamlUnread:
            newFiles = list()
            for (f, viaProjectFiles, inheritedOverrides) in self.yamlUnread:
                # Member-level canonicalization: a non-master copy of a
                # projectOverride-unified logical file resolves onto its master
                # member, so only master copies are parsed. Applied both here (to
                # catch any seed entry) and to every getFileList result below (so
                # recorded references and queued files name the master), which is
                # what lets a redirected copy's design members - reached via the
                # including project's include: edges - resolve onto the master's
                # members instead of parsing as the including project's own. The
                # alias map is empty unless an override unifies multiple physical
                # copies, so the monolithic/single-copy case is unchanged.
                f = self.scanResult.aliasMemberToMaster.get(f, f)
                if f in self.yamlAllFiles:
                    continue
                raw = existsLoad(f)
                nextOverrides = inheritedOverrides
                # A project file may only be reached through the projectFiles:
                # slot. Reaching one via an include: edge is a fatal authoring
                # error: a project file provides nothing to include: scoping.
                if self._isChildProjectFile(raw) and not viaProjectFiles:
                    printError(f"'{f}' declares projectName "
                               f"'{raw['projectName']}' and is a project file, "
                               f"but it is referenced via include:. A project "
                               f"file provides nothing to include: scoping and "
                               f"must be referenced only via projectFiles:.")
                    exit(warningAndErrorReport())
                # A projectFiles-slot entry carrying the project sentinel keys
                # opens a child project, subject to provider-override redirection
                # against the ancestor overrides.
                if viaProjectFiles and self._isChildProjectFile(raw):
                    projName = raw["projectName"]
                    selectedKey = self._selectProvider(f, projName, inheritedOverrides)
                    if selectedKey != f:
                        # Redirected by an ancestor override: f is not itself a
                        # context; process the selected provider instead. The
                        # redirect + enqueue below is load-bearing.
                        if selectedKey not in self.yamlAllFiles:
                            newFiles.insert(0, (selectedKey, True, inheritedOverrides))
                        continue
                    # f is the selected provider for projName. A second, lexically
                    # different path claiming the same projectName is ambiguous
                    # unless an ancestor override selects one (which would have
                    # redirected the loser above).
                    prior = self.projectProviders.get(projName)
                    if prior is not None and prior != f:
                        printError(f"Multiple providers declare projectName "
                                   f"'{projName}': '{prior}' and '{f}'. Add a "
                                   f"projectOverrides entry in an ancestor "
                                   f"project to select one.")
                        exit(warningAndErrorReport())
                    self.projectProviders[projName] = f
                    # Capture the child's raw project content plus its own file
                    # location, so buildProjectLayout can resolve the child's
                    # dirs: relative to the child project file (not the root). f
                    # is a relpath from g.yamlBasePath and cwd is g.yamlBasePath,
                    # so abspath yields the child project file's directory.
                    self.childProjectRaw[projName] = {
                        'raw': raw,
                        'projectFileDir': os.path.abspath(os.path.dirname(f)),
                    }
                    # A child project's own projectOverrides extend the inherited
                    # map for its subtree (ancestor entries still win).
                    nextOverrides = self._mergeOverrides(raw, os.path.dirname(f),
                                                         inheritedOverrides)
                self.yamlAllFiles[f] = None
                self.yamlRaw[f] = raw
                myBase = os.path.dirname(f)
                (todo, include, projectSlotFiles) = self.getFileList(raw, myBase, self.yamlDependancies)
                # Canonicalize member-level aliases so every recorded reference
                # and queued file names the master copy (see the dequeue
                # canonicalization above). No-op when no override unifies copies.
                alias = self.scanResult.aliasMemberToMaster
                if alias:
                    todo = [alias.get(t, t) for t in todo]
                    include = [alias.get(t, t) for t in include]
                    projectSlotFiles = {alias.get(t, t) for t in projectSlotFiles}
                if raw and "includeName" in raw:
                    self.includeName[f] = raw["includeName"]
                else:
                    self.includeName[f] = os.path.splitext(os.path.basename(f))[0]
                for t in todo:
                    if t not in self.yamlAllFiles:
                        newFiles.insert(0, (t, t in projectSlotFiles, nextOverrides))
                if f in self.yamlDependancies:
                    self.yamlDependancies[f].update(include)
                else:
                    self.yamlDependancies[f] = include

            self.yamlUnread = newFiles
        # Both cache consumers are done: the scan pre-pass has drained and every
        # closure file has been parsed here. Drop the cached bytes so the whole
        # closure does not stay resident for the rest of the process.
        yamlReadCache.clear()

    def _deriveOwnershipFromScan(self):
        # Per-context ownership and logical key derived from the scan-all
        # ScanResult - the single ownership implementation. The scanner walks the
        # full projectFiles:/include: closure INCLUDING every override-redirected
        # child copy's own closure and reconciles physically distinct copies of
        # one logical project onto one master, so each parsed (master) context
        # carries its reconciled owning projectName and logical key
        # (owningProjectName, projRelPath) - the identity two physical copies of
        # one logical IP share. Only system/root-only files (systemFiles, outside
        # the scan's design closure) fall back to the root PROJECTNAME, matching
        # the prior default-to-root behavior; a monolithic project has no child
        # providers so every design context resolves to the root PROJECTNAME. A
        # design context that is not a systemFile yet absent from the scan
        # ownership is a key-mismatch bug (its scanner key spelled differently
        # from its parse key) and is rejected here rather than silently
        # defaulted. The logical key (owningProjectName, projRelPath) is derived
        # only to log the multi-copy signal below; system files carry none.
        rootProjectName = self.config.getConfig('PROJECTNAME')
        logicalGroups = {}
        for f in self.yamlAllFiles:
            owner = self.scanResult.ownership.get(f)
            if owner is None:
                if f not in self.systemFiles:
                    printError(f"context '{f}' is parsed into the project but is "
                               f"absent from the scan-all ownership closure and "
                               f"is not a systemFile; its scan key likely differs "
                               f"from its parse key (ownership key mismatch).")
                    exit(warningAndErrorReport())
                # System file: outside the scan closure, so it carries no
                # logical key either.
                self.contextOwningProject[f] = rootProjectName
                continue
            self.contextOwningProject[f] = owner
            # logicalKey is keyed identically to ownership, so an owned file
            # always carries one.
            logical = self.scanResult.logicalKey[f]
            logicalGroups.setdefault(logical, []).append(f)
            printIfDebug(f"logicalKey: {f} -> {logical[0]}::{logical[1]}")
        # Log physical keys that share one logical key (the multi-copy signal).
        for logical, physicals in logicalGroups.items():
            if len(physicals) > 1:
                printIfDebug(f"logicalKey MULTI-COPY {logical[0]}::{logical[1]}: "
                             + ", ".join(sorted(physicals)))

    def calcAddresses(self):
        # Post-parse derivation: parse-time self._parserResolver is None here.
        # Construct a local resolver for the wordLines lookups; only the
        # context-stateless lookupNamedRow helper is used, so no context
        # binding is needed.
        resolver = ValueResolver(self)
        # maintain a dict of the next available offset in a block
        blockAddressCurrent = dict()
        # loop through address generating objects
        for addressType, addressInfo in self.addressObjects.items():
            sortDescending = addressInfo.get('sortDescending', False)
            allocateOrder = dict()
            # decodeSize: bytes of address-decoded memory range, before any
            # sizeRoundUpPowerOf2/alignment padding. This is the worst-case
            # decoded size templates need for the apb decode case-range; the
            # padded `size` only feeds offset bumping. Non-memory registers
            # have no decode size; their row defaults to 0.
            decodeSizeMap = dict()
            # get everything that needs an address, sorted by block type then entry order. Entry order is maintained
            # to allow engineers to keep consistency of address generation and ensure addresses only change when intended
            if addressType == 'memories':
                sql = f"select a.*, a.ROWID, s.width, s.maxBitwidth, s.isParameterizable as structIsParam, a.isParameterizable as rowIsParam from {addressType} as a, structures as s where a.structureKey = s.structureKey and a.regAccess = 1 order by blockKey, a.ROWID"
            else:
                sql = f"select a.*, a.ROWID, s.width, s.maxBitwidth, s.isParameterizable as structIsParam, a.isParameterizable as rowIsParam from {addressType} as a, structures as s where a.structureKey = s.structureKey order by blockKey, a.ROWID"
            g.cur.execute(sql)
            data = g.cur.fetchall()
            currentBlock = ""
            keyField = self.schema.data['key'][addressType] + 'Key' # use the context disambiguated varient of the key for the address object
            for row in data:
                # as data is sorted by block, detect when the block changes
                if row['blockKey'] != currentBlock:
                    currentBlock = row['blockKey']
                    if currentBlock not in blockAddressCurrent:
                        blockAddressCurrent[currentBlock] = 0
                # Pick worst-case width when row is parameterizable.
                isParam = bool(row['rowIsParam'])
                width = row['maxBitwidth'] if (isParam and row['maxBitwidth']) else row['width']
                # for register memory type, use the memory objects alignment settings
                if addressType == 'memories' or (addressType == 'registers' and row['regType'] == 'memory'):
                    alignment = convert_value(self.addressObjects['memories'].get('alignment', 1))
                    alignmentModeValue = True if isinstance(alignment, int) else False
                    sizeRoundUpPowerOf2 = self.addressObjects['memories'].get('sizeRoundUpPowerOf2', False)
                    # memories can be aligned to an alignment value or to memory sized boundaries.
                    # memory size is based on the next rounded power of 2 of the data width, due to address decoding requirements.
                    # Worst-case wordLines uses maxValue when constant is parameterizable.
                    wlConst = self._resolveWordLinesConst(self.flatData[addressType][row[keyField]], resolver)
                    if isParam and wlConst and wlConst['isParameterizable'] and wlConst['maxValue']:
                        wordLines = wlConst['maxValue']
                    elif wlConst and wlConst['value'] is not None:
                        wordLines = wlConst['value']
                    else:
                        # _resolveWordLinesConst hard-errors on non-empty
                        # symbolic misses, so this is limited to missing/empty
                        # wordLines on rows that require address sizing.
                        keyField = 'memoryKey' if addressType == 'memories' else 'registerKey'
                        printError(f"Cannot determine wordLines for "
                                   f"{addressType[:-1]} '{row[keyField]}' "
                                   f"(blockKey='{row['blockKey']}', "
                                   f"wordLines='{row['wordLines']}', "
                                   f"wordLinesKey='{row['wordLinesKey']}'). "
                                   f"Address sizing requires a resolvable "
                                   f"wordLines value.")
                        exit(warningAndErrorReport())
                    decodeSize = roundup_pow2min4((width + 7) >> 3) * wordLines
                    size = decodeSize
                    if sizeRoundUpPowerOf2:
                        size = roundup_pow2min4(size)
                    if alignmentModeValue:
                        size = ((size + alignment - 1) // alignment ) * alignment
                elif addressType == 'registers':
                    alignment = convert_value(self.addressObjects['registers'].get('alignment', 1))
                    alignmentModeValue = True if isinstance(alignment, int) else False
                    # Regular register: width is in bits so convert to bytes and ensure alignment
                    #        bits to bytes              round up to alignment
                    bytesPerRow = (width + 7) >> 3
                    size = ((bytesPerRow + alignment - 1 ) // alignment ) * alignment
                    # Decoded address footprint for a non-memory register: the
                    # SV decoder emits one exact-offset case arm per
                    # REG_BUS_WIDTH_BYTES-wide bus segment of the structure, so
                    # the row occupies ceil(bytes / busWidth) * busWidth bytes
                    # of address space (no power-of-2 rounding; that only
                    # applies to memory range-match decode). busWidth matches
                    # templates/systemVerilog/moduleRegs.py REG_BUS_WIDTH_BYTES.
                    busWidth = 4
                    decodeSize = ((bytesPerRow + busWidth - 1) // busWidth) * busWidth
                else:
                    continue
                allocateOrder[row[keyField]] = size
                decodeSizeMap[row[keyField]] = decodeSize
            if sortDescending:
                # sort data list in ascending order of size
                data.sort(key=lambda x: allocateOrder[x[keyField]], reverse=True)
            for row in data:
                size = allocateOrder[row[keyField]]
                currentBlock = row['blockKey']
                offset = blockAddressCurrent[currentBlock]
                # Memory registers and memories use similar alignment logic
                if addressType == 'memories' or (addressType == 'registers' and row['regType'] == 'memory'):
                    alignment = convert_value(self.addressObjects['memories'].get('alignment', 1))
                    alignmentModeValue = True if isinstance(alignment, int) else False
                    sizeRoundUpPowerOf2 = self.addressObjects['memories'].get('sizeRoundUpPowerOf2', False)
                    if alignmentModeValue:
                        size = ((size + alignment - 1) // alignment ) * alignment
                        offset = ((offset + alignment - 1) // alignment ) * alignment
                        blockAddressCurrent[currentBlock] = offset + size
                    else:
                        # memory size alignment simplifies HW address decode
                        offset = ((blockAddressCurrent[currentBlock] + size - 1) // size ) * size
                        blockAddressCurrent[currentBlock] = offset + size
                else:
                    blockAddressCurrent[currentBlock] = offset + size
                decodeSize = decodeSizeMap[row[keyField]]
                sql = f"UPDATE {addressType} SET offset = {offset}, decodeSize = {decodeSize} WHERE \"{keyField}\" = '{row[keyField]}'" # field is quoted to allow for sql reserved words
                g.cur.execute(sql)

        # once all addresses are calculated we need to perform space checks
        for context in self.data['instances']:
            for instance, instData in self.data['instances'][context].items():
                # not every instance has used any space, so only check the ones that do
                if instData['instanceTypeKey'] in blockAddressCurrent:
                    # available is based on the number of size of each address space in that group * addressMultiples
                    availableSpace = self.addressControl['AddressGroups'][instData['addressGroup']]['addressIncrement'] * instData['addressMultiples']
                    if blockAddressCurrent[instData['instanceTypeKey']] > availableSpace:
                        printError(f"Block {instData['instanceKey']} overflowed its address space. Used: {blockAddressCurrent[instData['instanceTypeKey']]}. Available: {availableSpace}")
                        exit(warningAndErrorReport())
        for blockKey, address in blockAddressCurrent.items():
            sql = f"UPDATE blocks SET maxAddress = {address-1} WHERE blockKey = '{blockKey}'"
            g.cur.execute(sql)

        # Nested-decoder address containment. A routed slot whose block contains
        # a nested register decoder must fit that decoder's entire routed
        # footprint (addressIncrement * maxAddressSpaces) inside the per-child
        # window its parent decoder allocates to the slot. The space check above
        # keys on a block's decoded span (blockAddressCurrent) and so covers the
        # bare register-block slot; a router block owns no registers/memories,
        # never enters blockAddressCurrent, and is invisible to that check.
        # A project with no addressBlock: declarations has no AddressGroups.
        if isinstance(self.addressControl, dict) and 'AddressGroups' in self.addressControl:
            addressGroups = self.addressControl['AddressGroups']
            blockByKey = {row['blockKey']: row for row in self.flatData['blocks'].values()}
            # Map each container block key to the nested router group(s) it
            # instances. Resolve every group's router block through its block row
            # (declared name plus declaring file) rather than a raw name compare,
            # so composed builds with same-named blocks in different files stay
            # distinct.
            routerContainerGroups = dict()
            for group, groupRow in addressGroups.items():
                routerBlockKey = None
                for blockKey, blockRow in blockByKey.items():
                    if (blockRow['block'] == groupRow['_declaringBlock']
                            and blockRow['_context'] == groupRow['_declaringFile']):
                        routerBlockKey = blockKey
                        break
                if routerBlockKey is None:
                    continue
                for instRow in self.flatData['instances'].values():
                    if instRow['instanceTypeKey'] == routerBlockKey:
                        routerContainerGroups.setdefault(
                            instRow['containerKey'], list()).append(group)
            for instRow in self.flatData['instances'].values():
                parentGroup = instRow['addressGroup']
                # only routed slots (those carrying an addressGroup) have a
                # parent window; a router at the dispatch-tree root has none.
                if not parentGroup:
                    continue
                for childGroup in routerContainerGroups.get(instRow['instanceTypeKey'], list()):
                    childRow = addressGroups[childGroup]
                    childFootprint = childRow['addressIncrement'] * childRow['maxAddressSpaces']
                    parentRow = addressGroups[parentGroup]
                    parentWindow = parentRow['addressIncrement'] * instRow['addressMultiples']
                    if childFootprint > parentWindow:
                        printError(
                            f"Nested register decoder '{childRow['_declaringBlock']}' "
                            f"(group '{childGroup}') routes a {hex(childFootprint)}-byte footprint "
                            f"(addressIncrement {hex(childRow['addressIncrement'])} x "
                            f"maxAddressSpaces {childRow['maxAddressSpaces']}), which exceeds "
                            f"the {hex(parentWindow)}-byte window that parent decoder "
                            f"'{parentRow['_declaringBlock']}' (group '{parentGroup}') allocates "
                            f"to slot '{instRow['instanceKey']}' (addressIncrement "
                            f"{hex(parentRow['addressIncrement'])} x addressMultiples "
                            f"{instRow['addressMultiples']}). Reduce the nested decoder's "
                            f"increment or maxAddressSpaces, or widen the parent's addressIncrement.")
                        exit(warningAndErrorReport())

        if isinstance(self.addressControl, dict):
            self.config.setConfig("ADDRESS_CONFIG", self.addressControl, bin=True)


    def calcBlockConfigInfo(self):
        # One-shot post-processing pass: for each block, walk every
        # structure it references through registers, memories, connections,
        # and connection maps. Persist isParameterizable and defaultConfig
        # on the blocks row.
        # Walks parse-time rows rather than the per-block view assembled by
        # getBlockData(); the result is read back via the slim
        # getBDConfigInfo() and getBlockConfigView() in projectOpen.
        # Note: a block carries isParameterizable: true when at least one
        # structure on its reachable surface is itself isParameterizable;
        # the same flag name as on structures and registers/memories,
        # one scope up.

        def flat_rows(section):
            if section in self.flatData:
                return list(self.flatData[section].values())
            rows = list()
            for context_rows in self.data.get(section, dict()).values():
                rows.extend(context_rows.values())
            return rows

        structures = {r['structureKey']: r for r in flat_rows('structures')}
        interfaces = {r['interfaceKey']: r for r in flat_rows('interfaces')}

        instances_by_type = dict()
        instances_by_container = dict()
        instance_container = dict()
        inherit_instances = list()  # rows using inheritContainerParam (validated below)
        for r in flat_rows('instances'):
            instances_by_type.setdefault(r['instanceTypeKey'], list()).append(r['instanceKey'])
            cont = r['containerKey']
            if cont:
                instances_by_container.setdefault(cont, list()).append(r['instanceKey'])
                instance_container[r['instanceKey']] = cont
            if r['inheritContainerParam']:
                inherit_instances.append(r)

        conn_end_instances = dict()
        for r in flat_rows('connectionsends'):
            conn_end_instances.setdefault(r['connectionKey'], list()).append(r['instanceKey'])

        connections = flat_rows('connections')

        registers_by_block = dict()
        registers_by_key = dict()
        for r in flat_rows('registers'):
            registers_by_block.setdefault(r['blockKey'], list()).append(r)
            registers_by_key[r['registerBlockKey']] = r

        memories_by_block = dict()
        memories_by_key = dict()
        for r in flat_rows('memories'):
            memories_by_block.setdefault(r['blockKey'], list()).append(r)
            memories_by_key[r['memoryBlockKey']] = r

        memory_connections = flat_rows('memoryConnections')
        register_connections = flat_rows('registerConnections')
        connection_maps = flat_rows('connectionMaps')
        block_rows = flat_rows('blocks')

        # A block that declares its own `params:` is leaf-parameterizable and
        # must carry isParameterizable=true so getBlockConfigView surfaces the
        # per-variant Config descriptors that emit `<block><Variant>Config`
        # structs and feed the trampoline.
        blocks_with_own_params = dict()
        params_by_block = dict()
        for r in flat_rows('blocksparams'):
            blocks_with_own_params.setdefault(r['blockKey'], r['_context'] or '')
            params_by_block.setdefault(r['blockKey'], set()).add(r['param'])

        block_name = {r['blockKey']: r['block'] for r in block_rows}
        block_context = {r['blockKey']: r['_context'] for r in block_rows}

        def validate_inherit_container_params():
            # A contained-block instance may declare `inheritContainerParam: true`
            # (schema.yaml instances section) to be typed with the CONTAINER
            # block's active Config template symbol instead of a variant. Enforce
            # the preconditions here (once, reusing this pass's prebuilt maps):
            # (a) the child's params are a by-name subset of the container's;
            # (b) variant and inheritContainerParam are mutually exclusive on one
            # instance (per instance row); (c) the container block is
            # parameterized (declares params); (d) the child block declares
            # params; (e) container and child are the same owning project. A
            # block declares params iff it has blocksparams rows (params_by_block),
            # so parameterized == has-params here. The subset relationship is
            # load-bearing for the SV parent->child param name-forwarding path.
            seen_pairs = set()
            for inst in inherit_instances:
                childKey = inst['instanceTypeKey']
                containerKey = instance_container[inst['instanceKey']]
                # The container must be a real block (block_name spans every
                # block row; the root top instance's container is `_topInstance`,
                # which is not a block). Emit a clean diagnostic instead of a
                # KeyError on the block_name/block_context lookups below.
                if containerKey not in block_name:
                    self.logError(
                        f"instance {inst['instance']} in file {inst['_context']}: "
                        f"inheritContainerParam requires the instance to be "
                        f"contained in a block")
                    continue
                childName = block_name[childKey]
                containerName = block_name[containerKey]
                # (b) per-instance-row: variant is mutually exclusive.
                if inst['variant'] != '':
                    self.logError(
                        f"instance {inst['instance']} in file {inst['_context']}: "
                        f"variant and inheritContainerParam are mutually exclusive "
                        f"on one instance")
                # The remaining checks depend only on the (container, child) pair;
                # fire them once per distinct pair.
                if (containerKey, childKey) in seen_pairs:
                    continue
                seen_pairs.add((containerKey, childKey))
                childParams = params_by_block.get(childKey, set())
                containerParams = params_by_block.get(containerKey, set())
                # (e) same owning project.
                containerProj = self.contextOwningProject[block_context[containerKey]]
                childProj = self.contextOwningProject[block_context[childKey]]
                if containerProj != childProj:
                    self.logError(
                        f"instance {inst['instance']} in file {inst['_context']}: "
                        f"inheritContainerParam requires container block "
                        f"'{containerName}' (project '{containerProj}') and child "
                        f"block '{childName}' (project '{childProj}') to be the "
                        f"same owning project")
                # (d) child has params; (c) container parameterized;
                # (a) child params by-name subset of the container's.
                if not childParams:
                    self.logError(
                        f"instance {inst['instance']} in file {inst['_context']}: "
                        f"inheritContainerParam requires child block '{childName}' "
                        f"to declare params")
                elif not containerParams:
                    self.logError(
                        f"instance {inst['instance']} in file {inst['_context']}: "
                        f"inheritContainerParam requires container block "
                        f"'{containerName}' to be parameterized (declare params)")
                else:
                    missing = childParams - containerParams
                    if missing:
                        self.logError(
                            f"instance {inst['instance']} in file {inst['_context']}: "
                            f"inheritContainerParam child block '{childName}' "
                            f"param(s) {sorted(missing)} are not a by-name subset of "
                            f"container block '{containerName}' params "
                            f"{sorted(containerParams)}")

        validate_inherit_container_params()

        for block_row in block_rows:
            qualBlock = block_row['blockKey']
            blockName = block_row['block']
            is_reg_handler = bool(block_row['isRegHandler'])

            # For regHandler blocks, registers and memories live on the
            # parent block; mirror getBDRegistersMemories' parent lookup.
            register_block = qualBlock
            if is_reg_handler:
                for inst_key in instances_by_type.get(qualBlock, list()):
                    cont = instance_container.get(inst_key)
                    if cont:
                        register_block = cont
                        break

            qual_block_inst_set = set(instances_by_type.get(qualBlock, list()))
            contained_inst_set = set(instances_by_container.get(qualBlock, list()))

            contexts = list()
            is_parameterizable = False
            # Tracks whether is_parameterizable was set by a parameterizable
            # structure on the block's OWN surface (its own registers, memories,
            # or own-port interfaces) rather than one reached only through a
            # contained child at a frozen variant (the valid transit/container
            # case). An own-surface parameterizable structure requires the block
            # to be a class template (own `params:`) so it has a `Config` to
            # instantiate the type with; the validation after step 8 rejects an
            # own-surface flag on a block with no own params.
            own_surface_param = False

            def add_param_source(is_param, ctx, own_surface):
                nonlocal is_parameterizable, own_surface_param
                if not is_param:
                    return
                is_parameterizable = True
                if own_surface:
                    own_surface_param = True
                if ctx and ctx not in contexts:
                    contexts.append(ctx)

            def add_struct(struct_key, own_surface):
                if not struct_key:
                    return
                struct = structures[struct_key]
                add_param_source(bool(struct['isParameterizable']), struct['_context'] or '', own_surface)

            def add_regmem(row, own_surface):
                add_struct(row['structureKey'], own_surface)
                add_struct(row['addressStructKey'], own_surface)
                add_param_source(bool(row['isParameterizable']), row['_context'] or '', own_surface)

            def add_interface(interface_key, own_surface):
                intf = interfaces[interface_key]
                if not intf['isParameterizable']:
                    return
                for struct_row in intf.get('structures', {}).values():
                    add_struct(struct_row['structureKey'], own_surface)

            # 1. Connections that touch a port-owner instance of this block: the
            #    block owns the port, so a parameterizable interface is on its
            #    own surface.
            for conn in connections:
                ends = conn_end_instances.get(conn['connectionKey'], list())
                if conn['isParameterizable'] and any(e in qual_block_inst_set for e in ends):
                    add_interface(conn['interfaceKey'], own_surface=True)

            # 2. Connections contained in this block (connectDouble): these wire
            #    contained children to each other, so a parameterizable interface
            #    is reached through a child at a frozen variant, NOT the block's
            #    own surface (the valid transit/container case).
            for conn in connections:
                ends = conn_end_instances.get(conn['connectionKey'], list())
                if conn['isParameterizable'] and any(e in contained_inst_set for e in ends):
                    add_interface(conn['interfaceKey'], own_surface=False)

            # 3. Connection maps belonging to or terminating at this block: the
            #    map binds the block's own parent-facing port, so a
            #    parameterizable interface is on its own surface.
            for cm in connection_maps:
                if (cm['isParameterizable'] and
                        (cm['blockKey'] == qualBlock or cm['instanceKey'] in qual_block_inst_set)):
                    add_interface(cm['interfaceKey'], own_surface=True)

            # 4. Registers owned by this block (or parent block when this is
            #    a regHandler).
            for reg in registers_by_block.get(register_block, list()):
                add_regmem(reg, own_surface=True)

            # 5. Memories owned by this block (or parent block when this is
            #    a regHandler).
            for mem in memories_by_block.get(register_block, list()):
                add_regmem(mem, own_surface=True)

            # 6. Memory connections touching this block (container or port).
            for mc in memory_connections:
                if mc['blockKey'] == qualBlock or mc['instanceKey'] in qual_block_inst_set:
                    if mc['isParameterizable']:
                        mem_row = memories_by_key[mc['memoryBlockKey']]
                        add_regmem(mem_row, own_surface=True)

            # 7. Register connections touching this block (container or port).
            for rc in register_connections:
                if rc['blockKey'] == register_block or rc['instanceKey'] in qual_block_inst_set:
                    if rc['isParameterizable']:
                        reg_row = registers_by_key[rc['registerBlockKey']]
                        add_regmem(reg_row, own_surface=True)

            # 8. A block that declares its own `params:` is
            #    leaf-parameterizable even if no structure on its surface is
            #    itself parameterizable. The per-variant Config emission in
            #    includes.py and the trampoline in blockRegistrar.py both key
            #    on isParameterizable; without this flag the
            #    `<block><Variant>Config` structs and `<block>Registrar.cpp`
            #    are skipped. Primary context is the block's own context
            #    (where its `params:` are declared).
            own_param_context = blocks_with_own_params.get(qualBlock)
            if own_param_context is not None and not is_parameterizable:
                is_parameterizable = True
                if own_param_context and own_param_context not in contexts:
                    contexts.append(own_param_context)

            # A parameterizable structure on the block's own surface requires the
            # block to declare its own `params:` so it is a
            # template<typename Config> with a Config to instantiate the type.
            # An own-surface flag with no own params has no valid C++
            # realization: classDecl.py would emit a non-templated class that
            # names Type<Config> with no Config in scope. The valid
            # transit/container case is flagged only via step 2
            # (own_surface=False) and is not rejected here.
            if own_surface_param and own_param_context is None:
                printError(
                    f"Block '{blockName}' has a parameterizable structure on its "
                    f"own surface (its own register, memory, or own-port "
                    f"interface) but declares no params:. A non-templated block "
                    f"has no Config to instantiate a parameterizable type; add a "
                    f"params: declaration to make it a parameterizable (template) "
                    f"block, or use non-parameterizable structures on its surface."
                )
                exit(warningAndErrorReport())

            # Derive defaultConfig from contexts[0] (file-name basename
            # sanitised) when present, otherwise from the block name.
            # contexts[0] is also persisted verbatim as configContext: the
            # canonical config context, i.e. the YAML context that owns the
            # block's parameterizable declarations and where its Config struct
            # is emitted. This differs from the block's own _context when the
            # block is declared in a file that includes the IP root (e.g. a
            # testbench stimulus/sink), and every config-emission site keys on
            # configContext rather than the block's declaring context.
            if is_parameterizable:
                if contexts:
                    config_context = contexts[0]
                    base = os.path.splitext(os.path.basename(config_context))[0]
                    default_config = base.replace('-', '_').replace('.', '_') + 'DefaultConfig'
                else:
                    config_context = ''
                    default_config = blockName + 'DefaultConfig'
            else:
                config_context = ''
                default_config = ''

            # Mirror the derived fields onto the in-memory block row. Later stages
            # of this same projectCreate pass read the dict rather than re-querying
            # SQL: _configHeaderContexts consumes configContext, and artifact
            # hooks may filter on isParameterizable (the fileMap
            # blockRegistrar cond). Without the mirror they would see the parse-time
            # default (false) and the manifest would omit every registrar dir.
            block_row['configContext'] = config_context
            block_row['isParameterizable'] = is_parameterizable
            block_row['defaultConfig'] = default_config

            sql_param = 1 if is_parameterizable else 0
            g.cur.execute("UPDATE blocks SET isParameterizable = ?, "
                          "defaultConfig = ?, configContext = ? WHERE blockKey = ?",
                          (sql_param, default_config, config_context, qualBlock))


    def calcForeignConfigHeaders(self):
        # Authoritative set of owner-qualified foreign per-variant Config headers,
        # keyed (owningProject, childBlockKey) -> module file stub. A pair earns a
        # header iff some project declares a FOREIGN variant of the child (its
        # declaring project differs from the project owning the child's config
        # context) AND the child actually has Config fields to emit. The field
        # test mirrors the projectOpen emit gate: a variant Config struct's members
        # are the config context's parameterizable constants plus the child's own
        # block params, so a canonical foreign descriptor has non-empty values iff
        # one of those two sources is present. Persisting the pair here gives the
        # build manifest and the newModule scaffold one source of truth, so neither
        # can record a header the emitter would not produce. On a monolithic build
        # every declaring project is the root project, so nothing is foreign and
        # the set is empty.
        blockByKey = {row['blockKey']: row for row in self.flatData['blocks'].values()}
        blocksWithParams = {row['blockKey'] for row in self.flatData['blocksparams'].values()}
        paramConstantContexts = {row['_context'] for row in self.flatData['constants'].values()
                                 if row['isParameterizable'] and row['_context']}
        # The foreign-Config header basename is fileMap-derived (never a
        # hardcoded suffix): the foreignConfig fileMap entry supplies the name
        # tail ("VariantConfig") and ext, and expandNewModulePath composes the
        # basename from the owner-qualified stub exactly as saveIncludeFiles
        # derives config_hdr for the context config header. Only the basename is
        # consumed, so the moduleDir/module inputs do not affect the result.
        foreignDef = self.proj['fileGeneration']['fileMap']['foreignConfig']
        headers = dict()
        for contextRows in self.data['parametersvariantsparams'].values():
            for row in contextRows.values():
                childKey = row['blockKey']
                configContext = blockByKey[childKey]['configContext']
                if not configContext:
                    continue
                if row['projectName'] == self.contextOwningProject[configContext]:
                    continue
                if childKey not in blocksWithParams and configContext not in paramConstantContexts:
                    continue
                key = (row['projectName'], childKey)
                if key not in headers:
                    childBlock = blockByKey[childKey]['block']
                    stub = f"{sanitizeModuleToken(row['projectName'])}_{childBlock}"
                    layout = self.projectLayout[row['projectName']]
                    filePath = expandNewModulePath(foreignDef, blockByKey[childKey]['dir'],
                                                   childBlock, stub, layout, missingDirOk=True)
                    baseName = os.path.basename(filePath) + "." + foreignDef['ext']['cppm']
                    # `variants`: the FOREIGN variant labels this declaring project
                    # binds for the child. The Config module aggregates all of
                    # them into one unit; the per-variant SV verilated wrapper top
                    # (vlSvWrapForeign) emits one owner-qualified trampoline per
                    # label. Same source of truth so scaffold, manifest, and emit
                    # agree.
                    headers[key] = {'stub': stub, 'baseName': baseName, 'variants': set()}
                headers[key]['variants'].add(row['variant'])
        for entry in headers.values():
            entry['variants'] = sorted(entry['variants'])
        self.config.setConfig('FOREIGNCONFIGHEADERS', headers, bin=True)

    def deriveParameterizedDeclSets(self):
        # Derive, per parameterizable block, the parameterizable constants,
        # types, and structures that can be declared local to that block's
        # module: those visible to the block whose backing-parameter closure is
        # satisfiable by the block's own params. Order local dependencies before
        # their users and persist the keys + order into the non-schema
        # blockParameterizedDecls table that getBlockData() reads.
        #
        # Declaration dependencies are recovered from parse-time facts: eval
        # symbol keys for eval-derived constants, type width*Key references, and
        # structure varType/subStruct/arraySizeKey references. Each declaration
        # carries the backing parameter constants required to keep it symbolic
        # plus any module-local declarations that must appear earlier in the
        # same block.
        #
        # Runs immediately after calcBlockConfigInfo() (which set
        # blocks.isParameterizable). All inputs are persisted.

        # All structural inputs are already in memory from parsing as flat
        # qualified-key indexes (self.flatData), so read them from there. Every
        # field used below - the *Key dependency edges and the parse-time
        # isParameterizable - is carried on these rows.
        types = self.flatData['types']
        structures = self.flatData['structures']

        # Backing constants are exactly the block-param keys: a constant whose
        # qualified key is consumed by some block param.
        backingKeys = {row['paramKey'] for row in self.flatData['blocksparams'].values()}
        structVars = dict()
        for row in self.flatData['structuresvars'].values():
            structVars.setdefault(row['structureKey'], list()).append(row)

        constants = self.flatData['constants']
        evalConstSymbols = dict()
        for (yamlFile, constName), node in self._evalNodes.items():
            evalConstSymbols[constName + '/' + yamlFile] = evalExpr.symbolKeys(node)

        def emptyDeclDeps():
            return {'paramDeps': set(), 'localDeps': set()}

        constMemo = dict()
        typeMemo = dict()
        structMemo = dict()

        def mergeDeps(dst, src):
            dst['paramDeps'] |= src['paramDeps']
            dst['localDeps'] |= src['localDeps']

        def constantRefDeps(constKey, stack):
            deps = emptyDeclDeps()
            if not constKey:
                return deps
            constRow = constants.get(constKey)
            if constRow is None:
                return deps
            if constKey in backingKeys:
                deps['paramDeps'].add(constKey)
            elif constRow['isParameterizable'] and constRow['evalCanonical']:
                localDep = ('constant', constKey)
                deps['localDeps'].add(localDep)
                constDeps = constDeclDeps(constKey, stack)
                deps['paramDeps'] |= constDeps['paramDeps']
                deps['localDeps'] |= constDeps['localDeps']
            elif constRow['isParameterizable']:
                deps['paramDeps'].add(constKey)
            return deps

        def constDeclDeps(constKey, stack):
            cached = constMemo.get(constKey)
            if cached is not None:
                return cached
            if constKey in stack:
                printError(f"Generator bug in deriveParameterizedDeclSets: constant dependency cycle at '{constKey}'")
                exit(warningAndErrorReport())
            stack.add(constKey)
            deps = emptyDeclDeps()
            if constKey not in evalConstSymbols:
                printError(f"Generator bug in deriveParameterizedDeclSets: eval-derived constant '{constKey}' "
                           f"has no parse-time eval node")
                exit(warningAndErrorReport())
            for symKey in evalConstSymbols[constKey]:
                mergeDeps(deps, constantRefDeps(symKey, stack))
            stack.discard(constKey)
            constMemo[constKey] = deps
            return deps

        def typeInfo(typeKey):
            cached = typeMemo.get(typeKey)
            if cached is not None:
                return cached
            row = types[typeKey]
            deps = emptyDeclDeps()
            for key in (row['widthKey'], row['widthLog2Key'], row['widthLog2minus1Key']):
                mergeDeps(deps, constantRefDeps(key, set()))
            typeMemo[typeKey] = deps
            return deps

        def structInfo(structKey, stack):
            cached = structMemo.get(structKey)
            if cached is not None:
                return cached
            if structKey in stack:
                printError(f"Generator bug in deriveParameterizedDeclSets: structure dependency cycle at '{structKey}'")
                exit(warningAndErrorReport())
            stack.add(structKey)
            deps = emptyDeclDeps()
            for var in structVars.get(structKey, list()):
                if var['varTypeKey']:
                    typeDeps = typeInfo(var['varTypeKey'])
                    mergeDeps(deps, typeDeps)
                    if typeDeps['paramDeps'] or typeDeps['localDeps']:
                        deps['localDeps'].add(('type', var['varTypeKey']))
                if var['subStructKey']:
                    structDeps = structInfo(var['subStructKey'], stack)
                    mergeDeps(deps, structDeps)
                    if structDeps['paramDeps'] or structDeps['localDeps']:
                        deps['localDeps'].add(('structure', var['subStructKey']))
                mergeDeps(deps, constantRefDeps(var['arraySizeKey'], set()))
            stack.discard(structKey)
            structMemo[structKey] = deps
            return deps

        # Per-declaration dependency set. declInfo holds only declarations whose
        # closure finds parameter dependence: (declKind, declKey) -> deps/context.
        # The derived flag must agree with the parser's isParameterizable; a
        # disagreement is a generator bug.
        def checkAgreement(kind, key, stored, deps):
            flagged = bool(deps['paramDeps']) or bool(deps['localDeps'])
            if flagged != bool(stored):
                printError(f"Generator bug in deriveParameterizedDeclSets: {kind} '{key}' has "
                           f"isParameterizable={bool(stored)} but the derived parameter "
                           f"dependency disagrees (paramDeps={sorted(deps['paramDeps'])}, "
                           f"localDeps={sorted(deps['localDeps'])})")
                exit(warningAndErrorReport())
            return flagged

        declInfo = dict()
        for constKey, row in self.flatData['constants'].items():
            if not row['isParameterizable'] or not row['evalCanonical'] or constKey in backingKeys:
                continue
            deps = constDeclDeps(constKey, set())
            declInfo[('constant', constKey)] = {
                'declKind': 'constant',
                'declKey': constKey,
                'context': row['_context'],
                'paramDeps': deps['paramDeps'],
                'localDeps': deps['localDeps'],
            }
        for typeKey, row in types.items():
            deps = typeInfo(typeKey)
            if checkAgreement('type', typeKey, row['isParameterizable'], deps):
                declInfo[('type', typeKey)] = {
                    'declKind': 'type',
                    'declKey': typeKey,
                    'context': row['_context'],
                    'paramDeps': deps['paramDeps'],
                    'localDeps': deps['localDeps'],
                }
        for structKey, row in structures.items():
            deps = structInfo(structKey, set())
            if checkAgreement('structure', structKey, row['isParameterizable'], deps):
                declInfo[('structure', structKey)] = {
                    'declKind': 'structure',
                    'declKey': structKey,
                    'context': row['_context'],
                    'paramDeps': deps['paramDeps'],
                    'localDeps': deps['localDeps'],
                }

        # Per-block selection. A declaration can be emitted only when it is
        # visible from the block and its full backing-parameter closure is
        # supplied by that block's params; any local declaration dependencies are
        # recursively selected first.
        # Record each block's params as the backing ipParameters constant key
        # resolved through the block's include chain, not the param's
        # declaring-file qualification. A block may consume an ipParameters
        # constant defined in an included IP-root file (e.g. a testbench
        # stimulus/sink instanced against the IP); the backing parameter it
        # carries is that same constant. Endpoint backing and per-declaration
        # selection both compare against interface paramDeps, which are the
        # constants' own keys, so resolved constant identity is the correct
        # basis for comparison rather than the file the param was declared in.
        blockParams = dict()
        for row in self.flatData['blocksparams'].values():
            (constInfo, _constContext) = self.lookupInScope(
                'constants', row['_context'], row['param'])
            if constInfo is None:
                # A param with no backing constant is reported by
                # _post_validateBlockParamBacking; nothing to record here.
                continue
            blockParams.setdefault(row['blockKey'], set()).add(constInfo['constantKey'])
        # blocks.isParameterizable is computed by calcBlockConfigInfo(), which
        # also mirrors it back onto the in-memory block rows, so read it from
        # there rather than re-querying the DB.
        blockIsParameterizable = {block['blockKey']: bool(block['isParameterizable'])
                                  for block in self.flatData['blocks'].values()}

        # Validate parameterized-interface connection endpoints while the
        # per-declaration paramSet is still in memory, so it need not be persisted.
        self._validateParameterizedConnectionEndpoints(declInfo, blockParams, blockIsParameterizable)

        rows = list()
        for block in self.flatData['blocks'].values():
            blockKey = block['blockKey']
            if not blockIsParameterizable[blockKey]:
                continue
            params = blockParams.get(blockKey, set())
            visible = self.yamlContext.get(block['_context'], OrderedDict())
            selected = OrderedDict()

            def selectDecl(declId, visiting):
                info = declInfo[declId]
                if declId in selected:
                    return True
                if info['context'] not in visible:
                    return False
                if not info['paramDeps'] <= params:
                    return False
                if declId in visiting:
                    printError(f"Generator bug in deriveParameterizedDeclSets: declaration dependency cycle at '{declId}'")
                    exit(warningAndErrorReport())
                visiting.add(declId)
                for depId in sorted(info['localDeps']):
                    if depId not in declInfo:
                        return False
                    if not selectDecl(depId, visiting):
                        return False
                visiting.discard(declId)
                selected[declId] = info
                return True

            for declId in declInfo:
                selectDecl(declId, set())
            for orderIndex, info in enumerate(selected.values()):
                rows.append((blockKey, info['declKind'], info['declKey'], orderIndex))

        # Explicit non-schema table: create, bulk insert, then index on blockKey
        # (the block-usage access path). Building the row list in memory and
        # inserting via a single executemany keeps creation cheap; the index is
        # added after the bulk load. getBlockData() queries this directly and
        # joins to types/structures for bodies; it is never loaded into prj.data.
        g.cur.execute("DROP TABLE IF EXISTS blockParameterizedDecls")
        g.cur.execute("CREATE TABLE blockParameterizedDecls "
                      "(blockKey TEXT, declKind TEXT, declKey TEXT, orderIndex INTEGER)")
        g.cur.executemany("INSERT INTO blockParameterizedDecls "
                          "(blockKey, declKind, declKey, orderIndex) VALUES (?, ?, ?, ?)", rows)
        g.cur.execute("CREATE INDEX idx_blockParameterizedDecls_blockKey "
                      "ON blockParameterizedDecls (blockKey)")

    def _validateParameterizedConnectionEndpoints(self, declInfo, blockParams, blockIsParameterizable):
        # A parameterized interface implies both connected endpoints are
        # parameterized. SV sizes a parameterized payload from the owning module's
        # parameters, so an endpoint block that does not itself declare a required
        # backing parameter cannot declare the payload type - the parameter would
        # have to come from a level the block does not own. For every
        # parameterizable connection, each endpoint instance's block must supply
        # the union of backing parameters of the interface's parameterizable
        # payload structures; a shortfall is a fatal error.
        interfaces = self.flatData['interfaces']
        constByKey = {row['constantKey']: row for row in self.flatData['constants'].values()}

        # connectionsends is a nested ('multiple') table, not flat - gather the
        # endpoints per connection from self.data, keyed by connectionKey.
        connEnds = dict()
        for fileRows in self.data.get('connectionsends', dict()).values():
            for end in fileRows.values():
                connEnds.setdefault(end['connectionKey'], list()).append(end)

        errors = False
        for conn in self.flatData['connections'].values():
            if not conn['isParameterizable']:
                continue
            intf = interfaces[conn['interfaceKey']]
            needed = set()
            for structRow in intf.get('structures', dict()).values():
                info = declInfo.get(('structure', structRow['structureKey']))
                if info is not None:
                    needed |= info['paramDeps']
            if not needed:
                continue
            for end in connEnds.get(conn['connectionKey'], list()):
                blockKey = end['instanceTypeKey']
                missing = needed - blockParams.get(blockKey, set())
                if not missing:
                    continue
                missingNames = ', '.join(sorted(constByKey[key]['constant'] for key in missing))
                reason = ('is not parameterized' if not blockIsParameterizable.get(blockKey)
                          else 'does not declare the required parameter(s)')
                printError(f"Parameterized interface '{intf['interface']}' on the connection "
                           f"'{conn['src']}' -> '{conn['dst']}' connects endpoint instance "
                           f"'{end['instance']}' (block '{end['instanceType']}'), which "
                           f"{reason}: missing {missingNames}. A block reached through a "
                           f"parameterized interface must itself carry the backing "
                           f"parameter(s) so the payload is sized in its own module scope.")
                errors = True
        if errors:
            exit(warningAndErrorReport())

    def generateAddressEnums(self):
        self.yamlContext['_global'] = {key: None for key in self.yamlContext}
        # calculate all the enums and types
        typesEnum = dict()
        for group in self.counterGroupControl.get('AddressGroups', []):
            # create a dictionary of all the enums and types for this group
            typesEnum[group] = {'desc': f'Generated type for addressing {group} instances',   'enum': list()}
        for context in self.data['instances']:
            for instance, instData in self.data['instances'][context].items():
                if instData.get('addressGroup', None) is not None:
                    # this block needs an address space
                    group = instData['addressGroup']
                    control = self.counterGroupControl['AddressGroups'][group]
                    typesEnum[group]['enum'].append( { 'enumName': control['enumPrefix'] + instance.upper(), 'desc': instance + ' instance address', 'value': instData['addressID']} )
        #convert the dictionary keys from group to the varType from the addressControl
        for group in typesEnum:
            dataToAdd = {'types': dict()}
            if len(typesEnum[group]['enum']) > 0:
                if 'varTypeContext' in self.counterGroupControl['AddressGroups'][group]:
                    context = self.counterGroupControl['AddressGroups'][group]['varTypeContext']
                    if context not in self.yamlContext:
                        printError(f"In address control file, AddressControl group:{group} specified varTypeContext:{context} which is not a valid context")
                        exit(warningAndErrorReport())
                else:
                    (decoder, context) = self.lookupInScope('instances', '_global', self.counterGroupControl['AddressGroups'][group]['decoderInstance'])
                    if not decoder:
                        printError(f"instances {self.counterGroupControl['AddressGroups'][group]['decoderInstance']} in file _global is unresolved")
                        exit(warningAndErrorReport())
                    if decoder:
                        decoderContainer = self.flatData['blocks'][decoder['containerKey']]
                        context = decoderContainer['_context']
                if context:
                    dataToAdd['types'][ self.counterGroupControl['AddressGroups'][group]['varType'] ] = typesEnum[group].copy()
                    self.processSingleFile(context, sections=dataToAdd)

        # add to the table

        del self.yamlContext['_global']
        # Phase complete; see processYamls() for the rationale.
        self._parserResolver = None

    def saveIncludeFiles(self):
        files = dict()
        if 'fileGeneration' in self.proj:
            if 'fileMap' in self.proj['fileGeneration']:
                self.config.setConfig('FILEMAP', self.proj['fileGeneration']['fileMap'])
                for fileType, fileInfo in self.proj['fileGeneration']['fileMap'].items():
                    mode = fileInfo.get('mode', 'block')
                    if mode == 'context':
                        files[fileType] = fileInfo

        includeFiles = dict()
        config_contexts = self._configHeaderContexts()
        for fileType, fileData in files.items():
            smartInclude = fileData['cond']['smartInclude']
            for include, includeData in self.includeValid.items():
                includeName = self.includeName[include]
                valid = includeData['valid']
                if fileType == 'config':
                    # Config headers are a narrower surface than ordinary
                    # context includes. A YAML file with only fixed
                    # structures/types still needs Includes.{h,cppm}, but it
                    # should not grow an empty *Config.h.
                    valid = include in config_contexts
                if not(smartInclude and not valid):
                    # Resolve under the layout of the project that owns this
                    # context (its defining file). include is the context's
                    # file key, keyed identically to contextOwningProject.
                    layout = self.projectLayout[self.contextOwningProject[include]]
                    fileName = expandNewModulePath(fileData, includeData['dir'], includeName, includeName, layout, missingDirOk=True)
                    # Sibling header basename, derived from this file type's own
                    # ext map (filespec). A source artifact #includes its paired
                    # header by this name, so templates never reconstruct the
                    # header from the source filename.
                    siblingHeaderName = None
                    if 'hdr' in fileData['ext']:
                        siblingHeaderName = os.path.basename(fileName + "." + fileData['ext']['hdr'])
                    for ext in fileData['ext']:
                        fileNameExt = fileName + "." + fileData['ext'][ext]
                        baseName = os.path.basename(fileNameExt)
                        expandedType = fileType + "_" + ext
                        if not (os.path.exists(fileNameExt)):
                            printWarning(f"File {fileNameExt} does not exist. run arch2code.py with --newmodule option")
                        entry = {'baseName': baseName, 'fileName': fileNameExt}
                        if ext == 'src' and siblingHeaderName is not None:
                            entry['siblingHeaderName'] = siblingHeaderName
                        includeFiles.setdefault(expandedType, {})[include] = entry

        self.config.setConfig('INCLUDEFILES', includeFiles)

    def _configHeaderContexts(self):
        contexts = set()
        # Every context that declares a parameterizable constant emits a
        # <context>DefaultConfig struct.
        for const_row in self.flatData['constants'].values():
            if const_row['isParameterizable'] and const_row['_context']:
                contexts.add(const_row['_context'])

        # Blocks with own params still emit (or share) per-variant Config
        # structs when the project binds an instance of the block. The header
        # is keyed on the block's canonical config context, where its Config
        # struct is emitted, not its declaring context. configContext is
        # mirrored onto the block rows by calcBlockConfigInfo earlier in this
        # pass.
        instanced = {row['instanceTypeKey'] for row in self.flatData['instances'].values()}
        blocks_with_params = {row['blockKey'] for row in self.flatData['blocksparams'].values()}
        block_by_key = {row['blockKey']: row for row in self.flatData['blocks'].values()}
        for block_key in instanced & blocks_with_params:
            config_context = block_by_key[block_key]['configContext']
            if config_context:
                contexts.add(config_context)
        return contexts

    _PROJECT_ADDRESS_GROUP_FIELDS = {'varType': None, 'enumPrefix': None}
    _PROJECT_ADDRESS_OBJECT_FIELDS = {'alignment': None,
                                      'sizeRoundUpPowerOf2': None,
                                      'sortDescending': None}

    def _gateYamlFormat(self):
        """Stop the build unless the project is migrated to the current YAML
        authoring format.

        The sentinel is a single top-level `yamlFormat:` field in the user
        project.yaml. Its absence marks a pre-migration (legacy) project. The
        legacy addressControl loader and Python-syntax eval acceptance are
        already removed, so an un-migrated project must be stopped here, before
        any address or eval processing, with an actionable remediation command
        rather than failing obscurely downstream.
        """
        yamlFormat = self.proj.get('yamlFormat')
        if yamlFormat == CURRENT_YAML_FORMAT:
            return
        if yamlFormat is None:
            printError(
                f"Project '{self.projFile}' is not migrated to yamlFormat: "
                f"{CURRENT_YAML_FORMAT}.\n"
                f"       Run the migration, then rebuild:\n\n"
                f"           make migrate\n"
                f"           make clean && make gen\n"
            )
        else:
            printError(
                f"Project '{self.projFile}' declares yamlFormat: {yamlFormat}, "
                f"but this generator expects yamlFormat: {CURRENT_YAML_FORMAT}. "
                f"Update the project to the current authoring format."
            )
        exit(warningAndErrorReport())

    def loadProjectAddressPolicy(self):
        """Normalize project.yaml instanceGroups:/addressObjects: into the
        counter-state and persisted ADDRESS_CONFIG blob.

        project.yaml is the sole source for these sections; they populate
        the same state the address allocator and firmware-header generator
        consume.
        """
        projInstanceGroups = self.proj.get('instanceGroups')
        projAddressObjects = self.proj.get('addressObjects')
        if projInstanceGroups is None and projAddressObjects is None:
            return

        addressConfig = (self.addressControl
                         if isinstance(self.addressControl, dict)
                         else OrderedDict())

        if projInstanceGroups is not None:
            self._mergeProjectAddressGroupSection(
                'InstanceGroups', projInstanceGroups,
                self._PROJECT_ADDRESS_GROUP_FIELDS,
                addressConfig,
            )

        if projAddressObjects is not None:
            self._mergeProjectAddressObjectSection(
                'AddressObjects', projAddressObjects,
                self._PROJECT_ADDRESS_OBJECT_FIELDS,
                addressConfig,
            )

        self.addressControl = addressConfig

    def _validateProjectAddressRows(self, sectionLabel, rows, allowedFields,
                                    rowKindLabel):
        """Reject rows that are not mappings or carry unknown fields."""
        ok = True
        if not isinstance(rows, dict):
            self.logError(
                f"In {self.projFile}, section '{sectionLabel}:' must be "
                f"a mapping of {rowKindLabel} -> "
                f"{sorted(allowedFields)}."
            )
            return False
        for name, settings in rows.items():
            if not isinstance(settings, dict):
                self.logError(
                    f"In {self.projFile}, {sectionLabel} {rowKindLabel} "
                    f"'{name}' must be a mapping of "
                    f"{sorted(allowedFields)}."
                )
                ok = False
                continue
            for setting in settings:
                if setting not in allowedFields:
                    line = (settings.lc.line + 1
                            if hasattr(settings, 'lc') and settings.lc is not None
                            else '?')
                    self.logError(
                        f"In {self.projFile}:{line}, {sectionLabel} "
                        f"{rowKindLabel} '{name}' has unknown parameter "
                        f"'{setting}'. Allowed: {sorted(allowedFields)}"
                    )
                    ok = False
        return ok

    def _mergeProjectAddressGroupSection(self, sectionKey, projRows,
                                         allowedFields, addressConfig):
        """Normalize a project.yaml 'group'-shaped section (today only
        instanceGroups:) into the counter-state and ADDRESS_CONFIG entry."""
        if not self._validateProjectAddressRows(
                'instanceGroups', projRows, allowedFields, 'group'):
            return

        addressConfig[sectionKey] = projRows
        self.counterGroup[sectionKey] = OrderedDict()
        self.counterGroupControl[sectionKey] = OrderedDict()
        self.counterData[sectionKey] = OrderedDict()
        for group, settings in projRows.items():
            self.counterGroup[sectionKey][group] = 0
            self.counterGroupControl[sectionKey][group] = settings
            self.counterData[sectionKey][group] = OrderedDict()

    def _mergeProjectAddressObjectSection(self, sectionKey, projRows,
                                          allowedFields, addressConfig):
        """Normalize project.yaml addressObjects: into the AddressObjects
        ADDRESS_CONFIG entry and in-memory state."""
        if not self._validateProjectAddressRows(
                'addressObjects', projRows, allowedFields, 'object'):
            return

        addressConfig[sectionKey] = projRows
        self.addressObjects = projRows

    def validateDeclaredPorts(self, blocks_flat, instances_flat, interfaces_flat,
                              connections_flat, connection_maps_flat,
                              memory_connections_flat, register_connections_flat,
                              memories_flat, registers_flat):
        # Keep this create-time so bad YAML fails while building the DB, not
        # later when a generator happens to request a block view.
        instances_by_type = dict()
        for instKey, instRow in instances_flat.items():
            instances_by_type.setdefault(
                instRow['instanceTypeKey'], set()).add(instKey)

        def _addInferred(inferred, portName, sourceType, row, interfaceKey='',
                         direction=''):
            if not portName:
                return
            interfaceName = None
            if interfaceKey != '':
                interfaceName = interfaces_flat[interfaceKey]['interface']
            inferred.setdefault(portName, {
                'sourceType': sourceType,
                'interface': interfaceName,
                'interfaceKey': interfaceKey,
                'direction': direction,
                '_context': row['_context'],
            })

        regMapBlock = {'rw': 'dst', 'ro': 'src', 'ext': 'dst', 'memory': 'dst'}

        for blockKey, blockRow in blocks_flat.items():
            if 'ports' not in blockRow:
                continue
            declared = blockRow['ports']

            inferred = dict()
            qual_block_instances = instances_by_type.get(blockKey, set())

            # An exported/library block — declared with explicit ports: but never
            # instantiated in its owning project (e.g. a reusable block a
            # definitions-only project exports for other projects to instantiate) —
            # has its declared ports produced at the consumer's instantiation site,
            # not here. Every reconciliation below validates declared ports against
            # bindings inferred locally (all filtered by qual_block_instances), which
            # are empty for an uninstantiated block. Scope this validation to blocks
            # instantiated in this project; an unproduced declared port on an
            # uninstantiated block is not an error.
            if not qual_block_instances:
                continue

            for _connKey, conn in connections_flat.items():
                interfaceKey = conn['interfaceKey']
                for endRow in conn['ends'].values():
                    if endRow['instanceKey'] in qual_block_instances:
                        _addInferred(
                            inferred,
                            endRow['portName'],
                            'connections',
                            conn,
                            interfaceKey,
                            endRow['direction'],
                        )

            for _cmKey, connMap in connection_maps_flat.items():
                if connMap['instanceKey'] in qual_block_instances:
                    _addInferred(
                        inferred,
                        connMap['instancePortName'],
                        'connectionMaps',
                        connMap,
                        connMap['interfaceKey'],
                        connMap['direction'],
                    )
                # A connectionMap also declares a parent-boundary port on
                # `block:`. When the block currently being validated is
                # the parent of this connectionMap, the connectionMap
                # contributes the boundary port name to inferred.
                if connMap.get('blockKey') == blockKey and connMap.get('portName'):
                    _addInferred(
                        inferred,
                        connMap['portName'],
                        'connectionMaps',
                        connMap,
                        connMap['interfaceKey'],
                        connMap['direction'],
                    )

            for _memConnKey, memConn in memory_connections_flat.items():
                if memConn['instanceKey'] not in qual_block_instances:
                    continue
                _addInferred(
                    inferred,
                    memConn['memory'],
                    'memories',
                    memConn,
                    '',
                    'src',
                )

            for _regConnKey, regConn in register_connections_flat.items():
                if regConn['instanceKey'] not in qual_block_instances:
                    continue
                regInfo = registers_flat[regConn['registerBlockKey']]
                regType = regInfo['regType']
                _addInferred(
                    inferred,
                    regConn['register'],
                    'registers',
                    regConn,
                    '',
                    regMapBlock[regType],
                )

            block = blockRow['block']
            declaringContext = blockRow['_context']

            for portName, portRow in declared.items():
                portContext = portRow['_context']
                if portName not in inferred:
                    printError(
                        f"Block {block} declares port '{portName}' in ports: "
                        f"(file {portContext}) but no connection, connectionMap, "
                        f"register, or memory entry produces port '{portName}'.")
                    exit(warningAndErrorReport())

                portEntry = inferred[portName]
                declaredIfName = portRow['interface']
                inferredIfName = portEntry['interface']
                if (declaredIfName != inferredIfName
                        and portEntry['sourceType'] not in (
                            'connections', 'connectionMaps')):
                    printError(
                        f"Block {block} port '{portName}' declares interface "
                        f"'{declaredIfName}' in ports: (file {portContext}) but is "
                        f"bound by {portEntry['sourceType']} (file "
                        f"{portEntry['_context']}), which does not provide a "
                        f"connection interface for cross-interface validation.")
                    exit(warningAndErrorReport())

                declaredDir = portRow['direction']
                inferredDir = portEntry['direction']
                if declaredDir and inferredDir and declaredDir != inferredDir:
                    printError(
                        f"Block {block} port '{portName}' declares direction "
                        f"'{declaredDir}' in ports: (file {portContext}) but is "
                        f"bound with direction '{inferredDir}' by "
                        f"{portEntry['sourceType']} (file "
                        f"{portEntry['_context']}).")
                    exit(warningAndErrorReport())

            # ports: and registerPorts: are independent declarations. A
            # registerPorts-owned name is allowed to be absent from ports:,
            # and synthesized global binds are ignored for completeness.
            # A connectionMap whose parent block is this block also acts
            # as a boundary-port declaration — when the post-parse pass
            # bridges an inherited register-bus port through a container,
            # it emits a connectionMap with `block:` set to that
            # container; the connectionMap is the authoritative
            # declaration of that boundary port and satisfies partial
            # ports: even when the user did not enumerate it.
            registerPortNames = set((blockRow.get('registerPorts') or {}).keys())
            connectionMapPortNames = set()
            for _cmKey, connMap in connection_maps_flat.items():
                if connMap.get('blockKey') == blockKey and connMap.get('portName'):
                    connectionMapPortNames.add(connMap['portName'])
            missing = set()
            for portName in (set(inferred.keys()) - set(declared.keys())):
                if inferred[portName]['_context'] == '_global':
                    continue
                if portName in registerPortNames:
                    continue
                if portName in connectionMapPortNames:
                    continue
                missing.add(portName)
            if missing:
                for portName in sorted(missing):
                    portEntry = inferred[portName]
                    inferredIfName = portEntry['interface'] or '<unknown>'
                    inferredDir = portEntry['direction'] or '<unknown>'
                    printError(
                        f"Block {block} partial ports: declaration in "
                        f"{declaringContext} omits port '{portName}' (interface "
                        f"{inferredIfName}, direction {inferredDir}), which is "
                        f"implied by {portEntry['sourceType']} at "
                        f"{portEntry['_context']}. Either add '{portName}: "
                        f"{{ interface: {inferredIfName}, direction: "
                        f"{inferredDir} }}' to the ports: map, or remove the "
                        f"partial declaration to fall back to top-down inference.")
                exit(warningAndErrorReport())

    def validateRtlHierarchy(self, blocks_flat, instances_flat):
        for instName, instRow in instances_flat.items():
            parentBlockKey = instRow.get('containerKey') or ''
            if parentBlockKey == '_topInstance':
                continue
            parentBlock = blocks_flat.get(parentBlockKey)
            if not parentBlock or not bool(parentBlock.get('hasRtl', True)):
                continue

            childBlockKey = instRow.get('instanceTypeKey') or ''
            childBlock = blocks_flat.get(childBlockKey)
            if not childBlock or bool(childBlock.get('hasRtl', True)):
                continue

            instanceName = instRow.get('instance') or instName
            parentName = parentBlock.get('block') or parentBlockKey
            childName = childBlock.get('block') or childBlockKey
            instContext = instRow['_context']
            line = instRow.get('lc').line + 1 if instRow.get('lc') else '?'
            printError(
                f"In {instContext}:{line}, RTL block '{parentName}' contains "
                f"instance '{instanceName}' of block '{childName}', but "
                f"'{childName}' has hasRtl: false. RTL hierarchy requires every "
                f"subblock of an RTL block to have an RTL implementation. Set "
                f"blocks.{childName}.hasRtl: true, or set "
                f"blocks.{parentName}.hasRtl: false if the parent is model-only.")
            exit(warningAndErrorReport())

    def variantValueBindings(self, blockKey, variant):
        if not blockKey:
            return dict()
        resolver = ValueResolver(self)
        bindings = dict()
        g.cur.execute(
            "SELECT p.param, p.blockParamKey, b.paramKey, p.value, p.valueKey "
            "FROM parametersvariantsparams p "
            "JOIN blocksparams b "
            "ON p.blockParamKey = b.blockparamKey "
            "AND p.blockKey = b.blockKey "
            "WHERE p.blockKey = ? AND p.variant = ?",
            (blockKey, variant or ''),
        )
        for row in g.cur.fetchall():
            raw = row['valueKey'] or row['value']
            value = resolver.value(raw)
            bindings[row['param']] = value
            bindings[row['blockParamKey']] = value
            bindings[row['paramKey']] = value
        return bindings

    def _structureRowsForInterface(self, interfaceRow):
        return (interfaceRow.get('structures') or {}).values()

    def checkInterfacePair(self, parentIface, childIface, childBlockKey,
                           childVariant, locationStr, parentContext,
                           childContext, parentBlockKey='', parentVariant=''):
        """Validate that two qualified interfaces share the same packed form."""
        if parentIface['interfaceKey'] == childIface['interfaceKey']:
            return

        parentName = parentIface['interface']
        childName = childIface['interface']
        parentProto = parentIface['interfaceType']
        childProto = childIface['interfaceType']
        if parentProto != childProto:
            printError(
                f"{locationStr}: cross-interface bind requires the same "
                f"interface meta-protocol on both ends, but parent "
                f"interface {parentName} has interfaceType "
                f"'{parentProto}' (file {parentContext}) while child "
                f"interface {childName} has interfaceType "
                f"'{childProto}' (file {childContext}). Use a protocol "
                f"changer block when binding different register-bus "
                f"meta-protocols.")
            exit(warningAndErrorReport())

        parentStructs = self._structureRowsForInterface(parentIface)
        childStructs = self._structureRowsForInterface(childIface)
        parentByType = {s['structureType']: s for s in parentStructs}
        childByType = {s['structureType']: s for s in childStructs}
        allTypes = set(parentByType.keys()) | set(childByType.keys())
        anyError = False
        for stype in sorted(allTypes):
            if stype not in parentByType:
                printError(
                    f"{locationStr}: cross-interface bind requires both "
                    f"interfaces to carry the same structureTypes, but "
                    f"parent interface {parentName} (file "
                    f"{parentContext}) is missing structureType "
                    f"'{stype}' that child interface {childName} (file "
                    f"{childContext}) carries.")
                anyError = True
                continue
            if stype not in childByType:
                printError(
                    f"{locationStr}: cross-interface bind requires both "
                    f"interfaces to carry the same structureTypes, but "
                    f"child interface {childName} (file {childContext}) "
                    f"is missing structureType '{stype}' that parent "
                    f"interface {parentName} (file {parentContext}) "
                    f"carries.")
                anyError = True
                continue
        if anyError:
            exit(warningAndErrorReport())

        parentResolver = ValueResolver(
            self,
            values=self.variantValueBindings(parentBlockKey, parentVariant or ''),
            context=parentContext,
        )
        childResolver = ValueResolver(
            self,
            values=self.variantValueBindings(childBlockKey, childVariant or ''),
            context=childContext,
        )
        for stype in sorted(allTypes):
            parentStructKey = parentByType[stype]['structureKey']
            childStructKey = childByType[stype]['structureKey']
            parentStruct = parentByType[stype]['structure']
            childStruct = childByType[stype]['structure']
            parentFields = parentResolver.structPackedFields(parentStructKey)
            childFields = childResolver.structPackedFields(childStructKey)
            if len(parentFields) != len(childFields):
                printError(
                    f"{locationStr}: cross-interface bind requires the "
                    f"same field count in each paired structure, but "
                    f"{parentName}/{parentStruct} has "
                    f"{len(parentFields)} fields (file {parentContext}) "
                    f"while {childName}/{childStruct} has "
                    f"{len(childFields)} fields (file {childContext}).")
                anyError = True
                continue
            for (pname, pwidth, poff), (cname, cwidth, coff) in zip(
                    parentFields, childFields):
                if pname != cname:
                    printError(
                        f"{locationStr}: cross-interface bind requires "
                        f"matching field names in declared order, but "
                        f"field at offset {poff} in "
                        f"{parentName}/{parentStruct} is named "
                        f"'{pname}' (file {parentContext}) while the "
                        f"corresponding field at offset {coff} in "
                        f"{childName}/{childStruct} is named '{cname}' "
                        f"(file {childContext}).")
                    anyError = True
                    continue
                if pwidth != cwidth:
                    printError(
                        f"{locationStr}: cross-interface bind requires "
                        f"per-field _bitWidth to agree, but field "
                        f"'{pname}' of {parentName}/{parentStruct} has "
                        f"_bitWidth {pwidth} (file {parentContext}) "
                        f"while field '{cname}' of "
                        f"{childName}/{childStruct} has _bitWidth "
                        f"{cwidth} (file {childContext}). Adjust one "
                        f"side so per-field _bitWidth agrees, or split "
                        f"the connection.")
                    anyError = True
                    continue
                if poff != coff:
                    printError(
                        f"{locationStr}: cross-interface bind requires "
                        f"matching bit offsets in declared order, but "
                        f"field '{pname}' of {parentName}/{parentStruct} "
                        f"sits at bit offset {poff} (file "
                        f"{parentContext}) while field '{cname}' of "
                        f"{childName}/{childStruct} sits at bit offset "
                        f"{coff} (file {childContext}).")
                    anyError = True
        if anyError:
            exit(warningAndErrorReport())

    def validatePorts(self):
        # Cross-interface bind barrier: every connection end or connectionMap
        # whose declared interface differs from the child block's bottom-up
        # `ports:` declaration is checked for packed-form compatibility under
        # the bound variant. The check is purely a gate; it writes nothing back
        # to the DB and persists no state. The projectOpen consumer recomputes
        # the cheap cross-interface predicate from the same persisted data.
        #
        # Packed-form compatibility requires:
        #   1. Same interface meta-protocol (interfaceType).
        #   2. Same `structures` list paired by structureType.
        #   3. For each paired structure: same field count, same field
        #      order and names, exact per-field _bitWidth under the
        #      bound variant, exact bit offsets.
        #
        # Synthesised binds (carrying _context == '_global') are generated
        # internally and are exempt from user-authored compatibility checks.

        blocks_flat = self.flatData['blocks']
        instances_flat = self.flatData['instances']
        interfaces_flat = self.flatData['interfaces']
        connections_flat = self.flatData['connections']
        connection_maps_flat = self.flatData['connectionMaps']
        memory_connections_flat = self.flatData['memoryConnections']
        register_connections_flat = self.flatData['registerConnections']
        memories_flat = self.flatData['memories']
        registers_flat = self.flatData['registers']

        self.validateDeclaredPorts(
            blocks_flat,
            instances_flat,
            interfaces_flat,
            connections_flat,
            connection_maps_flat,
            memory_connections_flat,
            register_connections_flat,
            memories_flat,
            registers_flat,
        )
        self.validateRtlHierarchy(blocks_flat, instances_flat)

        def _blockHasOwnParams(blockRow):
            return bool(blockRow.get('params'))

        def _connectionBinding(conn):
            """Return the (blockKey, variant) binding used to resolve the
            connection-side packed form. This mirrors channel type derivation:
            prefer a leaf parameterizable end, with dst winning when more than
            one leaf participates."""
            leaf_choice = None
            transit_choice = None
            for endRow in conn['ends'].values():
                instRow = instances_flat[endRow['instanceKey']]
                blockKey = instRow['instanceTypeKey']
                blockRow = blocks_flat[blockKey]
                choice = (blockKey, instRow['variant'] or '')
                if _blockHasOwnParams(blockRow):
                    if leaf_choice is None or endRow['direction'] == 'dst':
                        leaf_choice = choice
                elif blockRow['isParameterizable'] and transit_choice is None:
                    transit_choice = choice
            return leaf_choice or transit_choice or ('', '')

        def _mapParentBinding(cm):
            """Best-effort binding for a connectionMap parent interface. The
            parent side is often non-parameterized; when the mapped block has
            its own params, using its binding matches the generated channel
            type for the supported destination-side bridge."""
            instRow = instances_flat[cm['instanceKey']]
            blockKey = instRow['instanceTypeKey']
            blockRow = blocks_flat[blockKey]
            if not _blockHasOwnParams(blockRow):
                return ('', '')
            return (blockKey, instRow['variant'] or '')

        # ------------------------------------------------------------
        # Iterate connections. Each end may be a cross-interface bind.
        # ------------------------------------------------------------
        for connName, conn in connections_flat.items():
            # Skip synthesised entries.
            connContext = conn['_context']
            if connContext == '_global':
                continue
            parentIfaceKey = conn['interfaceKey']
            for _endDir, endRow in conn['ends'].items():
                instanceKey = endRow['instanceKey']
                instRow = instances_flat[instanceKey]
                instTypeKey = instRow['instanceTypeKey']
                blockRow = blocks_flat[instTypeKey]
                portName = endRow['portName']
                # registerPorts: is part of the block's declared-port
                # surface. A routed leaf's register-bus ingress is declared
                # there rather than in ports:, so cross-interface checking
                # consults the union of both maps.
                portEntry = (blockRow.get('ports') or {}).get(portName)
                isRegisterBus = False
                if not portEntry:
                    portEntry = (blockRow.get('registerPorts') or {}).get(portName)
                    isRegisterBus = portEntry is not None
                if not portEntry:
                    # No bottom-up declaration; top-down inference
                    # governs and there is no cross-interface bind
                    # to check.
                    continue
                portIface = portEntry['interface']
                parentIfaceRow = interfaces_flat[parentIfaceKey]
                parentIfaceName = parentIfaceRow['interface']
                if portIface == parentIfaceName:
                    # Names agree; not a cross-interface bind.
                    continue
                childIfaceKey = portEntry['interfaceKey']
                childContext = interfaces_flat[childIfaceKey]['_context']
                parentContext = parentIfaceRow['_context']
                childVariant = instRow['variant'] or ''
                parentBlockKey, parentVariant = _connectionBinding(conn)
                if isRegisterBus:
                    # The synthesised register-bus connection links a router
                    # to the routed leaf. Name both instances and the
                    # registerPorts: row, and resolve the parent side from the
                    # router end rather than the leaf-preferring channel rule.
                    otherEnd = next(
                        (e for e in conn['ends'].values()
                         if e['instanceKey'] != instanceKey), None)
                    if otherEnd is not None:
                        otherInst = instances_flat[otherEnd['instanceKey']]
                        parentBlockKey = otherInst['instanceTypeKey']
                        parentVariant = otherInst['variant'] or ''
                        srcInstance = otherEnd['instance']
                    else:
                        srcInstance = instRow['instance']
                    locationStr = (
                        f"Register-bus dispatch from router "
                        f"'{srcInstance}' to leaf instance "
                        f"'{instRow['instance']}' (registerPorts: row "
                        f"'{portName}')")
                else:
                    locationStr = (
                        f"Block {blockRow['block']} connection "
                        f"'{connName}' (file {connContext}) binds external "
                        f"interface {parentIfaceName} to child "
                        f"{instRow['instance']}.{portName} declared as "
                        f"{portIface} (file {blockRow['_context']})")
                self.checkInterfacePair(
                    parentIfaceRow, interfaces_flat[childIfaceKey],
                    instTypeKey,
                    childVariant, locationStr, parentContext,
                    childContext, parentBlockKey, parentVariant)

        # ------------------------------------------------------------
        # Iterate connectionMaps. The child port is the local end.
        # ------------------------------------------------------------
        for cmName, cm in connection_maps_flat.items():
            cmContext = cm['_context']
            if cmContext == '_global':
                # Synthesised maps.
                continue
            parentIfaceKey = cm['interfaceKey']
            instanceKey = cm['instanceKey']
            instRow = instances_flat[instanceKey]
            instTypeKey = instRow['instanceTypeKey']
            blockRow = blocks_flat[instTypeKey]
            declaredPorts = blockRow.get('ports') or {}
            instPortName = cm['instancePortName']
            portEntry = declaredPorts.get(instPortName)
            if not portEntry:
                continue
            portIface = portEntry['interface']
            parentIfaceRow = interfaces_flat[parentIfaceKey]
            parentIfaceName = parentIfaceRow['interface']
            if portIface == parentIfaceName:
                continue
            childIfaceKey = portEntry['interfaceKey']
            childContext = interfaces_flat[childIfaceKey]['_context']
            parentContext = parentIfaceRow['_context']
            childVariant = instRow['variant'] or ''
            locationStr = (
                f"Block {cm['block']} connectionMap '{cmName}' "
                f"(file {cmContext}) binds external interface "
                f"{parentIfaceName} to child "
                f"{instRow['instance']}.{instPortName} declared as "
                f"{portIface} (file {blockRow['_context']})")
            parentBlockKey, parentVariant = _mapParentBinding(cm)
            self.checkInterfacePair(
                parentIfaceRow, interfaces_flat[childIfaceKey],
                instTypeKey,
                childVariant, locationStr, parentContext,
                childContext, parentBlockKey, parentVariant)

    def processYamls(self):
        # main outer loop for processing
        # to avoid recusion maintain dicts of processed and toProcess
        processed = dict()
        toProcess = self.yamlDependancies.copy() # initialize with the dependencies
        nextProcess = dict()
        # we need to detect circular dependencies. We do this by detecting if we did any work
        didWork = False

        # we loop through everything that needs to be processed, and process anything that has all its dependencies met
        while toProcess:
            didWork = False
            for myYaml, dep in toProcess.items():
                if not dep:
                    # if there are no dependancies, its always safe to process
                    if myYaml in self.systemFiles:
                        # System files go into special _a2csystem context
                        if '_a2csystem' not in self.yamlContext:
                            self.yamlContext['_a2csystem'] = OrderedDict()
                        self.yamlContext['_a2csystem'][myYaml] = None
                        self.processSingleFile(myYaml, contextOverride='_a2csystem')
                    else:
                        self.yamlContext[myYaml] = OrderedDict({myYaml: None})
                        self.processSingleFile(myYaml)
                    processed[myYaml] = None
                    didWork = True
                else:
                    # we have dependencies, need to check if all dependancies are satisfied
                    allDep = True
                    # loop through all the dependencies
                    for f in dep:
                        if f not in processed:
                            # an unmet dependancy, so put this item into the do over list
                            nextProcess[myYaml] = dep
                            allDep = False
                            # no need for additional dependency checks
                            break
                        else:
                            #maybe should delete met dependancies...
                            if myYaml not in self.yamlContext:
                                # add the file itself to its own context
                                self.yamlContext[myYaml] = OrderedDict({myYaml: None})
                            self.yamlContext[myYaml][f] = None
                            # if performance of this is slow, we might want to fix later
                            self.yamlContext[myYaml].update(OrderedDict.fromkeys(self.yamlDependancies[f], None))
                    # exited the loop because everything is checked or we found an unmet dependency
                    if allDep:
                        # yay
                        self.processSingleFile(myYaml)
                        processed[myYaml] = None
                        didWork = True
            toProcess = nextProcess.copy()
            nextProcess = dict()
            if toProcess and not didWork:
                printWarning("Files to process")
                printWarning(toProcess)
                printWarning("files not processed")
                printWarning(processed)
                printError("Circular include dependancy detected")
                exit(warningAndErrorReport())
            if self.errorState:
                exit(warningAndErrorReport())
        g.db.commit()
        # Phase complete; null the parse-time resolver so any post-parse
        # caller that reaches through self._parserResolver AttributeError's
        # at the call site. Post-parse code that needs a resolver should
        # construct its own (see calcAddresses for the pattern).
        self._parserResolver = None

    # process a single previously read file or provided standalone data
    def processSingleFile(self, yamlFile, sections=None, contextOverride=None):
        # loop through the sections and process the section
        if sections is None:
            printIfDebug(f"Processing yaml file {yamlFile}")
            sections = self.yamlRaw[yamlFile]
        # Use contextOverride if provided (for system files in _a2csystem context)
        contextFile = contextOverride if contextOverride else yamlFile
        self._parserResolver = ValueResolver(self, context=contextFile)
        if not sections:
            return
        if "blockDir" in sections:
            self.yamlDir = sections["blockDir"]
        else:
            yamlDir = os.path.dirname(yamlFile)
            if layoutConfig['mode'] == 'hierarchical':
                # hierarchical: a block's authored YAML lives in <node>/<yaml>/,
                # and its generated functional segments are created beside that
                # yaml/ dir. The decomposition anchor is therefore the node
                # directory (the parent of the yaml/ dir), made absolute so the
                # relative functional segment names join onto it at emit time.
                self.yamlDir = os.path.dirname(os.path.abspath(yamlDir))
            else:
                # functional: the object dir is relative to a yaml base which the
                # seam (expandNewModulePath) re-roots under that project's
                # $root/<segment>. When the object's defining context is owned by a
                # referenced CHILD project, a root-relative dir is wrong: the seam
                # would compose the child's own segment with a root-relative prefix.
                # Re-root the dir under the OWNING child's yaml base so the child's
                # segment composes with a child-base-relative dir. Root-owned and
                # system/special contexts own no child base and keep the legacy
                # root-relative value, so monolithic projects are byte-identical.
                self.yamlDir = yamlDir
                if contextFile not in self.specialContexts:
                    owner = self.contextOwningProject[contextFile]
                    if owner in self.childProjectRaw:
                        owningBase = self.childProjectRaw[owner]['projectFileDir']
                        self.yamlDir = os.path.dirname(
                            os.path.relpath(os.path.abspath(yamlFile), owningBase))
        if yamlFile not in self.includeValid and yamlFile not in self.specialContexts:
            # check if this is a nested project file
            if 'addressControl' not in sections:
                self.includeValid[yamlFile] = {"dir": self.yamlDir, "valid": False}
        # we are going to go through every section of the input yaml file and process it
        for section, sectData in sections.items():
            if section in self.schema.data['mapto']:
                section = self.schema.data['mapto'][section]
            # some sections need to be ignored (eg in case this is a nested project file)
            if section not in self.ignoreSections:
                # custom sections are checked first - they may not have a schema entry of their own
                # (e.g. ipParameters delegates to the schemas of its sub-sections)
                if section in self.customSections:
                    funct = '_process_'+ section
                    # getattr is used to call the function specified in the string funct in the self object
                    getattr(self, funct)(sectData, contextFile)
                elif (section in self.schema.data['schema']):
                    self.processSection(section, sectData, contextFile)
                else:
                    printError(f"Unknown section: {section} found in {yamlFile}:{sectData.lc.line}")
                    exit(warningAndErrorReport())
                if section in self.includeSections:
                    self.includeValid[yamlFile]["valid"] = True

    # loop through section handling all items for simple and inbetween sections
    def processSection(self, section, data, yamlFile):
        # print(f'Processing section {section} in {yamlFile}:{data.lc.line}')
        # create the context specific data holder for this section
        # during data parsing all data is held in context form to allow dependency checking
        if yamlFile not in self.data[section]:
            self.data[section][yamlFile] = OrderedDict()
        # some sections manage data using a combo key made up of other fields
        comboKey = self.schema.data['comboKey'].get(section, None)
        if comboKey:
            comboKeyName = self.schema.data['key'][section]
        # data input can be lists or dicts in the yaml
        isList = isinstance(data, list)
        if section == 'parameters':
            pass
        # for a given section, loop through all the items and process each item
        # note that this can be dict or list
        for loopitem in data:
            if comboKey is None:
                if isList:
                    # for list case the key is one of the data items
                    itemkey = loopitem[self.schema.data['key'][section]]
                else:
                    # for dict its the anchor of the data items ie loopitem
                    itemkey = loopitem
            else:
                # comboKey can only be handled later after other fields have been parsed
                itemkey = "" # will be filled out during parsing

            if isList:
                item = loopitem
            else:
                item = data[loopitem]
            if yamlFile in self.specialContexts:
                yamlFileOverride = item.get('_yamlFileOverride', yamlFile)
                if yamlFileOverride not in self.data[section]:
                    self.data[section][yamlFileOverride] = OrderedDict()
            else:
                yamlFileOverride = yamlFile
            if section in self.simpleSections:
                # for named simple sections that just contain simple items, go ahead and process
                entry = self.processSimple(section, itemkey, item, yamlFileOverride)
            else:
                #special sections are handled by appropriate class methods
                funct = '_'+ section
                # getattr is used to call the function specified in the string funct in the self object
                try:
                    entry = getattr(self, funct)(itemkey, item, yamlFileOverride)
                except AttributeError:
                    entry = self.processSimple(section, itemkey, item, yamlFileOverride)
                    self.simpleSections.add(section) # for user specific sections outside of default program supplied sections
            if comboKey is not None:
                # ok we have a combo key, so we can finally resolve it
                itemkey = entry[comboKeyName]
            self.data[section][yamlFileOverride][itemkey] = entry
            self.addFlatRecord(section, entry)
            self.addRecord(section, yamlFileOverride, itemkey, entry, self.schema.data['schema'][section])

    # process a single entry and handle all the trivial cases
    # schema can be provided for sub table use cases
    # note that auto fields are ignored
    def processSimple(self, section, anchor, item, yamlFile, schema = None, context='', outer = None):
        ret = {'_context': yamlFile}
        if isinstance(item, dict) and 'lc' in item:
            myLineNumber = item['lc'].line + 1
            ret['lc'] = item['lc']
        elif hasattr(item, 'lc'):
            myLineNumber = item.lc.line + 1
            ret['lc'] = item.lc
        else:
            myLineNumber = None
        comboKey = self.schema.data['comboKey'].get(context+section, None)
        comboSchema = self.schema.data['comboField'].get(context+section, {})
        if not schema:
            # default schema for non nested uses
            schema = self.schema.get_section(section).get_fields_dict() if self.schema.get_section(section) else {}

        if outer == None:
            # A top-level section entry must be a mapping of fields. Singular
            # scalars are coerced to a dict upstream in processSubTable before
            # dispatch (outer != None), so a non-dict reaching the top-level
            # walk is malformed YAML; report it cleanly instead of crashing on
            # the field iteration below.
            if not isinstance(item, dict):
                printError(f"In file {yamlFile}:{myLineNumber}, section {section}, key:{anchor} must be a mapping of fields but got {type(item).__name__}")
                exit(warningAndErrorReport())
            # loop through the fields in the item to make sure they are all in the schema
            for field in item:
                if not isinstance(field, dict) and not isinstance(item[field], dict):
                    if field not in schema and field not in ['eval', 'lc', '_yamlFileOverride']:
                        printWarning(f"In file {yamlFile}:{myLineNumber}, section {section}, key:{anchor} has unknown field {field}")

        # loop through the schema processing the input one field at a time
        for field, ftype in schema.items():
            comboField = comboSchema.get(field, None)
            if isinstance(ftype, dict):
                #if ftype is a dict, snap off the whole relevant piece as a dict depending on whether required or not
                attrib = self.schema.data['attrib'][context+section+field]
                if 'collapsed' in attrib:
                    # we have a nested entry, but as its collapsed its not actually anchored in the yaml with an varname, the anchor is the actual key
                    nested = item
                else:
                    nested = item.get(field)
                if not nested and 'required' in attrib:
                    self.logError(f"In file {yamlFile}:{myLineNumber}, section {section}, key:{anchor} required sub table {field} is missing")
                if nested:
                    if not isinstance(nested, (dict, list)):
                        printError(f"In file {yamlFile}:{myLineNumber}, section {section}, key:{anchor} required sub table {field} is missing definition")
                        exit(warningAndErrorReport())
                    # recursively process the sub entry
                    ret[field] = self.processSubTable(field, nested, yamlFile, ftype, anchor, context+section, ret)
                continue
            if ftype == 'ignore':
                # while unknown ftypes are ignored anyway, prefer to be explicit in ignoring ignore ftype
                continue
            if comboField:
                # field is created by concatenation of other fields. schema will have enforced ordering to after other fields
                # Use precomputed qualified sources from schema validation
                node = self.schema.get_node(context+section)
                field_obj = node.get_field(field) if node else None
                if not (field_obj and field_obj.combo_sources_qualified):
                    raise RuntimeError(f"Schema validation incomplete: combo field '{field}' in section '{context+section}' missing qualified sources")
                qualified_sources = field_obj.combo_sources_qualified
                comboStr = ""
                for source_field in qualified_sources:
                    if source_field not in ret or ret[source_field] is None:
                        self.logError(f"In file {yamlFile}:{myLineNumber}, section {section} {context}, field:{field} is missing required combo source {source_field}")
                        exit(warningAndErrorReport())
                    comboStr = comboStr + ret[source_field]
                ret[field] = comboStr
                # Immediately populate the qualified field if it exists in schema
                qualified_field = field + 'Key'
                if qualified_field in schema and qualified_field not in ret:
                    ret[qualified_field] = comboStr + '/' + yamlFile

            if ftype == 'key':
                if comboKey:
                    # key is created by concatenation of other fields. schema will have enforced ordering to after other fields
                    # Use precomputed qualified sources from schema validation
                    node = self.schema.get_node(context+section)
                    if not (node and node.combo_key_sources_qualified):
                        raise RuntimeError(f"Schema validation incomplete: combo key in section '{context+section}' missing qualified sources")
                    qualified_sources = node.combo_key_sources_qualified
                    keyStr = ""
                    for source_field in qualified_sources:
                        if source_field not in ret or ret[source_field] == None:
                            self.logError(f"In file {yamlFile}:{myLineNumber}, section {section} {context}, key:{anchor} is missing required field {source_field}")
                            exit(warningAndErrorReport())
                        keyStr = keyStr + ret[source_field]
                    ret[field] = keyStr
                elif anchor:
                    # if anchor was supplied then use it
                    ret[field] = anchor
                elif field not in item:
                    # anchor was not supplied and field not in item - this is an error
                    self.logError(f"In file {yamlFile}:{myLineNumber}, section {section}, key:{anchor} is missing required field {field}")
                else:
                    # anchor was not supplied but field is in item - use the item value
                    ret[field] = item.get(field)

                # Immediately populate the qualified key field if it exists in schema
                qualified_field = field + 'Key'
                if qualified_field in schema and qualified_field not in ret and field in ret:
                    ret[qualified_field] = ret[field] + '/' + yamlFile
            else:
                if ftype == 'listkey':
                    # For singleEntryList, the list item value is passed as anchor, not in item dict
                    ret[field] = anchor

                    # Immediately populate the qualified key field if it exists in schema
                    qualified_field = field + 'Key'
                    if qualified_field in schema and qualified_field not in ret and field in ret:
                        ret[qualified_field] = ret[field] + '/' + yamlFile
                if ftype == 'contextKey':
                    # contextKey fields are automatically populated when their corresponding
                    # key/anchor/listkey field is processed (see immediate population after each type)
                    # If not already populated, this is a bug that needs investigation
                    if field not in ret:
                        node = self.schema.get_node(context + section)
                        source_info = node.get_context_key_source(field) if node else None
                        if source_info is not None:
                            base_field, base_ftype = source_info
                        else:
                            base_field, base_ftype = '<unknown>', 'unknown'
                        self.logError(f"In file {yamlFile}:{myLineNumber}, section {context}{section}, contextKey field '{field}' was not pre-populated by its base field '{base_field}' (type={base_ftype}). This is a bug in processYaml.")
                        exit(warningAndErrorReport())
                    # else: correctly pre-populated, no action needed
                if ftype == 'anchor':
                    # anchor: field value comes from YAML anchor, not from item data
                    # Used for collapsed tables where the key is the YAML structure, not a field
                    # For list tables with natural keys, anchor may be None - get value from item
                    if anchor is not None:
                        ret[field] = anchor
                    elif field in item:
                        # List table with natural key - get the key value from item data
                        ret[field] = item[field]

                    # Immediately populate the qualified key field if it exists in schema
                    qualified_field = field + 'Key'
                    if qualified_field in schema and qualified_field not in ret and field in ret:
                        ret[qualified_field] = ret[field] + '/' + yamlFile
                if ftype in {'required', 'subkey'}:
                    if field not in item:
                        self.logError(f"In file {yamlFile}:{myLineNumber}, section {section}, key:{anchor} is missing required field {field}")
                    ret[field] = item.get(field)
                if ftype in {'optional', 'optionalConst'}:
                    # note that its only optional in the input - hence get usage
                    default = self.schema.data['optionalDefault'].get(context+section+field, "")
                    ret[field] = item.get(field, default)
                if ftype=='outerkey' or ftype=='outerkeyKey' or ftype=='outer':
                    # outer key is for the nested case, we want to refer back to the entry we are nested within
                    ret[field] = outer[field]
                if ftype in {'const', 'optionalConst', 'param'}:
                    # Shared shape: ret[field] keeps the user-typed token
                    # (symbol or numeric literal); ret[field+'Key'] gets the
                    # qualified 'name/context' for symbolic references and ''
                    # for literals (and for the param-is-block-parameter case,
                    # where the value resolves per-instance via parameter
                    # bindings rather than a constant-table lookup).
                    qualKey = ""
                    if ftype == 'param':
                        # param accepts: a block parameter name, OR a constant/
                        # enum symbol, OR a numeric literal. The design element
                        # must belong to a block for the block-param path.
                        if field not in item:
                            self.logError(f"In file {yamlFile}:{myLineNumber}, section {section} {context}, key:{anchor} is missing required field {field}")
                        else:
                            ret[field] = item[field]
                            if 'block' in ret and self.checkIsParam(ret['block'], item[field], yamlFile):
                                pass  # block parameter; resolved per-instance, no qualKey
                            else:
                                resolved = self._parserResolver.qualifyKey(
                                    item[field], yamlFile, fatal=False)
                                if resolved is None:
                                    self.logError(
                                        f"In file {yamlFile}:{myLineNumber}, section {section} {context}, "
                                        f"key:{anchor} field {field}: '{item[field]}' is not a parameter "
                                        f"of block '{ret.get('block', '?')}' and is not declared as a "
                                        f"constant or enum in '{yamlFile}' or any file it includes.")
                                else:
                                    qualKey = resolved
                    elif ftype == 'const':
                        if field not in item:
                            self.logError(f"In file {yamlFile}:{myLineNumber}, section {section} {context}, key:{anchor} is missing required field {field}")
                        else:
                            ret[field] = item[field]
                            qualKey = self._parserResolver.qualifyKey(item[field], yamlFile)
                    else:  # optionalConst
                        if field in item:
                            qualKey = self._parserResolver.qualifyKey(ret[field], yamlFile)
                    ret[field+'Key'] = qualKey
                if ftype=='eval':
                    # value is either provided from eval statement or a named field if present
                    if field in item:
                        # named field is present, so use that
                        ret[field] = item[field]
                    elif 'eval' in item:
                        # Parse once into the resolved IR: bare $symbols become
                        # qualified keys, and unresolved symbols, real literals,
                        # and bad syntax are rejected here. This is the sole
                        # symbol-resolution gate for eval expressions.
                        try:
                            node = evalExpr.parse(
                                item['eval'],
                                qualify=lambda n: self._parserResolver.qualifyKey(n, yamlFile, fatal=False))
                        except evalExpr.EvalParseError as e:
                            self.logError(f"In file {yamlFile}:{myLineNumber}, section {section}, key:{anchor} "
                                          f"eval expression '{item['eval']}' is invalid: {e}")
                            ret[field] = 0  # default to avoid cascading errors
                        else:
                            try:
                                ret[field] = evalExpr.evaluate(
                                    node,
                                    resolve=lambda k: self._parserResolver.value(
                                        k, label=f"eval token in {yamlFile}:{myLineNumber} key:{anchor}"))
                            except evalExpr.EvalEvalError as e:
                                self.logError(f"In file {yamlFile}:{myLineNumber}, section {section}, key:{anchor} "
                                              f"eval expression '{item['eval']}' failed: {e}")
                                ret[field] = 0  # default to avoid cascading errors
                            # Persist the canonical IR serialization and stash the
                            # node for _constants (parameterizable detection,
                            # worst-case maxValue). evalCanonical precedes 'value'
                            # in the schema, so the generic optional-field pass has
                            # already defaulted it and will not clobber this write.
                            if 'evalCanonical' in schema:
                                ret['evalCanonical'] = evalExpr.unparse(node)
                                self._evalNodes[(yamlFile, anchor)] = node
                    else:
                        # Neither field nor eval provided - this is an error
                        self.logError(f"In file {yamlFile}:{myLineNumber}, section {section}, key:{anchor} must provide either '{field}' field or 'eval' expression")
                if ftype[:4]=='auto':
                    # auto fields are used to handle all the special cases and prevent processSimple becoming bloated
                    # hopefully this eases maintainance and makes adding new special cases simplier
                    # call the special case:
                    myAutoRet = getattr(self, self.schema.data['fnStr'][context+section+field])(section, anchor, item, field, yamlFile, ret)
                    # the special cases can create signle return field or multiple - detect and handle
                    if isinstance(myAutoRet, dict):
                        # our auto function returned multiple keys so add them all
                        ret.update(myAutoRet)
                    else:
                        # just a single field
                        ret[field] = myAutoRet
            validator = self.schema.data['validator'].get(context+section+field, None)
            if ftype=='optional' and ret[field]=="":
                #if it was an optional field and there is no value, skip validation
                validator = None
                # still need to add key field
                if field+'Key' in schema:
                    ret[field+'Key'] = ""
            if validator:
                # if we have a validator, we need to check if the value is valid in this context
                if 'values' in validator:
                    # the validator can be a simple list of valid options
                    if ret[field] not in validator['values']:
                        self.logError(f"In file {yamlFile}:{myLineNumber}, section {section}, key:{anchor} field {field}, {item[field]} is not in the allowed values, check schema for valid valued")
                else:
                    # more complex validation necessary
                    # however we do have to avoid some special cases (for example _topInstance) which will by definition fail validation
                    if ret[field] not in self.dontValidate:
                        # search for appropriate value within the yaml context allowed for this file
                        scope = validator.get('scope', yamlFile) # if the schema specified a scope override - use that
                        (varInfo, varContext) = self.validateForeignKey(ret, context+section, field, scope)
                        # if its valid then use it
                        if varInfo:
                            # as its valid we also need to capture the context key - ie what file did the referenced value come from
                            ret[field+'Key'] = varInfo[validator['field']] + '/' + varContext
                        else:
                            # Surface likely include-scope mistakes by naming
                            # already-loaded contexts that define the symbol.
                            targetSection = validator['section']
                            foundElsewhere = []
                            for qualification, group in self.data.get(targetSection, {}).items():
                                if isinstance(group, dict) and ret[field] in group:
                                    foundElsewhere.append(qualification)
                            if foundElsewhere:
                                whereDefined = ', '.join(sorted(foundElsewhere))
                                hint = (f" but is defined in {whereDefined}; "
                                        f"add the defining file to the include: "
                                        f"chain of {scope}")
                            else:
                                hint = (f"; no {targetSection} row named "
                                        f"'{ret[field]}' was found in any "
                                        f"context processed before this one")
                            self.logError(f"In file {yamlFile}:{myLineNumber}, section {section}, key:{anchor} field {field}, value {ret[field]} was not valid in context {scope}{hint}")
                            # add anyway to prevent key error later
                            ret[field+'Key'] = 'InvalidValueInYaml'
                    else:
                        # if this is a special value that should not be validated
                        ret[field+'Key'] = ret[field] + '/' + yamlFile
        if context+section in self.schema.data['post']:
            # if there is a post process function for this section, call it now
            funct = self.schema.data['post'][context+section]
            # getattr is used to call the function specified in the string funct in the self object
            ret = getattr(self, funct)(anchor, ret, yamlFile)

        return ret

    # AUTO SECTIONS begin here
    #
    #constants: constant: key, value: eval, desc: required, valueType: optional(uint)
    def _constants(self, itemkey, item, yamlFile):
        ret = self.processSimple('constants', itemkey, item, yamlFile)
        # constants require special section handling as we want to save the const's in dict to allow later
        if 'value' not in ret:
            self.logError(f"Processing constants in {yamlFile}:{ret['lc'].line + 1} and constant:{itemkey} does not have a 'value' or 'eval' field")
        else:
            # Validate that the value matches the declared valueType
            declaredType = ret['valueType']
            val = ret['value']
            if declaredType == 'uint':
                if isinstance(val, float):
                    self.logError(f"In {yamlFile}:{ret['lc'].line + 1}, constant '{itemkey}': valueType is 'uint' (default) but eval produced a float ({val}). "
                                  f"Use // for integer division, or set valueType: real")
                elif isinstance(val, int) and val < 0:
                    self.logError(f"In {yamlFile}:{ret['lc'].line + 1}, constant '{itemkey}': valueType is 'uint' but value is negative ({val}). "
                                  f"Use valueType: int for signed constants")
            elif declaredType == 'int':
                if isinstance(val, float):
                    self.logError(f"In {yamlFile}:{ret['lc'].line + 1}, constant '{itemkey}': valueType is 'int' but eval produced a float ({val}). "
                                  f"Use // for integer division in eval expressions")
            elif declaredType == 'real':
                # The integer symbolic-eval pipeline does not support real eval
                # expressions; a real constant must carry a literal 'value'.
                if 'eval' in item and 'value' not in item:
                    self.logError(f"In {yamlFile}:{ret['lc'].line + 1}, constant '{itemkey}': valueType 'real' with an "
                                  f"'eval' expression is not supported; real constants must use a literal 'value'.")
        # Parameterizable constant propagation.
        # Determine if this constant is parameterizable, by:
        #   (a) derived: its eval expression references another parameterizable
        #       constant -> isParameterizable + maxValue auto-derived. This is
        #       the authoritative source whenever it applies; user must NOT
        #       hand-write maxValue on a derived constant.
        #   (b) direct: declared inside an ipParameters block, or user wrote a
        #       non-default maxValue on a literal-valued (non-eval) constant.
        # Referenced constants must already be finalized in self.data['constants'].
        lineNo = (ret['lc'].line + 1) if 'lc' in ret else '?'
        ipActive = getattr(self, '_ipParametersActive', False)
        rawMaxValue = item.get('maxValue', 0)
        # Normalize maxValue to an integer and report malformed values before
        # downstream arithmetic or comparisons.
        userMaxProvided = rawMaxValue not in (0, None, '')
        if userMaxProvided:
            # Reject bool explicitly (bool is a subclass of int in Python).
            if isinstance(rawMaxValue, bool) or not isinstance(rawMaxValue, int):
                # Allow string forms of integers ("16", "0x10") for consistency
                # with how YAML often quotes hex; reject anything else.
                coerced = None
                if isinstance(rawMaxValue, str):
                    try:
                        coerced = int(rawMaxValue, 0)
                    except (TypeError, ValueError):
                        coerced = None
                if coerced is None:
                    self.logError(f"In file {yamlFile}:{lineNo}, constant '{itemkey}': "
                                  f"maxValue must be an integer, got "
                                  f"{type(rawMaxValue).__name__}={rawMaxValue!r}")
                    rawMaxValue = 0
                    userMaxProvided = False
                else:
                    rawMaxValue = coerced
        userMaxValue = rawMaxValue if userMaxProvided else 0
        userParamFlag = bool(item.get('isParameterizable', False))

        # The parsed eval IR (if this is an eval constant) was stashed by
        # processSimple keyed by (yamlFile, name).
        node = self._evalNodes.get((yamlFile, itemkey))

        derivedParam = False
        derivedMaxValue = 0
        if node is not None:
            label = f"constant '{itemkey}' in {yamlFile}:{lineNo}"
            # Symbol resolution only: if any referenced constant is
            # parameterizable, this constant is derived-parameterizable. No
            # value is computed in this walk.
            for symKey in evalExpr.symbolKeys(node):
                if self._parserResolver.lookupNamedRow(symKey, label)['isParameterizable']:
                    derivedParam = True
                    break
            if derivedParam:
                # Worst-case maxValue: evaluate the same tree, substituting each
                # referent's maxValue (parameterizable) or value (otherwise).
                try:
                    derivedMaxValue = evalExpr.evaluate(
                        node,
                        resolve=lambda k: self._parserResolver.maxValue(k, label))
                except evalExpr.EvalEvalError as e:
                    self.logError(f"In file {yamlFile}:{lineNo}, constant '{itemkey}' "
                                  f"maxValue evaluation failed: {e}")
                    derivedMaxValue = 0

        # Direct path applies only when there is no derived path: literal value
        # (no eval) inside ipParameters, user-set isParameterizable: true, or
        # any literal with explicit maxValue.
        directParam = (not derivedParam) and (bool(ipActive) or userParamFlag or userMaxProvided)

        if derivedParam:
            ret['isParameterizable'] = True
            ret['maxValue'] = derivedMaxValue
            if userMaxProvided:
                # Reject: user-supplied maxValue on a derived constant is
                # redundant at best and a likely consistency hazard at worst.
                self.logError(f"In file {yamlFile}:{lineNo}, constant '{itemkey}': "
                              f"maxValue is auto-derived from eval expression "
                              f"(=> {derivedMaxValue}); do not hand-write maxValue "
                              f"on derived parameterizable constants")
            if derivedMaxValue <= 0:
                self.logError(f"In file {yamlFile}:{lineNo}, constant '{itemkey}': "
                              f"derived maxValue must be > 0, got {derivedMaxValue}")
            if 'value' in ret and isinstance(ret['value'], (int, float)) and ret['value'] > derivedMaxValue:
                self.logError(f"In file {yamlFile}:{lineNo}, constant '{itemkey}': "
                              f"value ({ret['value']}) exceeds derived maxValue ({derivedMaxValue})")
        elif directParam:
            ret['isParameterizable'] = True
            if not userMaxProvided:
                # Direct parameterizable constant (ipParameters or explicit
                # isParameterizable: true) MUST declare maxValue. Without it
                # downstream worst-case sizing is meaningless.
                origin = ("declared in ipParameters" if ipActive
                          else "marked isParameterizable: true")
                self.logError(f"In file {yamlFile}:{lineNo}, constant '{itemkey}': "
                              f"{origin} but maxValue is missing; maxValue is "
                              f"required for parameterizable constants")
            else:
                # User-provided maxValue is authoritative for direct case.
                if userMaxValue <= 0:
                    self.logError(f"In file {yamlFile}:{lineNo}, constant '{itemkey}': "
                                  f"maxValue must be > 0 when parameterizable, got {userMaxValue}")
                if 'value' in ret and isinstance(ret['value'], (int, float)) and ret['value'] > userMaxValue:
                    self.logError(f"In file {yamlFile}:{lineNo}, constant '{itemkey}': "
                                  f"value ({ret['value']}) exceeds maxValue ({userMaxValue})")
                # ret['maxValue'] already populated from schema/user input
        else:
            ret['isParameterizable'] = False

        return ret

    def _resolveWordLinesConst(self, row, resolver):
        """Resolve a memory/register row's wordLines constant entry.
        Handles both qualified-key (regular constant) and bare-name block-param
        cases, returning a constant entry dict or None for empty wordLines.
        Accepts a processed project row. `resolver` is supplied by the caller so
        this helper can be invoked both parse-time (passing the per-file
        `self._parserResolver`) and post-parse (passing a caller-owned
        ValueResolver, e.g. from calcAddresses).

        Lookup precedence:
          1. wordLinesKey qualified ('name/file') -> direct constant lookup
          2. wordLines is a literal int           -> synthesized non-param entry
          3. wordLines is a bare block param      -> exact blocksparams.paramKey lookup

        Bare-name misses are hard errors; searching every context risks picking
        a same-named constant from an unrelated block and would mask scope/typo
        errors.

        Returns None for empty wordLines only; non-empty symbolic wordLines must
        resolve to a constant row."""
        wlKey = row['wordLinesKey']
        if wlKey != '':
            return resolver.lookupNamedRow(wlKey, 'constant')
        # Bare-name (param) case: use the block-param row's backing constant key.
        wl = row['wordLines']
        if wl == '' or wl == 0:
            # Empty/default wordLines: caller decides (e.g. non-memory registers
            # have wordLines defaulted to 0). Surface as None rather than erroring.
            return None
        try:
            return {'value': int(wl), 'isParameterizable': False, 'maxValue': 0}
        except (TypeError, ValueError):
            pass
        blockKey = row['blockKey']
        blockRow = self.flatData['blocks'][blockKey]
        blockName = blockRow['block']
        ctx = blockRow['_context']
        blockParam = None
        for candidate in self.flatData['blocksparams'].values():
            if candidate['blockKey'] == blockKey and candidate['param'] == wl:
                blockParam = candidate
                break
        if blockParam is None:
            printError(f"In context '{ctx}', block '{blockName}': wordLines references "
                       f"'{wl}' but no block parameter named '{wl}' is declared "
                       f"in this block (typo, missing ipParameters entry, or "
                       f"scope violation).")
            exit(warningAndErrorReport())
        backingKey = blockParam['paramKey']
        return self.flatData['constants'][backingKey]

    def _post_add_enum(self, itemkey, item, yamlFile):
        if 'enumName' in item:
            if item['enumName'] in self.enums.get(yamlFile, {}):
                self.logError(f"Processing enums in {yamlFile}:{item['lc'].line + 1} and enum:{itemkey} has duplicate enumName {item['enumName']}")
                exit(warningAndErrorReport())
            # Defensive check - value should have been validated in processSimple (eval field type)
            # If value is missing here, validation failed earlier
            if 'value' not in item:
                # This shouldn't happen if processSimple validation works correctly
                return item  # Skip adding incomplete enum
            if yamlFile not in self.enums:
                self.enums[yamlFile] = dict()
            self.enums[yamlFile][item['enumName']] = {'value': item['value'], 'type': item['type']}
            self.qualEnums[item['enumName']+'/'+yamlFile] = {'value': item['value'], 'type': item['type']}
        return item

    def _post_validate_interface_structures(self, itemkey, item, yamlFile):
        """Validate that structureType values match parameters defined in interface_defs

        This performs bidirectional validation:
        1. Each structureType must be a valid parameter in interface_defs
        2. All struct-type parameters from interface_defs must be present
        """
        # Only validate if interface has interfaceType
        if 'interfaceType' not in item:
            return item

        intf_type = item['interfaceType']

        # Get the interface_defs for this interfaceType
        # Use yamlFile as context to allow user-defined interfaces, with _a2csystem as fallback
        (intf_def, intf_context) = self.lookupInScope('interface_defs', yamlFile, intf_type)

        if not intf_def:
            # If interface_defs not found, the interfaceType validation will catch this
            return item

        # Extract valid parameter names from interface_defs
        if 'parameters' not in intf_def:
            # No parameters defined, so no structure types are expected
            if item.get('structures'):
                line_num = item['lc'].line + 1 if hasattr(item, 'lc') else '?'
                self.logError(f"In file {yamlFile}:{line_num}, interface '{itemkey}' with interfaceType '{intf_type}' "
                            f"has structures defined, but interface_defs '{intf_type}' does not define any parameters")
            return item

        # Get all valid structure types and required struct parameters
        all_params = intf_def['parameters']
        valid_structure_types = set(all_params.keys())

        # Filter to only struct-type parameters (these are the ones that need structures defined)
        required_struct_params = {
            param_name for param_name, param_info in all_params.items()
            if param_info.get('datatype') == 'struct'
        }

        # Get the structureTypes that are defined in the interface
        defined_structure_types = set()
        structures = item.get('structures', {})

        # Validation 1: Check each defined structureType is valid
        for struct_key, struct_data in structures.items():
            if 'structureType' not in struct_data:
                continue  # This will be caught by required field validation

            structure_type = struct_data['structureType']
            defined_structure_types.add(structure_type)

            if structure_type not in valid_structure_types:
                line_num = struct_data['lc'].line + 1 if hasattr(struct_data, 'lc') else '?'
                valid_types_str = "', '".join(sorted(valid_structure_types))
                self.logError(f"In file {yamlFile}:{line_num}, interface '{itemkey}' with interfaceType '{intf_type}': "
                            f"structureType '{structure_type}' is not valid. "
                            f"Valid structureTypes for '{intf_type}' are: '{valid_types_str}'")

        # Validation 2: Check all required struct parameters are present
        missing_params = required_struct_params - defined_structure_types
        if missing_params:
            line_num = item['lc'].line + 1 if hasattr(item, 'lc') else '?'
            missing_params_str = "', '".join(sorted(missing_params))
            self.logError(f"In file {yamlFile}:{line_num}, interface '{itemkey}' with interfaceType '{intf_type}': "
                        f"missing required structureType(s): '{missing_params_str}'. "
                        f"All struct-type parameters from interface_defs must have corresponding structures.")

        return item

    def _post_validateBlockAddressDecl(self, itemkey, item, yamlFile):
        """Validate block-level address/register declaration invariants
        that the schema engine cannot express."""
        if item.get('registerPorts') and item.get('addressBlock'):
            lc = item.get('lc')
            line = lc.line + 1 if lc is not None else '?'
            self.logError(
                f"In {yamlFile}:{line}, block '{itemkey}' declares both "
                f"registerPorts: and addressBlock:; these are mutually exclusive."
            )
        registerPorts = item.get('registerPorts') or {}
        if len(registerPorts) > 1:
            lc = item.get('lc')
            line = lc.line + 1 if lc is not None else '?'
            names = "', '".join(sorted(registerPorts.keys()))
            self.logError(
                f"In {yamlFile}:{line}, block '{itemkey}' declares multiple "
                f"registerPorts: entries ('{names}'). Blocks support exactly "
                f"one register-bus ingress."
            )
        return item

    def _post_validateRegisterPortInterface(self, itemkey, item, yamlFile):
        """Confirm the row's interface resolves to an interface_defs
        entry with addressBus: true."""
        intfInfo = self.flatData['interfaces'][item['interfaceKey']]
        intfDef = self.flatData['interface_defs'][intfInfo['interfaceTypeKey']]
        if not intfDef['addressBus']:
            lc = item.get('lc')
            line = lc.line + 1 if lc is not None and hasattr(lc, 'line') else '?'
            self.logError(
                f"In {yamlFile}:{line}, registerPorts port "
                f"'{item['port']}' references interface "
                f"'{item['interface']}' whose interfaceType "
                f"'{intfInfo['interfaceType']}' is not marked "
                f"addressBus: true."
            )
        return item

    def _post_registerAddressBlock(self, itemkey, item, yamlFile):
        """Register the per-block addressBlock: declaration into the
        AddressGroups counter state consumed by address allocation and
        firmware-header generation. itemkey is the owning block name
        (passed by processSubTable for dataGroup tables)."""
        group = item['addressGroup']
        lc = item.get('lc')
        line = lc.line + 1 if lc is not None and hasattr(lc, 'line') else '?'

        if 'AddressGroups' not in self.counterGroup:
            self.counterGroup['AddressGroups'] = OrderedDict()
        if 'AddressGroups' not in self.counterGroupControl:
            self.counterGroupControl['AddressGroups'] = OrderedDict()
        if 'AddressGroups' not in self.counterData:
            self.counterData['AddressGroups'] = OrderedDict()
        if not isinstance(self.addressControl, dict):
            self.addressControl = OrderedDict()
        if 'AddressGroups' not in self.addressControl:
            self.addressControl['AddressGroups'] = OrderedDict()

        if group in self.counterGroupControl['AddressGroups']:
            prior = self.counterGroupControl['AddressGroups'][group]
            self.logError(
                f"In {yamlFile}:{line}, addressGroup '{group}' declared on "
                f"block '{itemkey}' duplicates a prior addressBlock: "
                f"declaration on block '{prior['_declaringBlock']}' "
                f"in {prior['_declaringFile']}. "
                f"Each addressGroup may have at most one router-block declaration."
            )
            return item

        # varTypeContext = yamlFile scopes varType resolution to the
        # router block's own YAML file.
        groupRow = OrderedDict()
        groupRow['addressIncrement'] = item['addressIncrement']
        groupRow['maxAddressSpaces'] = item['maxAddressSpaces']
        groupRow['varType'] = item['varType']
        groupRow['varTypeContext'] = yamlFile
        groupRow['enumPrefix'] = item['enumPrefix']
        groupRow['upstreamPort'] = item['upstreamPort']
        groupRow['registerDecoderPort'] = item['registerDecoderPort']
        groupRow['_declaringBlock'] = itemkey
        groupRow['_declaringFile'] = yamlFile

        self.counterGroup['AddressGroups'][group] = 0
        self.counterGroupControl['AddressGroups'][group] = groupRow
        self.counterData['AddressGroups'][group] = OrderedDict()
        self.addressControl['AddressGroups'][group] = groupRow

        return item

    #interfaces: interface: key, interfaceType: required, desc: required, structname: subkey,  structureType: auto,
    def _interfaces(self, itemkey, item, yamlFile):
        # handle simple stuff first
        ret = self.processSimple('interfaces', itemkey, item, yamlFile)
        #self.addRecord('interfaces', yamlFile, itemkey, ret, self.schema['interfaces'])
        # handle nested
        intfSchema = self.schema.data['interfaces']['structures']
        attrib = self.schema.data['attrib'].get('interfacesstructures')
        subItems = ret['structures'].copy()
        if ('required' in attrib) and (not subItems):
            self.logError(f"Processing interfaces in {yamlFile} and interface:{itemkey} does not have any structures to define the interface")

        ret['structures'] = OrderedDict()
        for subkey, subItem in subItems.items():
            ret['structures'][subkey] = self.processSimple('interfaces', subkey, subItem, yamlFile, schema=intfSchema)
            #self.addRecord('interfacesstructures', yamlFile, itemkey, ret, self.schema['interfacesstructures'])
        return ret

    def _specialStructures(self, itemkey, item, yamlFile):
        ret = self.processSimple('specialStructures', itemkey, item, yamlFile)
        (varInfo, varContext) = self.lookupInScope('structures', yamlFile, ret['baseStruct'])
        if not varInfo:
            self.logError(f"Processing specialStructures in {yamlFile} and entry:{itemkey} does not reference valid baseStruct")
            exit(warningAndErrorReport())

        varschema = self.schema.get_node('structuresvars').get_fields_dict() if self.schema.get_node('structuresvars') else {}
        newStruct = OrderedDict()
        newStructVars = OrderedDict()
        reserved = 0
        for k, v in varInfo.items():
            if k == 'structure':
                v = ret['structure']
            if k == 'structureKey':
                v = ret['structureKey']
            if k != 'vars':
                newStruct[k] = v

        # now handle alignment
        bitpos = 0
        for var, varData in varInfo['vars'].items():
            # convert 0 to 1
            align = max(int(varData['align']), 1)
            # from the alignment calculate the correctly aligned position by rounding up to next aligned spot
            newBitpos = ((bitpos + align - 1) // align) * align
            if newBitpos != bitpos:
                # we are not naturally aligned so we need to add a reserved field for padding
                varName = 'reserved'+str(reserved)
                reserved = reserved + 1
                newItem = {
                    'structure':    ret['structure'],
                    'variable':     varName,
                    'entryType':    'Reserved',
                    'desc':         'Reserved Field for padding',
                    'align':        newBitpos-bitpos
                }
                # use process simple here to reduce maintenance if more fields added to schema
                newVar = self.processSimple("vars", varName, newItem, yamlFile, schema = varschema, context="structures", outer=newStruct)
                bitpos = newBitpos
                newStructVars[varName] = newVar
            newStructVars[var] = varData
            bitpos = bitpos + self._parserResolver.varWidth(varData)
        newStruct['vars'] = newStructVars
        newStruct['width'] = bitpos
        # add our newly constructed struct to the tables and db
        self.data["structures"][yamlFile][itemkey] = newStruct
        self.addFlatRecord("structures", newStruct)
        self.addRecord("structures", yamlFile, itemkey, newStruct, self.schema.data['schema']["structures"])
        return ret

    def _encoders(self, itemkey, item, yamlFile):
        # process the data entry piece
        ret = self.processSimple('encoders', itemkey, item, yamlFile)
        # handle enum defaults
        if ret['enumType']=="":
            ret['enumType'] = itemkey+"TypeT"
        if ret['enumPrefix'] == "":
            ret['enumPrefix'] = itemkey.upper()+"_TYPE_"
        encoderType = ret['encoderType']
        newEncoderType = OrderedDict()
        newEncoderType['lc'] = ret['lc']
        newEncoderType['desc'] = ret['encoderTypeDesc']
        newEncoderType['width'] = ret['encoderTypeWidth']
        encoderTypeBits = self._parserResolver.value(
            newEncoderType['width'],
            label=f"encoder '{itemkey}' encoderTypeWidth")
        # split off the items for further processing and later adding back in
        encoderItems = ret['items']
        ret['items'] = OrderedDict()

        # sort keys in decending size based on numBits
        numBits = dict() # store the lookups
        for item in encoderItems:
            numBits[item] = self._parserResolver.value(
                encoderItems[item]['numBits'],
                label=f"encoder '{itemkey}' item '{item}' numBits")

        sortedItemKeys = sorted(encoderItems, key=lambda x: (numBits[x]), reverse=True)
        startValue = 0
        itemOrder = 0
        inverter = 0
        if not ret['zeroBased']:
            inverter = (1 << encoderTypeBits) - 1
        for item in sortedItemKeys:
            #copy the item over. note that as we care about the order we are copying the source items one at a time
            ret['items'][item] = encoderItems[item]
            ret['items'][item]['itemOrder'] = itemOrder
            itemOrder = itemOrder + 1
            # encodingValue are the bits above the field based on the number of bits in the field
            # note that we dont know how many bits in total the encoder needs just yet
            ret['items'][item]['encodingValue'] = (startValue ^ inverter) & ~((1 << numBits[item]) - 1)
            startValue = startValue + (1 << numBits[item])
        if startValue > (1 << encoderTypeBits):
            self.logError(f"Processing encoders in {yamlFile} and encoder:{itemkey} need more bits than the encoder type:{ret['encoderType']} can hold")
            exit(warningAndErrorReport())
        ret['totalBits'] = encoderTypeBits
        ret['encodeMax'] = startValue-1
        # generate new type to hold the enum and optional constants
        # iterate through the items to generate dictionary to allow the type to be generated
        newType = OrderedDict()
        newType['lc'] = ret['lc']
        newType['enum'] = list()
        newConstants = OrderedDict()
        addConstants = False
        baseConstPrefix = ret['baseConstPrefix']
        if baseConstPrefix != "":
            addConstants = True
        if ret['enumDesc'] == "":
            newType['desc'] = f"Type of {itemkey} (auto generated from encoder section)"
        else:
            newType['desc'] = ret['enumDesc']

        for item in sortedItemKeys:
            thisEnum = OrderedDict()
            # add the type
            thisEnum['enumName'] = ret['enumPrefix']+item.upper()
            thisEnum['desc'] = ret['items'][item]['desc']
            thisEnum['value'] = ret['items'][item]['itemOrder']
            newType['enum'].append(thisEnum)
            if addConstants:
                newConstants[baseConstPrefix+item.upper()] = {'value': ret['items'][item]['encodingValue'], 'desc': 'base value for ' + ret['items'][item]['desc'], 'lc': ret['lc'] }
        if not ret['zeroBased'] and ret['extendedRangeItem'] != "":
            thisEnum = OrderedDict()
            # add the type
            thisEnum['enumName'] = ret['enumPrefix']+ret['extendedRangeItem'].upper()
            thisEnum['desc'] = ret['extendedRangeDesc']
            thisEnum['value'] = itemOrder
            newType['enum'].append(thisEnum)
        newSections = {'types': {ret['enumType']: newType, encoderType: newEncoderType}}
        if addConstants:
            newSections['constants'] = newConstants
        self.processSingleFile(yamlFile, newSections)
        #newTypeProcessed = self.processSimple('types', ret['enumType'], newType, yamlFile)
        #self.data["types"][yamlFile][ret['enumType']] = newTypeProcessed
        #self.addRecord("types", yamlFile, ret['enumType'], newTypeProcessed, self.schema.data['schema']["types"])



        return ret

    # algorithm for special portname convention
    def _auto_variantProjectName(self, section, itemkey, item, field, yamlFile, processed):
        # Declaring project of a variant binding row: the project that owns the
        # row's context file. Populated from the authoritative ownership map
        # assigned at the end of readRaw (before section auto-fields run), so it
        # is parse-time safe. On a monolithic build every context resolves to the
        # root PROJECTNAME, so this projectName key dimension is uniform.
        return self.contextOwningProject[yamlFile]

    def _auto_portName(self, section, itemkey, item, field, yamlFile, processed):
        return(getPortChannelName(item))

    # algorithm for special portname convention
    def _auto_instancePortName(self, section, itemkey, item, field, yamlFile, processed):
        return(getPortChannelName(item, "instancePort"))

    # handle structure auto sensing of type
    def _auto_entryType(self, section, itemkey, item, field, yamlFile, processed):
        subStruct = item.get("subStruct", "")
        varType = item.get("varType", "")
        entryType = item.get("entryType", "")
        if entryType == "Reserved":
            return "Reserved"
        # need to figure out what has been specified
        if subStruct:
            ret = "NamedStruct"
        elif varType:
            ret = "NamedType"
        else:
            # for named var we have to perform the validation as its outside the capabilities of simple section
            (varInfo, varContext) = self.lookupInScope('variables', yamlFile, itemkey)
            if not varInfo:
                #it was neither
                self.logError(f"reference {itemkey} in structure does not reference a valid variable definition in this context {yamlFile}:{item.lc.line + 1}")

            ret = { 'varType': varInfo.get('type'),
                    'varTypeKey': varInfo.get('typeKey'),
                    'desc' : varInfo.get('desc'),
                    'entryType': "NamedVar",
                    'lc' : varInfo.get('lc')}
        return ret


    # handle special case where the top block does not have a container
    def _auto_container(self, section, itemkey, item, field, yamlFile, processed):
        ret = item[field]
        # if the instance matches the defined top instance override the container
        # the override allows for nested projects
        if itemkey == self.topInstance:
            ret = "_topInstance"
        return ret

    def _auto_addressGroup(self, section, itemkey, item, field, yamlFile, processed):
        ret=item.get(field, None)
        if ret:
            if ret not in self.counterGroup.get('AddressGroups', {}):
                self.logError(f"In {yamlFile}:{item.lc.line + 1}, '{itemkey}' referenced a non existant address group {ret}"
                              ", check addressGroup match your AddressControl file")
        return ret

    def _auto_addressID(self, section, itemkey, item, field, yamlFile, processed):
        #note that even if specified in instances section, will be overridden
        addressControlFields = {'addressGroup': None, 'addressID': None, 'addressMultiples': None, 'instanceGroup': None, 'instanceID': None}
        ret = None
        if processed[self.counterReverseField[section+'addressGroup']] is not None:
            group = processed[self.counterReverseField[section+'addressGroup']]
            counter = self.counterGroup['AddressGroups'][group]
            base = counter * self.addressControl['AddressGroups'][group]['addressIncrement']
            ret = {
                field: counter,
                'offset': base
            }
            self.counterGroup['AddressGroups'][group] = counter + processed[self.counterReverseField[section+'addressMultiples']]
            if self.counterGroup['AddressGroups'][group] > self.addressControl['AddressGroups'][group]['maxAddressSpaces']:
                self.logError(f"In {yamlFile}:{item.lc.line + 1}, '{itemkey}' we ran out of address space, check your maxAddressSpaces: in AddressControl file")
        return ret

    def _auto_instanceGroup(self, section, itemkey, item, field, yamlFile, processed):
         # this field needs to be one of the valid InstanceGroups defined in the addressControl file
        ret=item.get(field, None)
        if not ret:
            # if not specified, use the default group
            ret = 'default'
        if ret not in self.counterGroup.get('InstanceGroups', {}):
            self.logError(f"In {yamlFile}:{item.lc.line + 1}, '{itemkey}' referenced a non existant instance group {ret}")
        return ret

    def _auto_instanceID(self, section, itemkey, item, field, yamlFile, processed):
          #note that even if specified in instances section, will be overridde
        if not self.counterGroup.get(section+'InstanceGroups', None):
            group = 'default'
            if not 'InstanceGroups' in self.counterGroup:
                self.counterGroup['InstanceGroups'] = dict()
            self.counterGroup['InstanceGroups'][group] = 0
        else:
            group = item[self.counterReverseField[section+'instanceGroup']]
        ret = self.counterGroup['InstanceGroups'][group]
        self.counterGroup['InstanceGroups'][group] = ret + 1
        return ret

    # def _auto_registerLeafInstance(self, section, itemkey, item, field, yamlFile, processed):
    #     # registerLeafInstance is not enabled by default.
    #     ret = item.get(field, None)
    #     return ret

    def _auto_addressMultiples(self, section, itemkey, item, field, yamlFile, processed):
          #note that even if specified in instances section, will be overridde
        ret=item.get(field, 1)
        return ret

    def _post_validateTypeWidth(self, itemkey, item, yamlFile):
        """Validate type width fields after processing.

        Enforces:
        - Exactly one of width, widthLog2, widthLog2minus1 must be specified (unless enum provides width)
        - Resolved width must be non-zero
        - Float constants are not valid as widths
        - Signed log2-derived widths include sign bit adjustment (+1)
        """
        # Count which width fields are specified (non-empty)
        hasWidth = item['width'] != ''
        hasWidthLog2 = item['widthLog2'] != ''
        hasWidthLog2minus1 = item['widthLog2minus1'] != ''
        widthCount = sum([hasWidth, hasWidthLog2, hasWidthLog2minus1])

        if widthCount > 1:
            self.logError(f"In {yamlFile}:{item.get('lc').line + 1 if item.get('lc') else '?'}, type '{itemkey}' specifies multiple width fields. "
                          f"Only one of width, widthLog2, widthLog2minus1 may be specified")
            return item

        enum = item.get('enum', None)
        enumMax = 1
        if enum:
            for val, valItem in enum.items():
                if 'value' not in valItem:
                    self.logError(f"In {yamlFile}:{item.get('lc').line + 1 if item.get('lc') else '?'}, type '{itemkey}' enum entry missing 'value' field")
                    return item
                valActual = self._parserResolver.value(
                    valItem['value'],
                    label=f"enum '{val}' value",
                    source=item)
                if valActual < 0:
                    self.logError(f"In {yamlFile}:{item.get('lc').line + 1 if item.get('lc') else '?'}, type '{itemkey}' enum '{val}' has negative value ({valActual}), but signed enums are not supported")
                    return item
                enumMax = max(enumMax, valActual)

        if widthCount == 0:
            # No explicit width — derive from enum values if available.
            if enum:
                item['width'] = int(enumMax).bit_length()
            else:
                self.logError(f"In {yamlFile}:{item.get('lc').line + 1 if item.get('lc') else '?'}, type '{itemkey}' is missing width — must specify one of width, widthLog2, or widthLog2minus1 (or provide an enum)")
                return item

        # Validate the specified width field resolves to a non-zero integer
        if hasWidth:
            widthField = 'width'
        elif hasWidthLog2:
            widthField = 'widthLog2'
        else:
            widthField = 'widthLog2minus1' if hasWidthLog2minus1 else 'width'  # width for enum-derived case

        # Resolve the raw value to an integer
        rawValue = item[widthField]
        n = self._parserResolver.value(
            rawValue,
            label=widthField,
            source=item)

        # Compute the actual bit width
        isSigned = bool(item.get('isSigned', False))
        if hasWidthLog2:
            if n < 0:
                self.logError(f"In {yamlFile}:{item.get('lc').line + 1 if item.get('lc') else '?'}, type '{itemkey}' widthLog2 resolves to negative value ({n}), which is not valid")
                return item
            computedWidth = n.bit_length()
            if isSigned:
                computedWidth += 1
        elif hasWidthLog2minus1:
            if n <= 0:
                self.logError(f"In {yamlFile}:{item.get('lc').line + 1 if item.get('lc') else '?'}, type '{itemkey}' widthLog2minus1 resolves to {n}, "
                              f"which is not valid (requires a positive value to index 0..N-1)")
                return item
            computedWidth = (n - 1).bit_length()
            if isSigned:
                computedWidth += 1
        else:
            computedWidth = n

        if computedWidth == 0:
            self.logError(f"In {yamlFile}:{item.get('lc').line + 1 if item.get('lc') else '?'}, type '{itemkey}' {widthField} resolves to zero width, which is not valid")

        # Parameterizable type propagation.
        # Two paths to be parameterizable:
        #   (a) direct: declared inside ipParameters block, user explicitly set
        #       isParameterizable: true, or user wrote a non-default maxBitwidth.
        #   (b) derived: width/widthLog2/widthLog2minus1 references a
        #       parameterizable constant.
        lineNo = (item.get('lc').line + 1) if item.get('lc') else '?'
        ipActive = getattr(self, '_ipParametersActive', False)
        rawMaxBitwidth = item.get('maxBitwidth', 0)
        userMaxBitwidthProvided = rawMaxBitwidth not in (0, None, '', '0')
        if userMaxBitwidthProvided:
            if isinstance(rawMaxBitwidth, bool):
                self.logError(f"In {yamlFile}:{lineNo}, type '{itemkey}': "
                              f"maxBitwidth must be an integer, got "
                              f"bool={rawMaxBitwidth!r}")
                return item
            try:
                userMaxBitwidth = int(rawMaxBitwidth, 0) if isinstance(rawMaxBitwidth, str) else int(rawMaxBitwidth)
            except (TypeError, ValueError):
                self.logError(f"In {yamlFile}:{lineNo}, type '{itemkey}': "
                              f"maxBitwidth must be an integer, got "
                              f"{type(rawMaxBitwidth).__name__}={rawMaxBitwidth!r}")
                return item
            if isinstance(rawMaxBitwidth, float) and rawMaxBitwidth != userMaxBitwidth:
                self.logError(f"In {yamlFile}:{lineNo}, type '{itemkey}': "
                              f"maxBitwidth must be an integer, got "
                              f"float={rawMaxBitwidth!r}")
                return item
            item['maxBitwidth'] = userMaxBitwidth
        else:
            userMaxBitwidth = 0
        userParamFlag = bool(item.get('isParameterizable', False))
        directParam = bool(ipActive) or userParamFlag or userMaxBitwidthProvided

        # Identify referenced constant. It must already be finalized.
        derivedParam = False
        derivedMaxBitwidth = 0
        widthMode = None
        if hasWidth:
            widthMode = 'width'
        elif hasWidthLog2:
            widthMode = 'widthLog2'
        elif hasWidthLog2minus1:
            widthMode = 'widthLog2minus1'
        if widthMode:
            qualKey = item.get(widthMode + 'Key', '')
            if qualKey:
                refConst = self._parserResolver.lookupNamedRow(qualKey, 'constant')
                if refConst and refConst.get('isParameterizable'):
                    derivedParam = True
                    refMax = refConst.get('maxValue', 0) or 0
                    if widthMode == 'widthLog2':
                        derivedMaxBitwidth = int(refMax).bit_length()
                        if isSigned:
                            derivedMaxBitwidth += 1
                    elif widthMode == 'widthLog2minus1':
                        if refMax > 0:
                            derivedMaxBitwidth = int(refMax - 1).bit_length()
                        else:
                            derivedMaxBitwidth = 0
                        if isSigned:
                            derivedMaxBitwidth += 1
                    else:  # width
                        derivedMaxBitwidth = int(refMax)

        if directParam or derivedParam:
            item['isParameterizable'] = True
            if directParam and userMaxBitwidthProvided:
                # User-provided maxBitwidth takes precedence (worst case).
                # When the width references a parameterizable constant the type
                # can be as wide as that constant's maxValue, so the floor is the
                # worst-case derived width, not just the nominal resolved width;
                # otherwise it must at least cover the resolved width.
                if userMaxBitwidth <= 0:
                    self.logError(f"In {yamlFile}:{lineNo}, type '{itemkey}': "
                                  f"maxBitwidth must be > 0 when parameterizable, got {userMaxBitwidth}")
                requiredFloor = (derivedMaxBitwidth
                                 if (derivedParam and derivedMaxBitwidth > 0)
                                 else computedWidth)
                if userMaxBitwidth < requiredFloor:
                    self.logError(f"In {yamlFile}:{lineNo}, type '{itemkey}': "
                                  f"maxBitwidth ({userMaxBitwidth}) is less than the "
                                  f"worst-case width ({requiredFloor}) implied by its "
                                  f"parameterizable width")
                # already in item['maxBitwidth']
            elif directParam:
                # ipParameters type or user-set isParameterizable: true with no
                # explicit maxBitwidth. Accept only when a derived path supplies
                # one; otherwise hard-error (silently falling back to the nominal
                # width would cause downstream worst-case sizing to under-allocate).
                if derivedParam and derivedMaxBitwidth > 0:
                    item['maxBitwidth'] = derivedMaxBitwidth
                else:
                    origin = ("declared in ipParameters" if ipActive
                              else "marked isParameterizable: true")
                    self.logError(f"In {yamlFile}:{lineNo}, type '{itemkey}': "
                                  f"{origin} but maxBitwidth is missing and "
                                  f"the {widthMode or 'width'} expression does not "
                                  f"reference a parameterizable constant; "
                                  f"explicit maxBitwidth is required")
                    return item
            elif derivedParam:
                # Pure derived case
                item['maxBitwidth'] = derivedMaxBitwidth
                if derivedMaxBitwidth < computedWidth:
                    self.logError(f"In {yamlFile}:{lineNo}, type '{itemkey}': "
                                  f"derived maxBitwidth ({derivedMaxBitwidth}) is less than width ({computedWidth})")
        else:
            item['isParameterizable'] = False
            # leave maxBitwidth as 0

        return item

    def _auto_structWidth(self, section, itemkey, item, field, yamlFile, processed):
        width = 0
        for var, varinfo in processed['vars'].items():
            width = width + self._parserResolver.varWidth(
                varinfo,
                field_name=f"structure '{itemkey}' field '{var}'")
        return (width)

    def _auto_structIsParameterizable(self, section, itemkey, item, field, yamlFile, processed):
        # A structure is parameterizable iff any field references a
        # parameterizable type, sub-structure, or array-size constant.
        lineNo = (processed.get('lc').line + 1) if processed.get('lc') else '?'
        for var, varinfo in processed['vars'].items():
            # Type field
            varTypeKey = varinfo['varTypeKey']
            if varTypeKey and '/' in varTypeKey:
                tEntry = self._rowByQualifiedKey('types', varTypeKey)
                if tEntry['isParameterizable']:
                    return True
            elif varTypeKey:
                printError(f"Internal error: structure '{itemkey}' in {yamlFile}:{lineNo} "
                           f"has malformed varTypeKey '{varTypeKey}' for field '{var}' "
                           f"(expected 'name/yamlFile').")
                exit(warningAndErrorReport())
            # Sub-structure
            subKey = varinfo['subStructKey']
            if subKey and '/' in subKey:
                sEntry = self._rowByQualifiedKey('structures', subKey)
                if sEntry['isParameterizable']:
                    return True
            elif subKey:
                printError(f"Internal error: structure '{itemkey}' in {yamlFile}:{lineNo} "
                           f"has malformed subStructKey '{subKey}' for field '{var}' "
                           f"(expected 'name/yamlFile').")
                exit(warningAndErrorReport())
            # Array size: arraySizeKey may be qualified ('NAME/file')
            arrKey = varinfo['arraySizeKey']
            if arrKey and '/' in arrKey:
                cEntry = self._parserResolver.lookupNamedRow(arrKey, 'constant')
                if cEntry['isParameterizable']:
                    return True
            elif arrKey:
                printError(f"Internal error: structure '{itemkey}' in {yamlFile}:{lineNo} "
                           f"has malformed arraySizeKey '{arrKey}' for field '{var}' "
                           f"(expected 'name/yamlFile').")
                exit(warningAndErrorReport())
        return False

    def _rowByQualifiedKey(self, section, qualifiedKey):
        if not qualifiedKey or '/' not in qualifiedKey:
            printError(f"Internal error: malformed {section} key "
                       f"'{qualifiedKey}' (expected 'name/yamlFile').")
            exit(warningAndErrorReport())
        try:
            return self.flatData[section][qualifiedKey]
        except KeyError:
            printError(f"Internal error: {section} key '{qualifiedKey}' is "
                       f"not present in flatData['{section}'].")
            exit(warningAndErrorReport())

    def _auto_intfIsParameterizable(self, section, itemkey, item, field, yamlFile, processed):
        # Interface rows inherit parameterization from any carried structure.
        for struct_row in (processed.get('structures') or {}).values():
            sEntry = self._rowByQualifiedKey('structures', struct_row['structureKey'])
            if sEntry['isParameterizable']:
                return True
        return False

    def _auto_interfaceRefIsParameterizable(self, section, itemkey, item, field, yamlFile, processed):
        intf = self._rowByQualifiedKey('interfaces', processed['interfaceKey'])
        return bool(intf['isParameterizable'])

    def _auto_memoryConnectionIsParameterizable(self, section, itemkey, item, field, yamlFile, processed):
        mem = self._rowByQualifiedKey('memories', processed['memoryBlockKey'])
        return bool(mem['isParameterizable'])

    def _auto_registerConnectionIsParameterizable(self, section, itemkey, item, field, yamlFile, processed):
        reg = self._rowByQualifiedKey('registers', processed['registerBlockKey'])
        return bool(reg['isParameterizable'])

    def _auto_structMaxBitwidth(self, section, itemkey, item, field, yamlFile, processed):
        # Worst-case bit sum across fields. Returns 0 if structure is
        # not parameterizable (callers consult isParameterizable first).
        if not processed['isParameterizable']:
            return 0
        total = 0
        lineNo = (processed.get('lc').line + 1) if processed.get('lc') else '?'
        for var, varinfo in processed['vars'].items():
            fieldWidth = self._parserResolver.varWidth(
                varinfo,
                use_max=True,
                field_name=f"structure '{itemkey}' field '{var}'")
            if not isinstance(fieldWidth, int) or fieldWidth <= 0:
                printError(f"Internal error: structure '{itemkey}' in {yamlFile}:{lineNo} "
                           f"field '{var}' resolved to invalid field width {fieldWidth!r}.")
                exit(warningAndErrorReport())
            total += fieldWidth
        # Validate: maxBitwidth >= width
        existingWidth = processed['width']
        if total < existingWidth:
            lineNo = (processed.get('lc').line + 1) if processed.get('lc') else '?'
            self.logError(f"In {yamlFile}:{lineNo}, structure '{itemkey}': "
                          f"computed maxBitwidth ({total}) is less than width ({existingWidth})")
        return total

    def _auto_blockDir(self, section, itemkey, item, field, yamlFile, processed):
        # check if user provided an override
        ret = item.get(field, None)
        if ret:
            return ret
        return self.yamlDir

    def _auto_memIsParameterizable(self, section, itemkey, item, field, yamlFile, processed):
        # Memory is parameterizable iff its structure or wordLines constant is
        # parameterizable.
        structKey = processed['structureKey']
        sEntry = self._rowByQualifiedKey('structures', structKey)
        structIsParam = bool(sEntry['isParameterizable'])
        wlConst = self._resolveWordLinesConst(processed, self._parserResolver)
        wlIsParam = bool(wlConst and wlConst['isParameterizable'])
        return structIsParam or wlIsParam

    def _auto_regIsParameterizable(self, section, itemkey, item, field, yamlFile, processed):
        # Register is parameterizable iff its structure is parameterizable,
        # plus (for memory-type registers) its wordLines constant.
        structKey = processed['structureKey']
        sEntry = self._rowByQualifiedKey('structures', structKey)
        structIsParam = bool(sEntry['isParameterizable'])
        if processed['regType'] == 'memory':
            wlConst = self._resolveWordLinesConst(processed, self._parserResolver)
            if wlConst and wlConst['isParameterizable']:
                return True
        return structIsParam

    def _auto_regMaxBytes(self, section, itemkey, item, field, yamlFile, processed):
        # Worst-case byte size for a register, derived from its structure.
        # Hard-error on any failure path: a silent 0 propagates downstream as a
        # zero-sized register, corrupting address allocation without warning.
        structKey = processed['structureKey']
        sEntry = self._rowByQualifiedKey('structures', structKey)
        if sEntry['isParameterizable'] and sEntry['maxBitwidth']:
            width = sEntry['maxBitwidth']
        else:
            width = sEntry['width']
        if not isinstance(width, int) or width <= 0:
            paramFlag = sEntry['isParameterizable']
            printError(f"Register '{itemkey}' in {yamlFile}: structure "
                       f"'{structKey}' has invalid width "
                       f"(isParameterizable={paramFlag}, "
                       f"maxBitwidth={sEntry['maxBitwidth']}, "
                       f"width={sEntry['width']}). Cannot derive maxBytes.")
            exit(warningAndErrorReport())
        return (width + 7) >> 3

    def _post_registers(self, itemkey, item, yamlFile):
        """Validate memory register constraints after processing"""
        regType = item.get('regType', None)
        registerName = item.get('register', itemkey)

        if regType == 'memory':
            # Memory registers must have non-empty wordLines
            if not item.get('wordLines') or item.get('wordLines') == "":
                self.logError(f"In {yamlFile}:{item.get('lc').line + 1 if item.get('lc') else '?'}, memory register '{registerName}' must have wordLines field")
                return item

            # Validate wordLines resolves to non-zero value
            wlConst = self._resolveWordLinesConst(item, self._parserResolver)
            parsed_val = wlConst['maxValue'] if wlConst['isParameterizable'] and wlConst['maxValue'] else wlConst['value']
            if isinstance(parsed_val, bool) or not isinstance(parsed_val, int) or parsed_val <= 0:
                self.logError(f"In {yamlFile}:{item.get('lc').line + 1 if item.get('lc') else '?'}, memory register '{registerName}' "
                              f"wordLines must resolve to a positive integer, got {parsed_val!r}")
                return item

            # Memory registers must have addressStruct
            if not item.get('addressStruct') or item.get('addressStruct') == "":
                self.logError(f"In {yamlFile}:{item.get('lc').line + 1 if item.get('lc') else '?'}, memory register '{registerName}' must have addressStruct field")

        return item

    # connections: connection: key, instance: auto, direction: auto, port: optional, connCount: optional
    # this is a complete custom handler, as the key is derived from other fields
    def _process_connections(self, data, yamlFile):

        # Initialize the per-file dict only if absent. Post-parse scripts
        # may call processSingleFile() repeatedly for the same yamlFile
        # to add synthesized connections; resetting the dict would wipe
        # the user-authored rows processed earlier. The postProcess
        # script list must be authored to avoid running the same script
        # twice (avoid list_append duplication), otherwise duplicate
        # rows would accumulate here.
        self.data['connections'].setdefault(yamlFile, dict())
        self.data['connectionsends'].setdefault(yamlFile, dict())
        # loop through the items in the section
        for item in data:

            dirContext = dict()
            # use process simple with the data schema to extract the info and validate
            row = self.processSimple('connections_dataSchema', 'dummy', item, yamlFile, schema=self.schema.data['dataSchema']['connections'] )
            # the base entry is based on this processing
            entry = row.copy()
            # every connection has a nested table with the source and destination of the connection saved in the ends field
            entry['ends'] = dict()
            myKey = row['connection']
            # if a name is provided use that as the channel name, otherwise use the src port naming
            if row['name'] != '':
                entry['channel'] = row['name']
            else:
                entry['channel'] = ''
            for dir in ['src', 'dst']:
                (instInfo, instContext) = self.lookupInScope('instances', yamlFile, row[dir])
                if not instInfo:
                    printError(f"instances {row[dir]} in file {yamlFile} is unresolved")
                    exit(warningAndErrorReport())
                row['instanceType'] = instInfo['instanceType']
                row['instanceTypeKey'] = instInfo['instanceTypeKey']
                row['instance'] = row[dir]
                row['instanceKey'] = row[dir+'Key']
                row['port'] = row[dir+'port']
                row['direction'] = dir
                portName = getPortChannelName(row, dir+'port') # use naming convention
                row['portName'] = portName
                if 'lc' in instInfo:
                    row['lc'] = instInfo['lc']
                elif hasattr(instInfo, 'lc'):
                    row['lc'] = instInfo.lc
                else:
                    myConnection = instInfo['instance']
                    print(f"Warning: no line number in connections section for {yamlFile}:{myConnection}")

                # the channel is declared based on the src port
                if entry['channel'] == '' and dir=='src':
                    entry['channel'] = portName

                endRow = self.processSimple('ends', 'dummy', row, yamlFile, schema=self.schema.data['schema']['connections']['ends'],context='connections', outer = row )

                entry['ends'][endRow['portId']]=endRow
                self.data['connectionsends'][yamlFile][endRow['portId']]=endRow

            self.data['connections'][yamlFile][myKey] = entry
            self.addFlatRecord('connections', entry)
            self.addRecord('connections', yamlFile, myKey, entry, self.schema.data['schema']['connections'])

        return

    # ipParameters: container section that delegates to existing section schemas (constants, types).
    # Entries from ipParameters are merged into the same self.data['constants']/self.data['types']
    # dictionaries as regular entries. Per-entry handlers stamp them as parameterizable.
    # Transitive propagation and worst-case sizing are performed by those handlers.
    def _process_ipParameters(self, data, yamlFile):
        # ipParameters may only appear in an IP-root YAML, not in a pure shared
        # type/structure/constant include. A shared include is included by another
        # file and does not itself declare any blocks.
        isIncludedElsewhere = any(yamlFile in deps for deps in self.yamlDependancies.values())
        rawSections = self.yamlRaw.get(yamlFile, {}) or {}
        hasBlocks = 'blocks' in rawSections
        if isIncludedElsewhere and not hasBlocks:
            printError(f"ipParameters is not allowed in shared include file {yamlFile}; "
                       f"shared includes (no 'blocks:' section) cannot declare ipParameters "
                       f"because parameter bounds are tied to the IP root")
            exit(warningAndErrorReport())
        # Set a flag so per-section handlers (constants, types) can stamp
        # isParameterizable=True immediately as each entry is processed,
        # preserving finalized referents when later entries reference them.
        prev = getattr(self, '_ipParametersActive', False)
        self._ipParametersActive = True
        try:
            for section, sectData in data.items():
                if section in self.schema.data['mapto']:
                    section = self.schema.data['mapto'][section]
                if section in self.schema.data['schema']:
                    # Process through normal section pipeline - same schema, same validation.
                    # Per-entry handlers consult self._ipParametersActive to stamp isParameterizable.
                    self.processSection(section, sectData, yamlFile)
                    if section == 'constants':
                        self._captureIpParametersConstants(sectData, yamlFile)
                else:
                    printError(f"Unknown sub-section '{section}' in ipParameters in {yamlFile}")
                    exit(warningAndErrorReport())
        finally:
            self._ipParametersActive = prev

    def _captureIpParametersConstants(self, sectData, yamlFile):
        # Record each ipParameters constant into a per-file dict keyed by name so
        # the file-level orphan check (every exposed param consumed by >=1 block
        # param) and the per-row variant-binding sizing check can resolve them.
        # The constants have already been added to self.data['constants'][yamlFile]
        # by processSection, so the qualified key and maxValue are read back here.
        fileConsts = self.ipParametersConstants.setdefault(yamlFile, OrderedDict())
        names = sectData if isinstance(sectData, dict) else \
            (loopitem[self.schema.data['key']['constants']] for loopitem in sectData)
        for name in names:
            entry = self.data['constants'][yamlFile][name]
            fileConsts[name] = {
                'name': name,
                'context': yamlFile,
                'constantKey': entry['constantKey'],
                'maxValue': entry['maxValue'],
            }

    def _post_validateBlockParamBacking(self, itemkey, item, yamlFile):
        # Per block-param row: resolve the param to its same-name backing constant
        # and require that constant to be parameterizable. A declarative _validate
        # cannot express this because constants is context-scoped (the FK framework
        # only targets flat sections), so the lookup is done here. This rejects a
        # pure param (no backing const) and a param colliding with a plain
        # (non-parameterizable) constants: entry. The orphan direction (an exposed
        # ipParameters const consumed by no block param) is the file-level check.
        param = item['param']
        line = item['lc'].line + 1 if item.get('lc') else '?'
        (constInfo, _constContext) = self.lookupInScope('constants', yamlFile, param)
        if constInfo is None:
            self.logError(f"In {yamlFile}:{line}: block param '{param}' has no backing constant; "
                          f"every block param must be declared as a same-name ipParameters constant")
        elif not constInfo['isParameterizable']:
            self.logError(f"In {yamlFile}:{line}: block param '{param}' is backed by a non-parameterizable "
                          f"constant; a block param must be backed by an ipParameters constant")
        return item

    def _validateIpParametersLinkage(self):
        # Project-wide orphan/empty-set check, run once after every file is fully
        # parsed: each exposed ipParameters constant must be consumed by at least
        # one same-file block param. Detecting an empty consumer set is inherently
        # aggregate over the whole file, so it cannot run inside processSingleFile,
        # which is re-entered mid-parse for synthesized type/constant subsets
        # (encoder expansion, address-enum injection) where the consuming blocks:
        # section has not yet been parsed. The per-param backing and parameterizable
        # checks remain row-level validators on the params field (see
        # _post_validateBlockParamBacking and the param field _validate).
        # Consumption is read from the resolved blocksparams paramKey.
        for yamlFile, fileConsts in self.ipParametersConstants.items():
            if not fileConsts:
                continue
            consumed = {row['paramKey'] for row in self.data['blocksparams'].get(yamlFile, {}).values()}
            for name, const in fileConsts.items():
                if const['constantKey'] not in consumed:
                    self.logError(f"In {yamlFile}: ipParameters constant '{name}' is not consumed by any "
                                  f"block param; every exposed ipParameters constant must back >=1 block param")

    def _post_validateVariantBindingSizing(self, itemkey, item, yamlFile):
        # Per-binding-row check: the backing ipParameters const's maxValue must be
        # >= this binding's value, otherwise worst-case address sizing (sourced
        # from maxValue) would under-allocate for that variant. blockParamKey is
        # an opaque identity for the target blocksparams row; use that row's
        # paramKey to reach the exact backing constant.
        blockParamKey = item['blockParamKey']
        if blockParamKey not in self.flatData['blocksparams']:
            return item   # blockParam failed its own validation; error already logged
        blockParam = self.flatData['blocksparams'][blockParamKey]
        backingKey = blockParam['paramKey']
        if backingKey not in self.flatData['constants']:
            return item   # blockParam backing failed its own validation; error already logged
        backing = self.flatData['constants'][backingKey]
        value = self._resolveVariantBindingValue(item)
        if value is not None and backing['maxValue'] < value:
            self.logError(f"In {yamlFile}:{item['lc'].line + 1 if item.get('lc') else '?'}: variant "
                          f"'{item['variant']}' binds param '{item['param']}' to {value}, exceeding the "
                          f"backing ipParameters constant '{backingKey}' maxValue "
                          f"{backing['maxValue']}; raise the constant's maxValue to cover the worst-case binding")
        return item

    def _post_validateVariantParameterCompleteness(self, itemkey, item, yamlFile):
        # Per-variant-row check: every declared variant must bind EVERY parameter
        # its block declares; the nested variant schema has no default-fill for an
        # omitted parameter. Fires once per (block, variant) row with its nested
        # params children already populated, in the row's own file scope. The
        # variant row's block foreign key orders the block (and its declared
        # params) ahead of this row, so the block resolves by scope here with no
        # global bucket iteration.
        block = item['block']
        blockRow, _q = self.lookupInScope('blocks', yamlFile, block)
        if blockRow is None:
            # An out-of-scope block is already rejected by the leaf binding rows'
            # blockParam foreign-key validation; nothing to add here.
            return item
        reference = set(blockRow.get('params', {}))
        bound = set(item.get('params', {}))
        missing = reference - bound
        if missing:
            projectName = self.contextOwningProject[yamlFile]
            self.logError(
                f"Variant '{item['variant']}' of block '{block}' (project '{projectName}') "
                f"is missing required parameter(s): {', '.join(sorted(missing))}. "
                f"Every variant must bind all block parameters "
                f"[{', '.join(sorted(reference))}]; there is no default for an "
                f"omitted parameter.")
        return item

    def _resolveVariantBindingValue(self, row):
        # A binding value is either a literal int or the name of a constant the
        # user referenced; in the latter case valueKey is the qualified const key.
        valueKey = row.get('valueKey', '') or ''
        if valueKey:
            constEntry = self._parserResolver.lookupNamedRow(
                valueKey, 'variant binding value')
            return constEntry['value']
        return row['value']

    def checkIsParam(self, block, param, context):
        (varInfo, varContext) = self.lookupInScope('blocks', context, block)
        if varInfo:
            if 'params' in varInfo:
                return param in varInfo['params']

        return False

    def _lookupInGlobal(self, objType, name):
        ret = None
        found = False
        foundContext = None
        for qualification, rows in self.data[objType].items():
            if name in rows:
                if found:
                    printError(f"Duplicate key {name} found in global context during validation of {objType}")
                ret = rows[name]
                found = True
                foundContext = qualification
        return ret, foundContext

    def lookupInScope(self, objType, context, name):
        """Resolve an unqualified row name by walking the include chain of
        `context`. `_a2csystem` rows are visible from every non-global
        context as an implicit fallback.

        `context == 'global'` is the user-authored `scope: global` from
        schema validators: search every loaded qualification and treat
        duplicate matches as an error via `_lookupInGlobal`.

        `context == '_global'` is the internal sentinel populated by
        callers that need to walk every loaded context without duplicate
        diagnostics; the include chain stored in `yamlContext['_global']`
        already covers all of them, so this falls through the normal walk.

        Never interprets a `/` inside `name`. Returns
        (row, qualification) or (None, None)."""
        if context == 'global':
            return self._lookupInGlobal(objType, name)
        for qualification in self.yamlContext[context]:
            rows = self.data[objType].get(qualification, {})
            if name in rows:
                return rows[name], qualification
        sysRows = self.data[objType].get('_a2csystem', {})
        if name in sysRows:
            return sysRows[name], '_a2csystem'
        return None, None

    def validateForeignKey(self, sourceRow, sourceSection, sourceField, context):
        """Validate a schema-declared foreign key on `sourceRow` against
        its declared target. The schema's plain/combo classification of
        the source field selects the branch:

        - Plain FK: resolve `sourceRow[sourceField]` through scoped
          lookup. SCHEMA_SPECIFICATION.md, Foreign-Key Invariants
          guarantees the target section is `flat` and `validator.field`
          names its storage key.
        - Combo FK: walk rows of the target section in scope order and
          match the source row's components against the target's
          component fields. SCHEMA_SPECIFICATION.md, Foreign-Key
          Invariants guarantees the combo sources
          on source and target are identical, so reading the unqualified
          component values on `sourceRow` is safe and the match is
          immune to `is_foreign_key` asymmetry between sections.

        Returns (targetRow, qualification) or (None, None)."""
        validator = self.schema.data['validator'][sourceSection + sourceField]
        targetSection = validator['section']
        targetFieldName = validator['field']
        sourceFieldObj = self.schema.get_node(sourceSection).get_field(sourceField)
        sourceCombo = sourceFieldObj.combo_sources

        if not sourceCombo:
            return self.lookupInScope(targetSection, context, sourceRow[sourceField])

        if context == 'global':
            qualifications = list(self.data[targetSection])
        else:
            qualifications = list(self.yamlContext[context])
        if '_a2csystem' not in qualifications:
            qualifications.append('_a2csystem')
        for qualification in qualifications:
            for row in self.data[targetSection].get(qualification, {}).values():
                if all(row[source] == sourceRow[source] for source in sourceCombo):
                    return row, qualification
        return None, None

    def _scalarSeqItemLc(self, nested, index):
        # ruamel (round-trip) attaches line/col to the parent CommentedSeq, not to
        # scalar list elements (a bare str/int has no .lc). Recover the element's
        # position from the parent so flat-list rows carry a real line for error
        # reporting, mirroring the lc that mapping-style rows already get.
        # Synthesized (non-ruamel) lists have no .lc; those rows carry no line.
        if not hasattr(nested, 'lc'):
            return None
        line, col = nested.lc.item(index)
        lc = type(nested.lc)()
        lc.line = line
        lc.col = col
        return lc

    def _coerceSingular(self, sectionKey, item):
        # A _singular sub-table (e.g. signals.signalType, variants.params.value)
        # authors each entry as `<key>: <scalar>`. Wrap that scalar in a dict
        # keyed by the section's singular field so processSimple sees the normal
        # field mapping. Non-singular sections and dict items pass through
        # unchanged.
        if not isinstance(item, dict) and sectionKey in self.schema.data['singular']:
            return {self.schema.data['singular'][sectionKey]: item}
        return item

    def processSubTable(self, section, nested, yamlFile, nestedSchema, outerItemKey, context, outer = None):
        # Process nested table entries using the schema for the child section.
        ret = dict()
        nestedContext = context+section
        if nestedContext == 'memoriesports':
            pass
        if yamlFile not in self.data[nestedContext]:
            self.data[nestedContext][yamlFile] = OrderedDict()
        attribs = self.schema.data['attrib'].get(nestedContext, {})
        comboKey = self.schema.data['comboKey'].get(nestedContext, None)

        if 'list' in attribs:
            # if nested is a list of dictionaries then we will enumerate and process, however if it just a single enty, then it is just a key on its own
            if isinstance(nested[0], (dict, list)):
                # All list tables now have explicit keys defined in schema
                # The key value comes from item data, not from YAML anchor
                node = self.schema.get_node(nestedContext)

                for index, item in enumerate(nested):
                    # No anchor provided - key will come from item data
                    anchor = None

                    processed = self.processSimple(section, anchor, item, yamlFile, schema=nestedSchema, context=context, outer=outer)

                    # Get the key from the processed item's key field
                    key_field = node.storage_key_field if node else None
                    if not key_field:
                        self.logError(f"In file {yamlFile}, section {context}{section}, list table schema has no storage_key_field defined. This is a schema validation bug.")
                        exit(warningAndErrorReport())
                    if key_field not in processed:
                        self.logError(f"In file {yamlFile}, section {context}{section}, list table key field '{key_field}' not found in processed item. This is a processing bug.")
                        exit(warningAndErrorReport())
                    itemkey = processed[key_field]

                    ret[itemkey] = processed
                    self.data[nestedContext][yamlFile][itemkey] = processed
                    self.addFlatRecord(nestedContext, processed)
            else:
                # Simple list of scalar values; recover each element's line from
                # the parent sequence so the row carries a position for diagnostics.
                for index, item in enumerate(nested):
                    anchor = item
                    lc = self._scalarSeqItemLc(nested, index)
                    processed = self.processSimple(section, anchor, {'lc': lc} if lc is not None else {}, yamlFile, schema=nestedSchema, context=context, outer=outer)
                    itemkey = self.schema.data['key'][nestedContext]
                    itemkey = processed[itemkey]
                    ret[anchor] = processed
                    self.data[nestedContext][yamlFile][itemkey] = processed
                    self.addFlatRecord(nestedContext, processed)

        elif 'singleEntryList' in attribs:
            # Handle singleEntryList separately - items from a list become individual records
            for index, item in enumerate(nested):
                anchor = item
                lc = self._scalarSeqItemLc(nested, index)
                processed = self.processSimple(section, anchor, {'lc': lc} if lc is not None else {}, yamlFile, schema=nestedSchema, context=context, outer=outer)
                itemkey = self.schema.data['key'][nestedContext]
                itemkey = processed[itemkey]
                ret[anchor] = processed
                self.data[nestedContext][yamlFile][itemkey] = processed
                self.addFlatRecord(nestedContext, processed)

        else:
            if isinstance(nested, list):
                if comboKey:
                    itemkeyName = self.schema.data['key'][nestedContext]
                    itemkey = ""
                    for item in nested:
                        listret = self.processSimple(section, itemkey, item, yamlFile, schema=nestedSchema, context=context, outer=outer)
                        ret[listret[itemkeyName]] = listret
                        self.data[nestedContext][yamlFile][listret[itemkeyName]] = listret
                        self.addFlatRecord(nestedContext, listret)
                else:
                    printError(f"{yamlFile}:{nested.lc.line+1} {nested} unexpected in list format in file {context} this is either a schema or file error")
                    exit(warningAndErrorReport())

            else:
                if 'dataGroup' in attribs:
                    ret = self.processSimple(section, outerItemKey, nested, yamlFile, schema=nestedSchema, context=context, outer=outer)
                else:
                    for itemkey, item in nested.items():
                        item = self._coerceSingular(nestedContext, item)
                        processed = self.processSimple(section, itemkey, item, yamlFile, schema=nestedSchema, context=context, outer=outer)
                        storageKey = self.schema.data['key'][nestedContext]
                        storageKey = processed[storageKey]
                        ret[itemkey] = processed
                        self.data[nestedContext][yamlFile][storageKey] = processed
                        self.addFlatRecord(nestedContext, processed)
        return ret

    # add an item to the database
    def addRecord(self, table, yamlFile, itemkey, entry, schema, outerEntry=None):
        myLineNumber = 0
        if self.schema.data['multiEntry'][table]:
            # for this case we want to iterate over the items
            loop = entry
        else:
            # there is only one item, so pretend its a single entry multi item to allow looping
            loop = {itemkey: entry}
        for myEntryKey, myEntry in loop.items():
            if 'lc' in myEntry:
                myLineNumber = myEntry['lc'].line + 1
            comma = ''
            values = ''
            valueList = list()
            params = ''
            for col in schema:
                value = None
                # detect inner table
                if isinstance(schema[col], dict):
                    if col in myEntry:
                        self.addRecord(table+col, yamlFile, itemkey, myEntry[col], schema[col], outerEntry=entry)
                    continue
                if schema[col] == 'key':
                    value = myEntry.get(col, myEntryKey)
                if schema[col] in ['outerkey', 'outerkeyKey', 'outer']:
                    value = myEntry.get(col, outerEntry.get(col, None))
                    if value is None:
                        self.logError(f"In file {yamlFile}:{myLineNumber}, section {table}, key:{itemkey} is missing required field {col}")
                if schema[col] == 'context':
                    value = yamlFile
                if value is None:
                    value = myEntry[col]
                    if value is None:
                        value = ''
                valueList.append(value)
                params = f"{params}{comma} ? "
                comma = ', '

            sql = f"INSERT INTO {table} ({self.schema.data['colsSQL'][table]}) values ({params})"
            # use parameterized sql to finally fix the damn appostrophe
            try:
                g.cur.execute(sql, valueList)
            except sqlite3.InterfaceError as e:
                print(f"ERROR inserting into {table}:")
                print(f"  SQL: {sql}")
                print(f"  Values: {valueList}")
                print(f"  Value types: {[type(v) for v in valueList]}")
                raise
