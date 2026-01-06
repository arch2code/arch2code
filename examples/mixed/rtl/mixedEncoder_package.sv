package mixedEncoderPackage;

    import mixed_package::*;

    // GENERATED_CODE_PARAM --context=mixed.yaml
    // GENERATED_CODE_BEGIN --template=encoder

    function automatic opcodeTagT opcodeEnAEncoderEncode (opcodeTagT tag, opcodeEnumT tagType);
        const opcodeTagT encodingValue[tagType.num()] = {
            9'h000, 9'h040, 9'h080, 9'h0c0, 9'h100
        };
        return encodingValue[{tagType}] | tag;
    endfunction : opcodeEnAEncoderEncode

    function automatic opcodeEnumT opcodeEnAEncoderDecodeType (opcodeTagT tag);
        opcodeEnumT tagType;
        const opcodeTagT encodingValue[tagType.num()] = {
            9'h000, 9'h040, 9'h080, 9'h0c0, 9'h100
        };
        const opcodeTagT encodingMask[tagType.num()] = {
            9'h1c0, 9'h1c0, 9'h1c0, 9'h1c0, 9'h1fe
        };
        for (tagType = tagType.first(); int'(tagType) <= tagType.num() ; tagType = tagType.next()) begin
            if ((tag & encodingMask[{tagType}]) == encodingValue[{tagType}]) begin
                break;
            end
        end
        return tagType;
    endfunction : opcodeEnAEncoderDecodeType

    function automatic opcodeTagT opcodeEnAEncoderDecodeTag (opcodeTagT tag);
        opcodeEnumT tagType = opcodeEnAEncoderDecodeType(tag);
        const opcodeTagT encodingMask[tagType.num()] = {
            9'h1c0, 9'h1c0, 9'h1c0, 9'h1c0, 9'h1fe
        };
        return tag & ~encodingMask[{tagType}];
    endfunction : opcodeEnAEncoderDecodeTag

    // GENERATED_CODE_END

endpackage : mixedEncoderPackage
