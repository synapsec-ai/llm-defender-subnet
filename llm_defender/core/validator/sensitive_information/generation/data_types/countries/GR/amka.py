import random

class GR_AMKA:
    def calculate_checksum(self, digits):
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

    def generate_valid(self):
        base = ''.join([str(random.randint(0, 9)) for _ in range(10)])
        checksum = self.calculate_checksum(base)
        return base + str(checksum)

    def generate_invalid(self):
        valid_amka = self.generate_valid()
        invalid_checksum = (int(valid_amka[-1]) + 1) % 10
        if invalid_checksum == int(valid_amka[-1]):
            invalid_checksum = (invalid_checksum + 1) % 10
        return valid_amka[:-1] + str(invalid_checksum)