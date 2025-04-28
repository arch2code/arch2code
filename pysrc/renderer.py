from pysrc.arch2codeHelper import printError, warningAndErrorReport
import pysrc.processYaml as processYaml
import pysrc.arch2codeGlobals as g
from jinja2 import Template
import os
import importlib
import argparse
# simple helper class to take care of the jinja interfaces
class renderer:
    docType = ""
    configFile = ""
    config = None
    templates = dict()
    pythonTemplate = dict()
    def __init__(self, prj, configFileKey, docType = 'asciidoctor', directTemplate = None) -> None:
        self.docType = docType
        # initialze using a user provided mapping between templates and template files
        if directTemplate is None:
            templateConfig = prj.config.getConfig('TEMPLATE_CONFIGS')
            self.config = templateConfig.get(configFileKey, {})
        else:
            self.config = directTemplate
        if 'templates' not in self.config:
            printError(f"templates: key does not exist in config file {self.configFile}")
            exit(warningAndErrorReport())
        self.loadTemplates()

    def renderSections(self, caller, codeObj, sectionParser, prj, data, args):
        genOut = list()
        # add common section args
        sectionParser.add_argument('--handler', type=str, help='Generator handler' , default="generic")
        sectionParser.add_argument('--template', type=str, help='Jinga template or python function')
        sectionParser.add_argument('--section', type=str, help='Section within python template', default='')
        sectionParser.add_argument('--noExternalComments', action='store_true', help='For multi target project do not put external blocks in comment')
        sectionParser.add_argument('--fileMapKey', type=str, help='must match project file fileMap key' )

        for section in codeObj.sections:
            indent = section['indent']
            cmd = section['command'].split()
            if (isinstance(caller.code.params, argparse.Namespace)):
                sectionArgs = argparse.Namespace(**vars(sectionParser.parse_args(cmd)), **vars(args), **vars(caller.code.params), sectionindent=section['indent'])
            else:
                sectionArgs = argparse.Namespace(**vars(sectionParser.parse_args(cmd)), **vars(args), sectionindent=section['indent'])
            # the handler comes from the command parsed from the file. 
            # prepend _handle_ for safety, then lookup the function in this class
            handler = "_handler_" + sectionArgs.handler
            # note that we use the handler in the callers class in case they need to customize or add custom handler
            if hasattr(caller, handler):
                ret = getattr(caller, handler)(sectionArgs, prj, data)
                genOut.append(ret)
            else:
                printError(f"Invalid handler file:{args.file} at line {section['lineNo']}")
                exit(warningAndErrorReport())
        codeObj.genFile(genOut)

    # perform the jinja render
    def render(self, template, data):
        jinjaTemplate = self.templates.get(template, None)
        pythonTemplate =  self.pythonTemplate.get(template, None)
        if jinjaTemplate:
            tm = Template(jinjaTemplate, trim_blocks=True, lstrip_blocks=True)
            msg = tm.render(data=data)
        elif pythonTemplate:
            if isinstance(pythonTemplate, str):
                msg = pythonTemplate
            else:
                msg = pythonTemplate.render(data['args'], data['prj'], data['block'])
        else:
            printError(f"Template {template} does not exist in config file {self.configFile}")
            exit(warningAndErrorReport())
        return msg
        
    # handle non template items in the config    
    def get(self, item):
        ret = self.config.get(item, None)
        if ret is None:
            printError(f"Item {item} does not exist in config file {self.configFile}")
            exit(warningAndErrorReport())

        return (ret)
    
    def loadTemplates(self):
        for template, templateFile in self.config['templates'].items():
            if not os.path.exists(templateFile):
                self.pythonTemplate[template] = f"ERROR: Unable to find {templateFile} in {templateFile} referenced by {template} in config file {self.configFile}"
                continue
            if os.path.splitext(templateFile)[1] != '.py':
                with open(templateFile) as f:
                    self.templates[template] = f.read()
            else:
                # we are importing a python lib
                spec = importlib.util.spec_from_file_location(os.path.splitext(templateFile)[0], templateFile)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                #self.templates[template] = importlib.import_module(os.path.splitext(myFile)[0])
                self.pythonTemplate[template] = module


