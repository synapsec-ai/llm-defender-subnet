import requests
from llm_defender.base.utils import validate_prompt

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

    prompt_api_url = "https://ny1nnvnwnh.execute-api.eu-west-1.amazonaws.com/Prod/prompt"

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

    except requests.exceptions.JSONDecodeError as e:
        print(f"Unable to read the response from the API: {e}")
    except requests.exceptions.ConnectionError as e:
        print(f"Unable to connect to the prompt API: {e}")

def get_api_data(hotkey = "5CUd7qjrr7jtHxG7y6a7MDSbQpz6bgw2rDL5fWs2Cp97T5y2", 
                 signature = "78e28cc13f4627cb0784c29cdfa3bae4950a3c1748bfa0d76bf39a9ad43eee74888e5896b81f079d3050c9f3dbe22bcd37be912db63f9c8c683d159126377584",
                 synapse_uuid = "e6f30fd4-faef-4c5d-a621-0abb063715ad"):
    
    api_data = get_api_prompt(hotkey=hotkey, signature=signature, synapse_uuid=synapse_uuid)
    print(api_data)
    valid_prompt = validate_prompt(api_data)
    print(valid_prompt)

def main():
    get_api_data()

if __name__ == '__main__':
    main()