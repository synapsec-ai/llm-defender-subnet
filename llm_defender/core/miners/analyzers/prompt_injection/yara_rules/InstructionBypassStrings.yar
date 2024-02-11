rule InstructionBypassStrings
{
    meta:
        name = "Instruction Bypass Strings"
        description = "This YARA rule looks for common instruction bypass strings that could be an indication of a prompt injection."
        accuracy = "1.0"
    
    strings:
        $bypass_strings = /(Ignore|Disregard|Skip|Forget|Neglect|Overlook|Omit|Bypass|Ignore previous|Pay no attention to|Do not follow|Do not obey)\s*(prior|previous|preceding|above|foregoing|earlier|initial)?\s*(content|text|instructions|instruction|directives|directive|commands|command|context|conversation|input|inputs|data|message|messages|communication|response|responses|request|requests)\s*(and start over|and start anew|and begin afresh|and start from scratch)?/ nocase
    
    condition:
        $bypass_strings
}
