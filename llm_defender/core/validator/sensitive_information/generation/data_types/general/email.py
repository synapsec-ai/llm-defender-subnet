import random
import re
import string
from english_words import get_english_words_set
import time

class Email:

    def __init__(self):
        all_english_words = get_english_words_set(['web2'], lower=True)
        self.english_set = []
        for word in all_english_words:
            if len(word) > 10:
                self.english_set.append(word)

        self.predefined_domain_and_tlds = ['gmail.com', 'yahoo.com', 'proton.me', 'hotmail.com', 'hotmail.co.uk', 'aol.com', 'hotmail.fr', 'yahoo.fr', 'wanadoo.fr', 'orange.fr', 'yahoo.co.uk', 'yahoo.com.br', 'yahoo.co.in', 'outlook.com']
        
        self.predefined_tlds = ['.com', '.com', '.com', '.com', '.com', '.com', '.com', '.com', '.com', '.com', '.com', '.com', '.co', '.org', '.net', '.io', '.co.uk', '.fr', '.gov', '.tv', '.ai', '.travel', '.tel', '.pro', '.mil', '.int', '.info', '.edu', '.cat', '.biz', '.aero', '.me', '.gg']
        
        self.random_chars = ['!', '#', '$', '%', '^', '&', '*', '(', ')', '-', '_', '+', '=', '~', "'", '"', '<', '>', '?', '[', ']', '{', '}']
        
        self.email_pattern = re.compile(
            r'([!#-\'+/-9=?A-Z^-~-]+(\.[!#-\'+/-9=?A-Z^-~-]+)*|'
            r'"([]!#-[^-~ \t]|(\\[\t -~]))+")'
            r'@'
            r'([!#-\'+/-9=?A-Z^-~-]+(\.[!#-\'+/-9=?A-Z^-~-]+)*|\[[\t -Z^-~]*\])'
        )
    
    def generate_username(self): 
        # random set of strings 
        random_int = random.randint(1,3)
        if random_int == 1:
            username = ''.join(random.choices((string.ascii_letters + string.digits), k=random.randint(4, 16)))
        # one word 
        elif random_int == 2:
            username = random.choice(self.english_set) + random.choice(['',str(random.randint(1,999))])
        # two words
        else:
            first_word = random.choice(self.english_set)
            second_word = random.choice(self.english_set)
            username = first_word + random.choice(['','','','','','.','_',str(random.randint(1,99))]) + second_word + random.choice(['','','','',str(random.randint(1,999))])
        # truncate if necessary
        if len(username) > 64:
            return username[0:63]
        else:
            return username.replace('..','.').replace('--','-').replace('__','_')

    def generate_domain_and_tld(self):
        # predefined domain 
        if random.choice([True, False]):
            return random.choice(self.predefined_domain_and_tlds) 
        # construct domain       
        else:
            # use english words 
            if random.choice([True, False]):
                domain = random.choice(self.english_set)
            # randomly generated str
            else:
                domain = ''.join(random.choices((string.ascii_letters + string.digits), k=random.randint(3, 30)))

            domain_and_tld = domain + random.choice(self.predefined_tlds)

            if len(domain_and_tld) > 255:
                return domain_and_tld[-254:]
            else:
                return domain_and_tld

    def generate_valid(self):
        username = self.generate_username() 
        # remove periods and underscores at the beginning or end of the username
        if username[0] in ['.','_']:
            username = username[1:]
        if username[-1] in ['.','_']:
            username = username[:-1]
        domain_and_tld = self.generate_domain_and_tld()
        return f"{username}@{domain_and_tld}".replace('..','.').replace('--','-').replace('__','_').replace('.@','@').replace('_@','@').replace('@.','@').replace('@_','@')

    def generate_invalid(self):
        email = self.generate_valid()
        random_int = random.randint(1,3)
        # remove @
        if random_int == 1:
            return email.replace('@', '')
        # double the @
        elif random_int == 2:
            return email.replace('@','@@')

        # replace @ with another character
        else:
            return email.replace('@',random.choice(self.random_chars))     

    def verify(self, email):
        return self.email_pattern.match(email) is not None
    