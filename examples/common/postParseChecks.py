from pysrc.arch2codeHelper import printError, printWarning, warningAndErrorReport, printIfDebug
import pysrc.arch2codeGlobals as g

def postProcess(prj):
    """Post process the project after parsing the YAML file.
    
    Args:
        prj (project): The project object.
    """
    # perform checks on the project
    #
    sql = "select instance, variant, _context from instances where variant != '' and variant not in (select variant from parametersvariants where block = instances.instanceType)"
    cursor = g.db.cursor()
    cursor.execute(sql)
    rows = cursor.fetchall()
    if len(rows) > 0:
        for row in rows:
            printError(f"Variant {row['varient']} for instance {row['instance']} in file: {row['_context']} is not found in the parameters section")
        exit(1)

    sql = """
select b.param, b._context, i.variant, b.block from blocksparams b join instances i on b.blockKey = i.instanceTypeKey where i.variant != '' 
   and not exists (select 1 from parametersvariants p where p.param = b.param and p.variant = i.variant)
"""
    cursor.execute(sql)
    rows = cursor.fetchall()
    if len(rows) > 0:
        for row in rows:
            printError(f"Parameter:{row['param']} is missing for variant:{row['variant']} of block:{row['block']} ")
        exit(1)

    ret = None
    return ret