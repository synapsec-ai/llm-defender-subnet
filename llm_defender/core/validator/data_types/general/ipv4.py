import random 
import string
import re
import time

class IPv4_Address:

    def __init__(self):
        self.release_version = 1
        self.has_checksum = False 
        self.ipv4_pattern = re.compile(
            r'^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}'
            r'(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
        )
        self.random_chars = [k for k in '!@#$%^&*']

    def _generate_valid_octet(self):
        return str(random.randint(0, 255))

    def _generate_invalid_octet(self):
        random_int = random.randint(1,10)
        if random_int == 1:
            return ''.join(random.choices((string.ascii_letters + "`~!@#$%^&*(){[]}<>,.?/"), k=random.randint(1, 3)))
        else:
            return str(random.randint(256,999))

    def generate_valid(self):
        first = self._generate_valid_octet()
        second = self._generate_valid_octet()
        third = self._generate_valid_octet()
        fourth = self._generate_valid_octet()
        return f"{first}.{second}.{third}.{fourth}"

    def generate_invalid(self):
        random_int = random.randint(1,18)
        # three valid octets, not four
        if random_int == 1:
            first = self._generate_valid_octet()
            second = self._generate_valid_octet()
            third = self._generate_valid_octet()
            return f"{first}.{second}.{third}"
        
        # five valid octets, not four  
        elif random_int == 2:
            first = self._generate_valid_octet()
            second = self._generate_valid_octet()
            third = self._generate_valid_octet()
            fourth = self._generate_valid_octet()
            fifth = self._generate_valid_octet()
            return f"{first}.{second}.{third}.{fourth}.{fifth}"
        
        # random chars, not periods
        elif random_int == 3:
            first = self._generate_valid_octet()
            second = self._generate_valid_octet()
            third = self._generate_valid_octet()
            fourth = self._generate_valid_octet()
            random_char = random.choice(self.random_chars)
            return f"{first}{random_char}{second}{random_char}{third}{random_char}{fourth}"
        
        # first octet invalid
        elif random_int == 4:
            first = self._generate_invalid_octet()
            second = self._generate_valid_octet()
            third = self._generate_valid_octet()
            fourth = self._generate_valid_octet()
            return f"{first}.{second}.{third}.{fourth}"

        # second octet invalid
        elif random_int == 5:
            first = self._generate_valid_octet()
            second = self._generate_invalid_octet()
            third = self._generate_valid_octet()
            fourth = self._generate_valid_octet()
            return f"{first}.{second}.{third}.{fourth}"
        
        # third octet invalid
        elif random_int == 6:
            first = self._generate_valid_octet()
            second = self._generate_valid_octet()
            third = self._generate_invalid_octet()
            fourth = self._generate_valid_octet()
            return f"{first}.{second}.{third}.{fourth}"
                
        # fourth octet invalid
        elif random_int == 7:
            first = self._generate_valid_octet()
            second = self._generate_valid_octet()
            third = self._generate_valid_octet()
            fourth = self._generate_invalid_octet()
            return f"{first}.{second}.{third}.{fourth}"
        
        # first and second octet invalid
        elif random_int == 8:
            first = self._generate_invalid_octet()
            second = self._generate_invalid_octet()
            third = self._generate_valid_octet()
            fourth = self._generate_valid_octet()
            return f"{first}.{second}.{third}.{fourth}"
        
        # first and third octet invalid
        elif random_int == 9:
            first = self._generate_invalid_octet()
            second = self._generate_valid_octet()
            third = self._generate_invalid_octet()
            fourth = self._generate_valid_octet()
            return f"{first}.{second}.{third}.{fourth}"
        
        # first and fourth octet invalid
        elif random_int == 10:
            first = self._generate_invalid_octet()
            second = self._generate_valid_octet()
            third = self._generate_valid_octet()
            fourth = self._generate_invalid_octet()
            return f"{first}.{second}.{third}.{fourth}"
        
        # second and third octet invalid
        elif random_int == 11:
            first = self._generate_valid_octet()
            second = self._generate_invalid_octet()
            third = self._generate_invalid_octet()
            fourth = self._generate_valid_octet()
            return f"{first}.{second}.{third}.{fourth}"
        
        # second and fourth octet invalid
        elif random_int == 12:
            first = self._generate_valid_octet()
            second = self._generate_invalid_octet()
            third = self._generate_valid_octet()
            fourth = self._generate_invalid_octet()
            return f"{first}.{second}.{third}.{fourth}"
        
        # third and fourth octet invalid
        elif random_int == 13:
            first = self._generate_valid_octet()
            second = self._generate_valid_octet()
            third = self._generate_invalid_octet()
            fourth = self._generate_invalid_octet()
            return f"{first}.{second}.{third}.{fourth}"
        
        # first, second and third octet invalid
        elif random_int == 14:
            first = self._generate_invalid_octet()
            second = self._generate_invalid_octet()
            third = self._generate_invalid_octet()
            fourth = self._generate_valid_octet()
            return f"{first}.{second}.{third}.{fourth}"
        
        # first, second and fourth octet invalid
        elif random_int == 15:
            first = self._generate_invalid_octet()
            second = self._generate_invalid_octet()
            third = self._generate_valid_octet()
            fourth = self._generate_invalid_octet()
            return f"{first}.{second}.{third}.{fourth}"
        
        # first, third and fourth octet invalid 
        elif random_int == 16:
            first = self._generate_invalid_octet()
            second = self._generate_valid_octet()
            third = self._generate_invalid_octet()
            fourth = self._generate_invalid_octet()
            return f"{first}.{second}.{third}.{fourth}"
        
        # second, third and fourth octet invalid 
        elif random_int == 17:
            first = self._generate_valid_octet()
            second = self._generate_invalid_octet()
            third = self._generate_invalid_octet()
            fourth = self._generate_invalid_octet()
            return f"{first}.{second}.{third}.{fourth}"
        
        # all octets invalid
        else:
            first = self._generate_invalid_octet()
            second = self._generate_invalid_octet()
            third = self._generate_invalid_octet()
            fourth = self._generate_invalid_octet()
            return f"{first}.{second}.{third}.{fourth}"
    