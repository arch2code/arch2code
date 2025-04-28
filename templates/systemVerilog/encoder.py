from jinja2 import Template
import textwrap

# args from generator line
# prj object
# data set dict
def render(args, prj, data):

    out = []
    
    t = Template(encoder_main_j2_template)
    
    s_1 = []
    
    for k, v in data["encoders"].items():
        encoderName = v["encoder"] + 'Encoder'
        encoderType = v["encoderType"]
        enumType = v["enumType"]
        bits = v["totalBits"]
        hexWidth = (bits + 3) // 4
        
        encodingValueList, encodingMaskList = [], []
        
        for itemKey, itemVal in v["items"].items():
            entryBits = int(itemVal["numBitsInt"])
            encodingVal = int(itemVal["encodingValue"])
            encodingMask = int(itemVal["encodingMask"])
            encodingValueList.append(f"{bits}'h{encodingVal:0{hexWidth}x}")
            encodingMaskList.append(f"{bits}'h{encodingMask:0{hexWidth}x}")
        
        if not v["zeroBased"]:
            encodingVal, encodingMask = 0, 0
            encodingValueList.append(f"{bits}'h{encodingVal:0{hexWidth}x}")
            encodingMaskList.append(f"{bits}'h{encodingMask:0{hexWidth}x}")
            
        s_1.append('\n')
        s_1.append(t.render(
            encoderName=encoderName,
            encoderType=encoderType,
            enumType=enumType,
            encodingValueList=textwrap.fill(', '.join(encodingValueList), width=64, break_long_words=False),
            encodingMaskList=textwrap.fill(', '.join(encodingMaskList), width=64, break_long_words=False)
        ))
        s_1.append('\n')
    
    out += s_1
    
    return textwrap.indent(''.join(out), ' '*args.sectionindent)

encoder_main_j2_template = """\
function automatic {{encoderType}} {{encoderName}}Encode ({{encoderType}} tag, {{enumType}} tagType);
    const {{encoderType}} encodingValue[tagType.num()] = {
        {{ encodingValueList | indent(8) }}
    };
    return encodingValue[{tagType}] | tag;
endfunction : {{encoderName}}Encode

function automatic {{enumType}} {{encoderName}}DecodeType ({{encoderType}} tag);
    {{enumType}} tagType;
    const {{encoderType}} encodingValue[tagType.num()] = {
        {{ encodingValueList | indent(8) }}
    };
    const {{encoderType}} encodingMask[tagType.num()] = {
        {{ encodingMaskList | indent(8) }}
    };
    for (tagType = tagType.first(); int'(tagType) <= tagType.num() ; tagType = tagType.next()) begin
        if ((tag & encodingMask[{tagType}]) == encodingValue[{tagType}]) begin
            break;
        end
    end
    return tagType;
endfunction : {{encoderName}}DecodeType

function automatic {{encoderType}} {{encoderName}}DecodeTag ({{encoderType}} tag);
    {{enumType}} tagType = {{encoderName}}DecodeType(tag);
    const {{encoderType}} encodingMask[tagType.num()] = {
        {{ encodingMaskList | indent(8) }}
    };
    return tag & ~encodingMask[{tagType}];
endfunction : {{encoderName}}DecodeTag
"""
