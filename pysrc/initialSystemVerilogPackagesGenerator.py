# systemVerilog Initial Package Generation
import pysrc.arch2codeGlobals as globals
from pysrc.arch2codeHelper import printIfDebug
from collections import OrderedDict
from pathlib import Path

class initialSystemVerilogPackagesGenerator:

    def __init__(self, prj, args):
        # the yamlContext dictionary is in order with the first processed yaml last with it's dependancies
        # reverse the dictionary, go through sub dictionary and insert items if not already found
        # this will preseve the order the yaml files were processed in and order packages
        revYamlContexts = OrderedDict(reversed(list(prj.yamlContext.items())))
        c = []
        contextPerContext = []
        for unusedKey, v in revYamlContexts.items():
            for k, unusedValue in v.items():
                if k not in c:
                    contextPerContext.insert(0, k)
            c.extend(contextPerContext)
            contextPerContext = []
        printIfDebug(f'Yaml contexts: {c}')

        printIfDebug (args.moduledir)
        directory = Path(args.moduledir)

        packageDotF = ''
        for context in c:
            # remove file extension, protect from multiple dots in file path / name
            # https://stackoverflow.com/a/45866399
            package = Path(context).resolve().stem
            out = ''
            out += f'// GENERATED_CODE_PARAM --contexts {context}\n'
            out +=  '// GENERATED_CODE_BEGIN --template=package --fileMapKey=package_sv\n'
            out +=  '// GENERATED_CODE_END\n'
            # if the yaml context have a path we add that to the package location
            #   we can also make a package.f file
            cPath = Path(context)
            if cPath.parent.name != '':
                # .resolve() creates the absolute path leave in for files
                fileName    = directory / cPath.resolve().parent / f'{package}Package.sv'
                # Don't use .resolve() here because we want relative not absolute
                packageDotF += f'-sv {Path(context).parent}/{package}Package.sv\n'
            else:
                fileName = directory / f'{package}Package.sv'
                packageDotF += f'-sv {package}Package.sv\n'
            printIfDebug(f'out into file {fileName}')
            printIfDebug(out)
            if not globals.debug:
                fileName.parent.mkdir(parents=True, exist_ok=True)
                fileName.write_text(out)
        
        printIfDebug("Don't forget package.f is\n")
        printIfDebug(packageDotF)
        if not globals.debug:
            fileName = directory / 'package.f'
            fileName.write_text(packageDotF)
