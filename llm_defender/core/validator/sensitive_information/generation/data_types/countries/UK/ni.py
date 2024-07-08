import random
import string

class UK_NI:
    def __init__(self):
        self.valid_prefix_letters = "ABCDEFGHJKLMNOPRSTWXYZ"
        self.invalid_prefix_letters = "DFIQUV"
        self.invalid_prefixes = ["BG", "GB", "NK", "KN", "TN", "NT", "ZZ"]
        self.valid_suffix_letters = "ABCD"
        self.invalid_suffix_letters = "EFGHIJKLMNOPQRSTUVWXYZ"

    def generate_valid(self):
        while True:
            prefix = ''.join(random.choices(self.valid_prefix_letters, k=2))
            if prefix not in self.invalid_prefixes and prefix[1] != 'O' and prefix[0] not in self.invalid_prefix_letters and prefix[1] in self.invalid_prefix_letters:
                break
        digits = ''.join(random.choices(string.digits, k=6))
        suffix = random.choice(self.valid_suffix_letters)
        return f"{prefix}{digits}{suffix}"

    def generate_invalid(self):
        while True:
            prefix = ''.join(random.choices(self.valid_prefix_letters + self.invalid_prefix_letters, k=2))
            if prefix in self.invalid_prefixes or prefix[1] == 'O' or prefix[0] in self.invalid_prefix_letters or prefix[1] in self.invalid_prefix_letters:
                break
        prefix = ''.join(random.choices(self.invalid_prefix_letters, k=2))
        digits = ''.join(random.choices(string.digits, k=6))
        suffix = random.choice(self.invalid_suffix_letters)
        return f"{prefix}{digits}{suffix}"
