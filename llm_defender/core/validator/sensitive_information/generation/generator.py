import random
from wonderwords import RandomSentence 

# Data type imports 
from .data_types.general.ipv4 import IPv4_Address
from .data_types.general.ipv6 import IPv6_Address
from .data_types.general.email import Email
from .data_types.countries.US.ssn import US_SSN
from .data_types.countries.PL.pesel import PL_PESEL
from .data_types.keys.github_personal_access_token import GitHub_PersonalAccessToken
from .data_types.keys.aws_s3_secure_access_key import AWS_S3_secret_access_key
from .data_types.keys.btc_address import BTC_address
from .data_types.keys.eth_address import ETH_address
from .data_types.keys.google_api_key import Google_API_Key

class SensitiveInfoGenerator:

    def __init__(self):

        self.rs = RandomSentence()
        self.data_types = {
            'IPv4_Address':IPv4_Address(),
            'IPv6_Address':IPv6_Address(),
            'Email':Email(),
            'US_SSN':US_SSN(),
            'PL_PESEL':PL_PESEL(),
            'GitHub_PersonalAccessToken': GitHub_PersonalAccessToken(),
            'AWS_S3_Secret_Access_Key': AWS_S3_secret_access_key(),
            'BTC_address': BTC_address(),
            'ETH_address': ETH_address(),
            'Google_API_Key': Google_API_Key()
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

            # Generate
            valid_instance = self.data_types[data_type].generate_valid()
            
            return self.insert_sensitive_info_into_sentence(valid_instance)

    def generate_invalid(self, data_type):
        "Generates invalid instance of data_type"
        # Check that data_type is correct
        if isinstance(data_type, str) and data_type in [k for k in self.data_types]:
            
            # Generate
            invalid_instance = self.data_types[data_type].generate_invalid()
            
            return self.insert_sensitive_info_into_sentence(invalid_instance)

    def get_prompt_to_serve_miners(self):

        dtype = random.choice([k for k in self.data_types])
        valid_or_invalid = random.choice(['valid','invalid'])

        if valid_or_invalid == 'valid':
            return self.generate_valid(dtype), dtype, 1
        
        else:   
            return self.generate_invalid(dtype), dtype, 0
