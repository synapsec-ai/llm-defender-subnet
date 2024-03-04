from llm_defender.base.mock_data import (
    get_prompt
)
from uuid import uuid4
import bittensor as bt
import time

def test_get_prompt(hotkey, synapse_uuid):
    keep_loop_going = True
    while keep_loop_going:
        prompt = get_prompt(hotkey = hotkey, synapse_uuid = synapse_uuid)
        print(prompt)
        if prompt == None:
            keep_loop_going = False
        time.sleep(10)

def get_params(wallet):
    hotkey = wallet.hotkey.ss58_address
    synapse_uuid = str(uuid4())
    return hotkey, synapse_uuid

def generate_wallet(ck = "burner_test_ck", hk = "burner_test_hk"):
    wallet = bt.wallet(name=ck, hotkey=hk)
    wallet.create_if_non_existent()
    return wallet

def main():
    hk, suid = get_params(generate_wallet())
    test_get_prompt(hotkey = hk, synapse_uuid = suid)

if __name__ == '__main__':
    main()