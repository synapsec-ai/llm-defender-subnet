import random 
import re 

class IPv6_Address:

    def __init__(self):
        self.random_chars = [k for k in '&;-_']
        self.hex_chars = [k for k in '1234567890ABCDEF']
        self.not_hex_chars = [k for k in 'GHIJKLMNOPQRSTUVWXYZ']

    def _generate_valid_hex_number(self):
        # Generate a random integer between 0 and 65535 (inclusive)
        # because 65535 is the maximum value for a four-digit hexadecimal (FFFF in hex)
        random_number = random.randint(0, 65535)
        # Format the number as a hexadecimal with four digits, padded with zeros if necessary
        hex_number = format(random_number, '04X')
        return str(hex_number).upper()

    def _generate_invalid_hex_number(self):
        random_int = random.randint(1,15)
        # three digits 
        if random_int == 1:
            random_int1 = random.randint(1,6)
            # first digit invalid 
            if random_int1 == 1:
                d1 = random.choice(self.not_hex_chars)
                d2 = random.choice(self.hex_chars)
                d3 = random.choice(self.hex_chars)
                return f"{d1}{d2}{d3}"  
            
            # second digit invalid 
            elif random_int1 == 2:
                d1 = random.choice(self.hex_chars)
                d2 = random.choice(self.not_hex_chars)
                d3 = random.choice(self.hex_chars)
                return f"{d1}{d2}{d3}"  
            
            # third digit invalid 
            elif random_int1 == 3:
                d1 = random.choice(self.hex_chars)
                d2 = random.choice(self.hex_chars)
                d3 = random.choice(self.not_hex_chars)
                return f"{d1}{d2}{d3}"  

            # first and second digits invalid 
            elif random_int1 == 4:
                d1 = random.choice(self.not_hex_chars)
                d2 = random.choice(self.not_hex_chars)
                d3 = random.choice(self.hex_chars)
                return f"{d1}{d2}{d3}"  
            
            # second and third digits invalid 
            elif random_int1 == 5:
                d1 = random.choice(self.hex_chars)
                d2 = random.choice(self.not_hex_chars)
                d3 = random.choice(self.not_hex_chars)
                return f"{d1}{d2}{d3}"  
                
            # all digits invalid 
            else:
                d1 = random.choice(self.not_hex_chars)
                d2 = random.choice(self.not_hex_chars)
                d3 = random.choice(self.not_hex_chars)
                return f"{d1}{d2}{d3}"  
            
        # five digits         
        elif random_int == 2:
            random_int2 = random.randint(1,30)
            # first digit invalid 
            if random_int2 == 1:
                d1 = random.choice(self.not_hex_chars)
                d2 = random.choice(self.hex_chars)
                d3 = random.choice(self.hex_chars)
                d4 = random.choice(self.hex_chars)
                d5 = random.choice(self.hex_chars)
                return f"{d1}{d2}{d3}{d4}{d5}"  

            # second digit invalid 
            elif random_int2 == 2:
                d1 = random.choice(self.hex_chars)
                d2 = random.choice(self.not_hex_chars)
                d3 = random.choice(self.hex_chars)
                d4 = random.choice(self.hex_chars)
                d5 = random.choice(self.hex_chars)
                return f"{d1}{d2}{d3}{d4}{d5}"  

            # third digit invalid 
            elif random_int2 == 3:
                d1 = random.choice(self.hex_chars)
                d2 = random.choice(self.hex_chars)
                d3 = random.choice(self.not_hex_chars)
                d4 = random.choice(self.hex_chars)
                d5 = random.choice(self.hex_chars)
                return f"{d1}{d2}{d3}{d4}{d5}"  

            # fourth digit invalid 
            elif random_int2 == 4:
                d1 = random.choice(self.hex_chars)
                d2 = random.choice(self.hex_chars)
                d3 = random.choice(self.hex_chars)
                d4 = random.choice(self.not_hex_chars)
                d5 = random.choice(self.hex_chars)
                return f"{d1}{d2}{d3}{d4}{d5}"  

            # first and second digits invalid 
            elif random_int2 == 5:
                d1 = random.choice(self.not_hex_chars)
                d2 = random.choice(self.not_hex_chars)
                d3 = random.choice(self.hex_chars)
                d4 = random.choice(self.hex_chars)
                d5 = random.choice(self.hex_chars)
                return f"{d1}{d2}{d3}{d4}{d5}"  

            # first and third digits invalid 
            elif random_int2 == 6:
                d1 = random.choice(self.not_hex_chars)
                d2 = random.choice(self.hex_chars)
                d3 = random.choice(self.not_hex_chars)
                d4 = random.choice(self.hex_chars)
                d5 = random.choice(self.hex_chars)
                return f"{d1}{d2}{d3}{d4}{d5}"  

            # first and fourth digits invalid 
            elif random_int2 == 7:
                d1 = random.choice(self.not_hex_chars)
                d2 = random.choice(self.hex_chars)
                d3 = random.choice(self.hex_chars)
                d4 = random.choice(self.not_hex_chars)
                d5 = random.choice(self.hex_chars)
                return f"{d1}{d2}{d3}{d4}{d5}"  

            # first and fifth digits invalid 
            elif random_int2 == 8:
                d1 = random.choice(self.not_hex_chars)
                d2 = random.choice(self.hex_chars)
                d3 = random.choice(self.hex_chars)
                d4 = random.choice(self.hex_chars)
                d5 = random.choice(self.not_hex_chars)
                return f"{d1}{d2}{d3}{d4}{d5}"  

            # second and third digits invalid 
            elif random_int2 == 9:
                d1 = random.choice(self.hex_chars)
                d2 = random.choice(self.not_hex_chars)
                d3 = random.choice(self.not_hex_chars)
                d4 = random.choice(self.hex_chars)
                d5 = random.choice(self.hex_chars)
                return f"{d1}{d2}{d3}{d4}{d5}"  

            # second and fourth digits invalid 
            elif random_int2 == 10:
                d1 = random.choice(self.hex_chars)
                d2 = random.choice(self.not_hex_chars)
                d3 = random.choice(self.hex_chars)
                d4 = random.choice(self.not_hex_chars)
                d5 = random.choice(self.hex_chars)
                return f"{d1}{d2}{d3}{d4}{d5}"  
            
            # second and fifth digits invalid 
            elif random_int2 == 11:
                d1 = random.choice(self.hex_chars)
                d2 = random.choice(self.not_hex_chars)
                d3 = random.choice(self.hex_chars)
                d4 = random.choice(self.hex_chars)
                d5 = random.choice(self.not_hex_chars)
                return f"{d1}{d2}{d3}{d4}{d5}"  

            # third and fourth digits invalid 
            elif random_int2 == 12:
                d1 = random.choice(self.hex_chars)
                d2 = random.choice(self.hex_chars)
                d3 = random.choice(self.not_hex_chars)
                d4 = random.choice(self.not_hex_chars)
                d5 = random.choice(self.hex_chars)
                return f"{d1}{d2}{d3}{d4}{d5}"  

            # third and fifth digits invalid 
            elif random_int2 == 13:
                d1 = random.choice(self.hex_chars)
                d2 = random.choice(self.hex_chars)
                d3 = random.choice(self.not_hex_chars)
                d4 = random.choice(self.hex_chars)
                d5 = random.choice(self.not_hex_chars)
                return f"{d1}{d2}{d3}{d4}{d5}"      

            # fourth and fifth digits invalid 
            elif random_int2 == 14:
                d1 = random.choice(self.hex_chars)
                d2 = random.choice(self.hex_chars)
                d3 = random.choice(self.hex_chars)
                d4 = random.choice(self.not_hex_chars)
                d5 = random.choice(self.not_hex_chars)
                return f"{d1}{d2}{d3}{d4}{d5}"  

            # first second and third digits invalid 
            elif random_int2 == 15:
                d1 = random.choice(self.not_hex_chars)
                d2 = random.choice(self.not_hex_chars)
                d3 = random.choice(self.not_hex_chars)
                d4 = random.choice(self.hex_chars)
                d5 = random.choice(self.hex_chars)
                return f"{d1}{d2}{d3}{d4}{d5}"  

            # first second and fourth digits invalid 
            elif random_int2 == 16:
                d1 = random.choice(self.not_hex_chars)
                d2 = random.choice(self.not_hex_chars)
                d3 = random.choice(self.hex_chars)
                d4 = random.choice(self.not_hex_chars)
                d5 = random.choice(self.hex_chars)
                return f"{d1}{d2}{d3}{d4}{d5}"  

            # first second and fifth digits invalid 
            elif random_int2 == 17:
                d1 = random.choice(self.not_hex_chars)
                d2 = random.choice(self.not_hex_chars)
                d3 = random.choice(self.hex_chars)
                d4 = random.choice(self.hex_chars)
                d5 = random.choice(self.not_hex_chars)
                return f"{d1}{d2}{d3}{d4}{d5}"  

            # first third and fourth digits invalid 
            elif random_int2 == 18:
                d1 = random.choice(self.not_hex_chars)
                d2 = random.choice(self.hex_chars)
                d3 = random.choice(self.not_hex_chars)
                d4 = random.choice(self.not_hex_chars)
                d5 = random.choice(self.hex_chars)
                return f"{d1}{d2}{d3}{d4}{d5}"  

            # first third and fifth digits invalid 
            elif random_int2 == 19:
                d1 = random.choice(self.not_hex_chars)
                d2 = random.choice(self.hex_chars)
                d3 = random.choice(self.not_hex_chars)
                d4 = random.choice(self.hex_chars)
                d5 = random.choice(self.not_hex_chars)
                return f"{d1}{d2}{d3}{d4}{d5}"  

            # first fourth and fifth digits invalid 
            elif random_int2 == 20:
                d1 = random.choice(self.not_hex_chars)
                d2 = random.choice(self.hex_chars)
                d3 = random.choice(self.hex_chars)
                d4 = random.choice(self.not_hex_chars)
                d5 = random.choice(self.not_hex_chars)
                return f"{d1}{d2}{d3}{d4}{d5}"  

            # second third and fourth digits invalid 
            elif random_int2 == 21:
                d1 = random.choice(self.hex_chars)
                d2 = random.choice(self.not_hex_chars)
                d3 = random.choice(self.not_hex_chars)
                d4 = random.choice(self.not_hex_chars)
                d5 = random.choice(self.hex_chars)
                return f"{d1}{d2}{d3}{d4}{d5}"  

            # second fourth and fifth digits invalid 
            elif random_int2 == 22:
                d1 = random.choice(self.hex_chars)
                d2 = random.choice(self.not_hex_chars)
                d3 = random.choice(self.hex_chars)
                d4 = random.choice(self.not_hex_chars)
                d5 = random.choice(self.not_hex_chars)
                return f"{d1}{d2}{d3}{d4}{d5}"  

            # second third and fifth digits invalid
            elif random_int2 == 23:
                d1 = random.choice(self.hex_chars)
                d2 = random.choice(self.not_hex_chars)
                d3 = random.choice(self.not_hex_chars)
                d4 = random.choice(self.hex_chars)
                d5 = random.choice(self.not_hex_chars)
                return f"{d1}{d2}{d3}{d4}{d5}"  

            # third fourth and fifth digits invalid 
            elif random_int2 == 24:
                d1 = random.choice(self.hex_chars)
                d2 = random.choice(self.hex_chars)
                d3 = random.choice(self.not_hex_chars)
                d4 = random.choice(self.not_hex_chars)
                d5 = random.choice(self.not_hex_chars)
                return f"{d1}{d2}{d3}{d4}{d5}"  
                
            # first second third and fourth digits invalid
            elif random_int2 == 25:
                d1 = random.choice(self.not_hex_chars)
                d2 = random.choice(self.not_hex_chars)
                d3 = random.choice(self.not_hex_chars)
                d4 = random.choice(self.not_hex_chars)
                d5 = random.choice(self.hex_chars)
                return f"{d1}{d2}{d3}{d4}{d5}"  

            # first third fourth and fifth digits invalid 
            elif random_int2 == 26:
                d1 = random.choice(self.not_hex_chars)
                d2 = random.choice(self.hex_chars)
                d3 = random.choice(self.not_hex_chars)
                d4 = random.choice(self.not_hex_chars)
                d5 = random.choice(self.not_hex_chars)
                return f"{d1}{d2}{d3}{d4}{d5}"  

            # first second third and fifth digits invalid 
            elif random_int2 == 27:
                d1 = random.choice(self.not_hex_chars)
                d2 = random.choice(self.not_hex_chars)
                d3 = random.choice(self.not_hex_chars)
                d4 = random.choice(self.hex_chars)
                d5 = random.choice(self.not_hex_chars)
                return f"{d1}{d2}{d3}{d4}{d5}"  

            # first third fourth and fifth digits invalid 
            elif random_int2 == 28:
                d1 = random.choice(self.not_hex_chars)
                d2 = random.choice(self.hex_chars)
                d3 = random.choice(self.not_hex_chars)
                d4 = random.choice(self.not_hex_chars)
                d5 = random.choice(self.not_hex_chars)
                return f"{d1}{d2}{d3}{d4}{d5}"  

            # second third fourth and fifth digits invalid 
            elif random_int2 == 29:
                d1 = random.choice(self.hex_chars)
                d2 = random.choice(self.not_hex_chars)
                d3 = random.choice(self.not_hex_chars)
                d4 = random.choice(self.not_hex_chars)
                d5 = random.choice(self.not_hex_chars)
                return f"{d1}{d2}{d3}{d4}{d5}"  
            
            # all digits invalid 
            else:
                d1 = random.choice(self.not_hex_chars)
                d2 = random.choice(self.not_hex_chars)
                d3 = random.choice(self.not_hex_chars)
                d4 = random.choice(self.not_hex_chars)
                d5 = random.choice(self.not_hex_chars)
                return f"{d1}{d2}{d3}{d4}{d5}"  
                
        # first hex digit invalid
        elif random_int == 3:
            d1 = random.choice(self.not_hex_chars)
            d2 = random.choice(self.hex_chars)
            d3 = random.choice(self.hex_chars)
            d4 = random.choice(self.hex_chars)
            return f"{d1}{d2}{d3}{d4}"            

        # second hex digit invalid 
        elif random_int == 4:
            d1 = random.choice(self.hex_chars)
            d2 = random.choice(self.not_hex_chars)
            d3 = random.choice(self.hex_chars)
            d4 = random.choice(self.hex_chars)
            return f"{d1}{d2}{d3}{d4}"    
        
        # third hex digit invalid
        elif random_int == 5:
            d1 = random.choice(self.hex_chars)
            d2 = random.choice(self.hex_chars)
            d3 = random.choice(self.not_hex_chars)
            d4 = random.choice(self.hex_chars)
            return f"{d1}{d2}{d3}{d4}"    
        
        # fourth hex digit invalid 
        elif random_int == 6:
            d1 = random.choice(self.hex_chars)
            d2 = random.choice(self.hex_chars)
            d3 = random.choice(self.hex_chars)
            d4 = random.choice(self.not_hex_chars)
            return f"{d1}{d2}{d3}{d4}"    
        
        # first and second hex digit invalid 
        elif random_int == 7:
            d1 = random.choice(self.not_hex_chars)
            d2 = random.choice(self.not_hex_chars)
            d3 = random.choice(self.hex_chars)
            d4 = random.choice(self.hex_chars)
            return f"{d1}{d2}{d3}{d4}"    
        
        # first and third hex digit invalid 
        elif random_int == 8:
            d1 = random.choice(self.not_hex_chars)
            d2 = random.choice(self.hex_chars)
            d3 = random.choice(self.not_hex_chars)
            d4 = random.choice(self.hex_chars)
            return f"{d1}{d2}{d3}{d4}"    
            
        # first and fourth hex digit invalid 
        elif random_int == 9:
            d1 = random.choice(self.not_hex_chars)
            d2 = random.choice(self.hex_chars)
            d3 = random.choice(self.hex_chars)
            d4 = random.choice(self.not_hex_chars)
            return f"{d1}{d2}{d3}{d4}"    
        
        # second and third hex digit invalid 
        elif random_int == 10:
            d1 = random.choice(self.hex_chars)
            d2 = random.choice(self.not_hex_chars)
            d3 = random.choice(self.not_hex_chars)
            d4 = random.choice(self.hex_chars)
            return f"{d1}{d2}{d3}{d4}"    
        
        # second and fourth hex digit invalid 
        elif random_int == 11:
            d1 = random.choice(self.hex_chars)
            d2 = random.choice(self.not_hex_chars)
            d3 = random.choice(self.hex_chars)
            d4 = random.choice(self.not_hex_chars)
            return f"{d1}{d2}{d3}{d4}"    
        
        # third and fourth hex digit invalid 
        elif random_int == 12:
            d1 = random.choice(self.hex_chars)
            d2 = random.choice(self.hex_chars)
            d3 = random.choice(self.not_hex_chars)
            d4 = random.choice(self.not_hex_chars)
            return f"{d1}{d2}{d3}{d4}"    
        
        # first second and third hex digit invalid 
        elif random_int == 13:
            d1 = random.choice(self.not_hex_chars)
            d2 = random.choice(self.not_hex_chars)
            d3 = random.choice(self.not_hex_chars)
            d4 = random.choice(self.hex_chars)
            return f"{d1}{d2}{d3}{d4}"    
        
        # first second and fourth hex digit invalid 
        elif random_int == 14:
            d1 = random.choice(self.not_hex_chars)
            d2 = random.choice(self.not_hex_chars)
            d3 = random.choice(self.hex_chars)
            d4 = random.choice(self.not_hex_chars)
            return f"{d1}{d2}{d3}{d4}"    
        
        # first third and fourth hex digit invalid 
        elif random_int == 15:
            d1 = random.choice(self.not_hex_chars)
            d2 = random.choice(self.hex_chars)
            d3 = random.choice(self.not_hex_chars)
            d4 = random.choice(self.not_hex_chars)
            return f"{d1}{d2}{d3}{d4}"    
        
        # all hex digits invalid
        else:
            d1 = random.choice(self.not_hex_chars)
            d2 = random.choice(self.not_hex_chars)
            d3 = random.choice(self.not_hex_chars)
            d4 = random.choice(self.not_hex_chars)
            return f"{d1}{d2}{d3}{d4}"    
        
    def generate_valid(self):
        o1 = self._generate_valid_hex_number()
        o2 = self._generate_valid_hex_number()
        o3 = self._generate_valid_hex_number()
        o4 = self._generate_valid_hex_number()
        o5 = self._generate_valid_hex_number()
        o6 = self._generate_valid_hex_number()
        o7 = self._generate_valid_hex_number()
        o8 = self._generate_valid_hex_number()
        random_int = random.randint(1,100)
        if random_int < 60:
            return f"{o1}:{o2}:{o3}:{o4}:{o5}:{o6}:{o7}:{o8}".upper()
        elif random_int == 69:
            if random.choice([True, False]):
                return f"{o1}:{o2}:{o3}:{o4}:{o5}:{o6}::".lower()
            else:
                return f"{o1}:{o2}:{o3}:{o4}::{o7}:{o8}".upper()
        else:
            return f"{o1}:{o2}:{o3}:{o4}:{o5}:{o6}:{o7}:{o8}".lower()

    def generate_invalid(self):
        invalid_used_once = False 
        # o1
        if random.choice([True, False]):
            o1 = self._generate_invalid_hex_number()
            invalid_used_once = True 
        else:
            o1 = self._generate_valid_hex_number()

        # o2
        if random.choice([True, False]):
            o2 = self._generate_invalid_hex_number()
            invalid_used_once = True 
        else:
            o2 = self._generate_valid_hex_number()

        # o3
        if random.choice([True, False]):
            o3 = self._generate_invalid_hex_number()
            invalid_used_once = True 
        else:
            o3 = self._generate_valid_hex_number()

        # o4
        if random.choice([True, False]):
            o4 = self._generate_invalid_hex_number()
            invalid_used_once = True 
        else:
            o4 = self._generate_valid_hex_number()

        # o5
        if random.choice([True, False]):
            o5 = self._generate_invalid_hex_number()
            invalid_used_once = True 
        else:
            o5 = self._generate_valid_hex_number()

        # o6
        if random.choice([True, False]):
            o6 = self._generate_invalid_hex_number()
            invalid_used_once = True 
        else:
            o6 = self._generate_valid_hex_number()

        # o7
        if random.choice([True, False]):
            o7 = self._generate_invalid_hex_number()
            invalid_used_once = True 
        else:
            o7 = self._generate_valid_hex_number()

        # o8
        if not invalid_used_once:
            o8 = self._generate_invalid_hex_number()
        else:
            if random.choice([True, False]):
                o8 = self._generate_invalid_hex_number()
            else:
                o8 = self._generate_valid_hex_number()

        # use : as middle char
        if random.randint(1,10) > 2:
            sc = ":"
        # use another random char as middle char
        else:
            sc = random.choice(self.random_chars)

        return f"{o1}{sc}{o2}{sc}{o3}{sc}{o4}{sc}{o5}{sc}{o6}{sc}{o7}{sc}{o8}"
    

        
