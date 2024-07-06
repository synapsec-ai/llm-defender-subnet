import os
import eth_utils

class ETH_address:

    def generate_valid(self):
        """Generates a valid Ethereum address with EIP-55 checksum."""
        # Generate a random 20-byte hex address
        raw_address = os.urandom(20).hex()
        # Convert to a checksummed address
        checksum_address = eth_utils.to_checksum_address(raw_address)
        return checksum_address

    def generate_invalid(self):
        """Generates an Ethereum address and deliberately makes it invalid by breaking the checksum."""
        # Generate a valid address first
        valid_address = self.generate_valid()
        # Change case of the first letter that can be modified without changing the address itself
        invalid_address = valid_address[:2]
        for str_iter in valid_address[2:]:
            if not str_iter.isdigit():
                out_str = str_iter.swapcase()
            else:
                out_str = str_iter 
            invalid_address += out_str
        return invalid_address

    def verify(self,address):
        """Verifies that an Ethereum address is valid and correctly checksummed per EIP-55."""
        try:
            return address == eth_utils.to_checksum_address(address)
        except ValueError:
            return False