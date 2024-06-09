import random
from pathlib import Path
from wonderwords import RandomSentence 
from datetime import datetime

# Data type imports 
from data_types.general.ipv4 import IPv4_Address
from data_types.general.ipv6 import IPv6_Address
from data_types.general.email import Email
from data_types.countries.US.ssn import US_SSN
from data_types.keys.github_personal_access_token import GitHub_PersonalAccessToken

class SensitiveInfoGenerator:

    def __init__(self):

        self.rs = RandomSentence()
        self.data_types = {
            'IPv4_Address':IPv4_Address(),
            'IPv6_Address':IPv6_Address(),
            'Email':Email(),
            'US_SSN':US_SSN(),
            'GitHub_PersonalAccessToken': GitHub_PersonalAccessToken()
            }

    def generate_sentence_to_insert_into(self):
        output_text = ''
        for i in range(0, random.randint(1,3)):
            random_integer = random.randint(1,4)
            if random_integer == 1:
                output_text += self.rs.sentence() + ' '
            elif random_integer == 2: 
                output_text += self.rs.simple_sentence() + ' '
            elif random_integer == 3:
                output_text += self.rs.bare_bone_with_adjective() + ' '
            else:
                output_text += self.rs.bare_bone_sentence() + ' '
        return output_text[:-1]

    def insert_once(self, sentence_str, insert_str):
        words = sentence_str.split()
        if len(words) < 2:
            return sentence_str + ' ' + insert_str
        insert_index = random.randint(1, len(words) - 1)  
        words[insert_index:insert_index] = [insert_str]
        return ' '.join(words)

    def insert_sensitive_info_into_sentence(self, sensitive_info):
        sentence_str = self.generate_sentence_to_insert_into()
        output_str = self.insert_once(sentence_str=sentence_str, insert_str=sensitive_info)
        return output_str

    def generate_valid(self, data_type):
        """Generates valid instances of data_type"""
        # Check that data_type is correct
        if isinstance(data_type, str) and data_type in [k for k in self.data_types]:

            # Loop until we get a valid instance
            while True:

                # Generate
                valid_instance = self.data_types[data_type].generate_valid()
                
                return self.insert_sensitive_info_into_sentence(valid_instance)

    def generate_invalid(self, data_type):
        "Generates invalid instance of data_type"
        # Check that data_type is correct
        if isinstance(data_type, str) and data_type in [k for k in self.data_types]:

            # Loop until we get a valid instance
            while True:
                
                # Generate
                invalid_instance = self.data_types[data_type].generate_invalid()
                
                return self.insert_sensitive_info_into_sentence(invalid_instance)

    def get_prompt_to_serve_miners(self):

        dtype = random.choice([k for k in self.data_types])
        valid_or_invalid = random.choice(['valid','invalid'])

        if valid_or_invalid == 'valid':
            return self.generate_valid(dtype), dtype, 1, datetime.now().isoformat()
        
        else:   
            return self.generate_invalid(dtype), dtype, 0, datetime.now().isoformat()