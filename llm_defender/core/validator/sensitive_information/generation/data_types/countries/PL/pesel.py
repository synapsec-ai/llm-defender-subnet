import random
from datetime import datetime, timedelta

class PL_PESEL:

    def generate_valid(self):
        """Generates a valid Polish PESEL number."""
        birth_date = self.random_date()
        serial = random.randint(100, 999)
        sex_digit = random.choice([0, 1, 2, 3, 4, 5, 6, 7, 8, 9])  # Even for female, odd for male
        month = birth_date.month + (20 if birth_date.year >= 2000 else 0)
        pesel_base = f"{birth_date.year % 100:02d}{month:02d}{birth_date.day:02d}{serial:03d}{sex_digit}"
        pesel_base = [int(digit) for digit in pesel_base]
        checksum = self.calculate_checksum(pesel_base)
        return ''.join(map(str, pesel_base)) + str(checksum)

    def generate_invalid(self):
        """Generates an invalid Polish PESEL number."""
        valid_pesel = self.generate_valid()
        pesel_list = list(valid_pesel)
        wrong_digit = (int(pesel_list[-1]) + 5) % 10  # Alter the checksum digit
        pesel_list[-1] = str(wrong_digit)
        return ''.join(pesel_list)

    def calculate_checksum(self, digits):
        """Calculates the checksum for a Polish PESEL number."""
        weights = [1, 3, 7, 9, 1, 3, 7, 9, 1, 3]
        checksum = sum(w * d for w, d in zip(weights, digits))
        return (10 - checksum % 10) % 10

    def random_date(self):
        """Generates a random date for the birth date part of the PESEL."""
        start_date = datetime.strptime("1900-01-01", "%Y-%m-%d")
        end_date = datetime.today()
        time_between_dates = end_date - start_date
        days_between_dates = time_between_dates.days
        random_number_of_days = random.randrange(days_between_dates)
        random_date = start_date + timedelta(days=random_number_of_days)
        return random_date