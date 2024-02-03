rule HahaPwned
{
    meta:
        name = "Haha Pwned"
        description = "Hackers love to input Haha Pwned in their examples so a prompt must be malicious if such string is contained within"
        accuracy = "1.0"
    
    strings:
        $pwnedOwned = /(haha pwned|haha owned)/ nocase
    condition:
        $pwnedOwned
}
