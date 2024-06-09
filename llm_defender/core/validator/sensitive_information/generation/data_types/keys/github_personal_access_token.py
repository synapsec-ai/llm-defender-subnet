import zlib
import random
import string

class GitHub_PersonalAccessToken:
    def __init__(self):
        self.valid_prefixes = ['ghp', 'gho', 'ghu', 'ghs', 'ghr']

    def _generate_invalid_prefix(self):
        invalid_length = random.randint(2,5)
        prefix = ''.join(random.choices((string.ascii_letters), k=invalid_length)) 
        if prefix not in self.valid_prefixes:
            return prefix + '_'
        else:
            return self._generate_invalid_prefix()

    def calculate_checksum(self, data):
        # Calculate CRC32 checksum
        checksum = zlib.crc32(data.encode('utf-8')) & 0xffffffff
        # Convert checksum to Base62
        return self._to_base62(checksum)

    def _to_base62(self, num):
        chars = string.digits + string.ascii_letters
        base62 = ''
        while num > 0:
            num, rem = divmod(num, 62)
            base62 = chars[rem] + base62
        return base62.zfill(6)
    
    def _replace_chars(self, change_string):
        new_string = '' 
        new_char = ''
        for cs in change_string:
            while new_char != '' and new_char != cs:
                new_char = random.choice((string.ascii_letters + string.digits))
            new_string += new_char
        return new_string
    
    def _get_invalid_checksum(self, data):
        valid_checksum = self.calculate_checksum(data)
        return self._replace_chars(valid_checksum)

    def generate_valid(self):
        prefix = random.choice(self.valid_prefixes) + '_'
        random_part = ''.join(random.choices(string.ascii_letters + string.digits, k=30))
        full_token = prefix + random_part
        return full_token + self.calculate_checksum(full_token)

    def generate_invalid(self):
        if random.choice([True, False, False]):
            # Invalid prefix
            prefix = self._generate_invalid_prefix()
        else:
            # Valid prefix but will corrupt checksum
            prefix = random.choice(self.valid_prefixes) + '_'
        random_part = ''.join(random.choices(string.ascii_letters + string.digits, k=30))
        full_token = prefix + random_part
        return full_token + self._get_invalid_checksum(full_token)