import random

class SE_PIN:
    def calculate_checksum(self, digits):
        """Calculates the checksum"""
        weights = [1, 2] * 5 
        total = 0
        for i, digit in enumerate(digits):
            product = int(digit) * weights[i]
            if weights[i] == 2 and product > 9:
                digits = [digits for digits in str(product)]
                product = sum([int(digit) for digit in digits])
            total += product
        total_last_digit = int([digit for digit in str(total)][-1])
        checksum = 10 - total_last_digit
        return checksum if checksum < 10 else 0

    def generate_valid(self):
        """Generate a valid Swedish Personal Identity Number."""
        year = random.randint(0, 99)
        month = random.randint(1, 12)
        day = random.randint(1, (28 if month == 2 else 30 if month in [4, 6, 9, 11] else 31))
        random_digits = random.randint(100, 999)
        base_number = f"{year:02}{month:02}{day:02}{random_digits:03}"
        checksum_digit = self.calculate_checksum(base_number)
        return f"{base_number[:6]}-{base_number[6:]}{checksum_digit}"

    def generate_invalid(self):
        """Generate an invalid Swedish Personal Identity Number."""
        valid_number = self.generate_valid().replace('-','')
        last_digit = int(valid_number[-1])
        number = valid_number[:-1]
        invalid_digit = (last_digit + random.randint(1, 9)) % 10 
        return f"{number[:6]}-{number[6:]}{invalid_digit}"
    