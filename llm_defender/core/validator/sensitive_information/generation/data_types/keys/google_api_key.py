import random
import string

class Google_API_Key:
    
    def __init__(self):
        self.valid_prefix = 'AIza'
        self.other_valid_prefixes = ['ghp', 'gho', 'ghu', 'ghs', 'ghr']
        self.key_length = 39  # Total length

    def generate_valid(self):
        # Characters allowed in the API key after the prefix
        allowed_chars = string.ascii_letters + string.digits + '_-\\'
        # Generate the remaining part of the key
        remaining_length = self.key_length - len(self.valid_prefix)
        key_body = ''.join(random.choices(allowed_chars, k=remaining_length))
        return self.valid_prefix + key_body

    def generate_invalid_prefix(self):
        invalid_prefix_found = False 
        while not invalid_prefix_found:
            invalid_prefix=''.join(random.choice(string.ascii_letters + string.digits),k=random.randint(3,5))
            if invalid_prefix != self.valid_prefix and invalid_prefix not in self.other_valid_prefixes:
                invalid_prefix_found = True 
        return invalid_prefix

    def generate_invalid(self):
        # Generate with invalid prefix or invalid length
        if random.choice([True, False]):
            # Invalid prefix
            invalid_prefix = self.generate_invalid_prefix()  # Incorrect prefix
            allowed_chars = string.ascii_letters + string.digits + '_-\\'
            remaining_length = self.key_length - len(invalid_prefix) + random.randint()
            key_body = ''.join(random.choices(allowed_chars, k=remaining_length))
            return invalid_prefix + key_body
        else:
            # Invalid length
            allowed_chars = string.ascii_letters + string.digits + '_-\\'
            invalid_length = self.key_length + random.randint(-2,2)  # Incorrect length
            key_body = ''.join(random.choices(allowed_chars, k=invalid_length - len(self.valid_prefix)))
            return self.valid_prefix + key_body