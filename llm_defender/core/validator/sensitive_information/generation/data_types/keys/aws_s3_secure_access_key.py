import random
import string

class AWS_S3_secret_access_key:
        
    def generate_valid(self):
        """Generates a valid AWS S3 Secret Access Key."""
        return self.generate_key(40, (string.ascii_letters + string.digits + "/+"))

    def generate_invalid(self):
        """Generates an invalid AWS S3 Secret Access Key by using an incorrect length or characters."""
        length = random.choice([random.randint(35,39),random.randint(41,45)]) 
        return self.generate_key(length, (string.ascii_letters + string.digits + "/+"))

    def generate_key(self, length, chars):
        """Helper function to generate a key of a specified length from specified characters."""
        return ''.join(random.choice(chars) for _ in range(length))