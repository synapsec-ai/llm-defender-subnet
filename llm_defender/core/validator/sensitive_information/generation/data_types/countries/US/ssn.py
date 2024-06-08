import random

class US_SSN:

    def __init__(self):
        self.invalid_dividers = ' .,:;*&%$#@!?][}{_'

    def generate_valid(self):
        """
        Generates a string that matches the format of a U.S. Social Security Number (SSN). This function ensures the
        generated SSN does not include restricted or invalid numbers.
        
        Returns:
        - str: A string formatted like a valid U.S. SSN.
        """
        # Generate a valid Area Number (not 000, 666, or 900-999)
        area = random.randint(1, 899)
        if area == 666:  
            area = random.choice([random.randint(1,665), random.randint(667,899)])
        area = f"{area:03d}"  
        
        # Generate a valid Group Number (not 00)
        group = random.randint(1, 99)
        group = f"{group:02d}"  
        
        # Generate a valid Serial Number (not 0000)
        serial = random.randint(1, 9999)
        serial = f"{serial:04d}"  
        
        return f"{area}-{group}-{serial}"
    
    def generate_invalid(self):
        """
        Generates a string that is formatted like a U.S. Social Security Number (SSN) but is
        guaranteed to be invalid. 
        
        Returns:
        - str: A string formatted like an SSN but intentionally invalid.
        """
        # Choose a type of invalidity
        invalid_type = random.choice(['restricted_area', 'zero_group', 'zero_serial', 'out_of_range_area'])

        if random.randint(1,10) == 1:
            divider = random.choice(self.invalid_dividers)
        else:
            divider = '-'
        
        if invalid_type == 'restricted_area':
            # Use an area number that is never valid (e.g., 666 or 900-999)
            area = random.choice(['666'] + [f"{n:03d}" for n in range(900, 1000)])
        elif invalid_type == 'zero_group':
            # Use a valid area but make the group number 00
            area = f"{random.randint(1, 899):03d}"
            if area == '666':  
                area = '667'
            return f"{area}{divider}00{divider}{random.randint(1, 9999):04d}"
        elif invalid_type == 'zero_serial':
            # Use a valid area and group but make the serial number 0000
            area = f"{random.randint(1, 899):03d}"
            if area == '666':  
                area = '667'
            group = f"{random.randint(1, 99):02d}"
            return f"{area}{divider}{group}-0000"
        else:  # 'out_of_range_area'
            # Use an area number out of the entire possible range
            area = random.choice(['000'] + [f"{n:03d}" for n in range(1000, 9999)])
        
        group = f"{random.randint(1, 99):02d}"
        serial = f"{random.randint(1, 9999):04d}"

        return f"{area}{divider}{group}{divider}{serial}"

    def verify(self,ssn):
        """
        Checks if a given Social Security Number (SSN) is potentially valid based on its format
        and certain rules about the issuance of SSNs. This does not include a checksum verification,
        as SSNs do not use a checksum, but it does include checks for known invalid patterns.
        
        Args:
        - ssn (str): The SSN to validate, expected to be in the format "AAA-GG-SSSS".
        
        Returns:
        - bool: True if the SSN is potentially valid, False otherwise.
        
        """
        # Validate format
        if not isinstance(ssn, str) or len(ssn) != 11 or ssn[3] != '-' or ssn[5] == '-':
            return False
        
        for number in ssn:
            if number not in ['-','0','1','2','3','4','5','6','7','8','9']:
                return False
        
        area, group, serial = ssn.split('-')
        
        # Check for invalid patterns
        if (area == "000" or group == "00" or serial == "0000" or
            area == "666" or int(area) > 899):
            return False
        
        return True