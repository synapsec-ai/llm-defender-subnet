import requests	
from llm_defender.base.utils import validate_prompt, sign_data
from uuid import uuid4
import bittensor as bt
import pytest 
import unittest

def get_api_prompt(hotkey, signature, synapse_uuid) -> dict:	

    """Retrieves a promopt from the prompt API"""

    request_data = {
    "version": "2.0",
    "routeKey": "$default",
    "rawPath": "/prompt-api",
    "headers": {
                "X-Hotkey": hotkey,
                "X-Signature": signature,
                "X-Synapseid": synapse_uuid
            },
    "body": {"Some Message": "Hello from Lambda!"}
    }

    prompt_api_url = "https://czio6d2xbh.execute-api.eu-west-1.amazonaws.com/prompt-api"

    try:
        # get prompt
        res = requests.get(url=prompt_api_url, params=request_data, timeout=6)
        # check for correct status code
        if res.status_code == 200:
            # get prompt entry from the API output 
            prompt_entry = res.json()
            # check to make sure prompt is valid 
            print(
                f"Loaded remote prompt to serve to miners: {prompt_entry}"
            )
            return prompt_entry

        else:
            print(
                f"Miner blacklist API returned unexpected status code: {res.status_code}"
            )
    except requests.exceptions.ReadTimeout as e:
        print(f"Request timed out: {e}")
    except requests.exceptions.JSONDecodeError as e:
        print(f"Unable to read the response from the prompt API: {e}")
    except requests.exceptions.ConnectionError as e:
        print(f"Unable to connect to the prompt API: {e}")
    except Exception as e:
        print(f'Generic error during request: {e}')

def get_api_params(wallet):
    hotkey = wallet.hotkey.ss58_address
    synapse_uuid = str(uuid4())
    signature = sign_data(wallet = wallet, data = synapse_uuid)
    return hotkey, signature, synapse_uuid

def generate_wallet(ck = "burner_test_ck", hk = "burner_test_hk"):
    wallet = bt.wallet(name=ck, hotkey=hk)
    wallet.create_if_non_existent()
    return wallet

def test_failed_api_call():
    # Test that API does not return a query for an invalid wallet
    hotkey, signature, synapse_uuid = get_api_params(generate_wallet())
    prompt = get_api_prompt(hotkey, signature, synapse_uuid)
    assert prompt == None



def main():	
    test_failed_api_call()

if __name__ == '__main__':	
    main()