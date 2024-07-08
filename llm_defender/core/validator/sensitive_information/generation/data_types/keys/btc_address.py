import os
import hashlib
import base58
import random

class BTC_address:

    def generate_valid(self):
        """Generates a valid Bitcoin address."""
        pubkey_hash = os.urandom(20)
        return BTC_address.encode_address(pubkey_hash, b'\x00')  

    def generate_invalid(self):
        """Generates an invalid Bitcoin address by altering the checksum."""
        pubkey_hash = os.urandom(20)
        valid_address = BTC_address.encode_address(pubkey_hash, b'\x00')
        if random.choice([True, False]):
            invalid_char = '0' if valid_address[-1] != '0' else '1'
            return valid_address[:-1] + invalid_char
        else:
            if random.choice([True, False]):
                if random.choice([True, False]):
                    return valid_address[2:-3]
                else:
                    return valid_address[3:-2]
            else:
                if random.choice([True, False]):
                    return valid_address[2:]
                else:
                    return valid_address[1:-1]

    @staticmethod
    def encode_address(pubkey_hash, version_byte):
        """Encodes the public key hash into a Bitcoin address."""
        vh160 = version_byte + pubkey_hash
        hash = hashlib.sha256(hashlib.sha256(vh160).digest()).digest()
        addr = base58.b58encode(vh160 + hash[:4])
        return addr.decode('utf-8')