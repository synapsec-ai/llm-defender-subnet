import eth_utils
import sha3

from wonderwords import RandomSentence

class ETH_address:
    def __init__(self):
        self.rs = RandomSentence()

    def keccak256_hash(self):
        input_string = self.rs.sentence()
        k = sha3.keccak_256()
        k.update(input_string.encode('utf-8'))
        return ("0x" + k.hexdigest()[-40:])

    def generate_valid(self):
        """Generates a valid Ethereum address with EIP-55 checksum."""
        raw_address = self.keccak256_hash()
        checksum_address = eth_utils.to_checksum_address(raw_address)
        return checksum_address

    def generate_invalid(self):
        """Generates an Ethereum address and deliberately makes it invalid by breaking the checksum."""
        valid_address = self.generate_valid()
        invalid_address = valid_address[:2]
        for str_iter in valid_address[2:]:
            if not str_iter.isdigit():
                out_str = str_iter.swapcase()
            else:
                out_str = str_iter 
            invalid_address += out_str
        return invalid_address
    
if __name__ == '__main__':
    import time 
    e=ETH_address()
    while True:
        v = e.generate_valid()
        print(f"valid: {v} valid check: {eth_utils.is_checksum_formatted_address(v)}")
        i = e.generate_invalid()
        print(f"invalid: {i} invalid check: {eth_utils.is_checksum_formatted_address(i)}")
        time.sleep(5)