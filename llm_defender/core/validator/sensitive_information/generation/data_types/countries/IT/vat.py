import random

class IT_VAT:
    def generate_valid(self):
        """Generates a valid Italian VAT number."""
        base = [random.randint(0, 9) for _ in range(10)]  
        checksum = self.calculate_checksum(base)
        base.append(checksum)
        return ''.join(map(str, base))

    def generate_invalid(self):
        """Generates an invalid Italian VAT number."""
        base = [random.randint(0, 9) for _ in range(10)]
        checksum = self.calculate_checksum(base)
        invalid_checksum = (checksum + 1) % 10 
        base.append(invalid_checksum)
        return ''.join(map(str, base))

    def calculate_checksum(self, digits):
        """Calculates the checksum for an Italian VAT number."""
        weights = [1, 2] * 5  
        total = 0
        for i, digit in enumerate(digits):
            product = digit * weights[i]
            if weights[i] == 2 and product > 9:
                digits = [digits for digits in str(product)]
                product = sum([int(digit) for digit in digits])
            total += product
        checksum = 10 - (total % 10)
        return checksum if checksum < 10 else 0