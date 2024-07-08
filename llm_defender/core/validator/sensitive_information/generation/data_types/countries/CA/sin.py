import random

class CA_SIN:
    def generate_valid(self):
        """Generate a valid Canadian Social Insurance Number (SIN)."""
        base = [random.randint(0, 9) for _ in range(8)]  
        checksum = self.calculate_checksum(base)  
        base.append(checksum)
        return ''.join(str(digit) for digit in base)

    def generate_invalid(self):
        """Generate an invalid Canadian SIN by generating a valid one and then altering the checksum."""
        valid_sin = self.generate_valid()
        invalid_sin = list(valid_sin)
        last_digit = int(valid_sin[-1])
        invalid_digit = (last_digit + random.randint(1, 9)) % 10
        invalid_sin[-1] = str(invalid_digit)
        return ''.join(invalid_sin)

    def calculate_checksum(self, digits):
        """Calculates the checksum"""
        weights = [1, 2] * 4 
        total = 0
        for i, digit in enumerate(digits):
            product = digit * weights[i]
            if weights[i] == 2 and product > 9:
                digits = [digits for digits in str(product)]
                product = sum([int(digit) for digit in digits])
            total += product
        checksum = 10 - (total % 10)
        return checksum if checksum < 10 else 0

