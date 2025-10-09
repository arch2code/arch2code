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
        out.append(f'class {className} : public encoderBase< {v["encoderType"]}, {v["enumType"]} >')
        out.append('{')
        out.append(f'public:')
        out.append(f'    {className}() : encoderBase< {v["encoderType"]}, {v["enumType"]} >(')
        out.append(f'        {{   // encVal    encMask     max       hex width       name')
        for itemKey, itemVal in v["items"].items():
            entryBits = int(itemVal["numBitsInt"])
            encodingVal = int(itemVal["encodingValue"])
            encodingMask = int(itemVal["encodingMask"])
            out.append(f'            {{ 0x{encodingVal:0{hexWidth}x}, 0x{encodingMask:0{hexWidth}x}, (uint64_t)1<<{itemVal["numBits"]}, (({itemVal["numBits"]} + 3) >> 2), "{itemKey}", "{itemVal["varName"]}"}},')
        if v["zeroBased"] == 1:
            zeroBased = "true"
        else:
            zeroBased = "false"
            encodingVal = 0
            encodingMask = 0
            out.append(f'            {{ 0x{encodingVal:0{hexWidth}x}, 0x{encodingMask:0{hexWidth}x}, (uint64_t)1<<{bits}, {hexWidth}, "{v["extendedRangeItem"]}", ""}}')
        out.append(f'        }}, {v["totalBits"]}, 0x{v["encodeMax"]:0{hexWidth}x}, {zeroBased}) {{}}')
        out.append(f'}};')

    # take the list and return a string
    return("\n".join(out))
