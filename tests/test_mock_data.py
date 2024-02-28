from llm_defender.base.mock_data import (
    get_prompt
)
import time 

def test_get_prompt():
    keep_loop_going = True
    while keep_loop_going:
        prompt = get_prompt()
        print(prompt)
        if prompt == None:
            keep_loop_going = False

def main():
    test_get_prompt()

if __name__ == '__main__':
    main()