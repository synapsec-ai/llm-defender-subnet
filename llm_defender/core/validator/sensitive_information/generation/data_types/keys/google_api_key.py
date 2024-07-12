import random
import string

class Google_API_Key:
    
    def __init__(self):
        self.valid_prefix = 'AIza'
        self.other_valid_prefixes = ['ghp', 'gho', 'ghu', 'ghs', 'ghr']
        self.key_length = 39  

    def generate_valid(self):
        allowed_chars = string.ascii_letters + string.digits + '_-\\'
        remaining_length = self.key_length - len(self.valid_prefix)
        key_body = ''.join(random.choices(allowed_chars, k=remaining_length))
        return self.valid_prefix + key_body

    def generate_invalid_prefix(self):
        invalid_prefix_found = False 
        allowed_chars = string.ascii_letters + string.digits
        while not invalid_prefix_found:
            invalid_prefix=''.join(random.choices(allowed_chars,k=random.randint(3,5)))
            if invalid_prefix != self.valid_prefix and invalid_prefix not in self.other_valid_prefixes:
                invalid_prefix_found = True 
        return invalid_prefix

    def generate_invalid(self):
        if random.choice([True, False]):
            invalid_prefix = self.generate_invalid_prefix()
            allowed_chars = string.ascii_letters + string.digits + '_-\\'
            remaining_length = self.key_length - len(invalid_prefix)
            key_body = ''.join(random.choices(allowed_chars, k=remaining_length))
            return invalid_prefix + key_body
        else:
            allowed_chars = string.ascii_letters + string.digits + '_-\\'
            invalid_length = self.key_length + random.randint(-2,2) 
            key_body = ''.join(random.choices(allowed_chars, k=invalid_length - len(self.valid_prefix)))
            return self.valid_prefix + key_body
