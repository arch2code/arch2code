# args from generator line
# prj object
# data set dict
from pysrc.processYaml import camelCase

def render(args, prj, data):
    # using list to simplify all the last loop special cases to allow simple delete of last entry
    # to effectively backup
    out = list()
    for k, v in data["encoders"].items():
        className = camelCase('encoder', v["encoder"])
        bits = v["totalBits"]
        hexWidth = (bits + 3) // 4 # 4 bits per hex digit rounded up
        out.append(f'class {className} : public encoderBase< {v["encoderType"]}, {v["enumType"]} >\n')
        out.append('{\n')
        out.append(f'public:\n')
        out.append(f'    {className}() : encoderBase< {v["encoderType"]}, {v["enumType"]} >(\n')
        out.append(f'        {{   // encVal    encMask     max       hex width       name\n')
        for itemKey, itemVal in v["items"].items():
            entryBits = int(itemVal["numBitsInt"])
            encodingVal = int(itemVal["encodingValue"])
            encodingMask = int(itemVal["encodingMask"])
            out.append(f'            {{ 0x{encodingVal:0{hexWidth}x}, 0x{encodingMask:0{hexWidth}x}, (uint64_t)1<<{itemVal["numBits"]}, (({itemVal["numBits"]} + 3) >> 2), "{itemKey}", "{itemVal["varName"]}"}},\n')
        if v["zeroBased"] == 1:
            zeroBased = "true"
        else:
            zeroBased = "false"
            encodingVal = 0
            encodingMask = 0
            out.append(f'            {{ 0x{encodingVal:0{hexWidth}x}, 0x{encodingMask:0{hexWidth}x}, (uint64_t)1<<{bits}, {hexWidth}, "{v["extendedRangeItem"]}", ""}}\n')
        out.append(f'        }}, {v["totalBits"]}, 0x{v["encodeMax"]:0{hexWidth}x}, {zeroBased}) {{}}\n')
        out.append(f'}};\n')

    # take the list and return a string
    return("".join(out))
