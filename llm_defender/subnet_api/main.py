import argparse
from fastapi import FastAPI, Response
from typing import List
import os
import llm_defender.subnet_api as LLMDefenderSubnetAPI
import asyncio
import uvicorn
import bittensor as bt

from pydantic import BaseModel

class SingularItem(BaseModel):
    prompt: str

class BulkItem(BaseModel):
    prompt: List[str]

def get_parser():
    """This method setups the arguments for the argparse object"""
    parser = argparse.ArgumentParser()

    parser.add_argument("--netuid", type=str, default=os.getenv("NETUID", "14"))
    parser.add_argument(
        "--subtensor.network",
        type=str,
        default=os.getenv("SUBTENSOR_NETWORK", "finney"),
    )
    parser.add_argument(
        "--subtensor.chain_endpoint",
        type=str,
        default=os.getenv("SUBTENSOR_CHAIN_ENDPOINT", "wss://entrypoint-finney.opentensor.ai"),
    )
    parser.add_argument(
        "--api_data_dir", type=str, default=os.getenv("API_DATA_DIR", "/tmp")
    )
    parser.add_argument(
        "--wallet.name", type=str, default=os.getenv("WALLET_NAME", "validator")
    )
    parser.add_argument(
        "--wallet.hotkey", type=str, default=os.getenv("WALLET_HOTKEY", "default")
    )

    parser.add_argument(
        "--api_log_level", type=str, default=os.getenv("API_LOG_LEVEL", "TRACE")
    )
    
    return parser


parser = get_parser()

app = FastAPI()
handler = LLMDefenderSubnetAPI.Handler(parser=parser)

@app.post("/prompt_injection")
async def analyze_prompt_injection(response: Response, item: SingularItem):
    """This method analyzes a single string with the prompt injection
    analyzer"""

    analyzer = "Prompt Injection"

    # Determine if we want to query only the top axons
    if os.getenv("TOP_AXONS_ONLY") == "TRUE":
        top_axons_only = True
    else:
        top_axons_only = False

    # Get UIDs to query and send out the request
    uids_to_query = handler.get_uids_to_query(top_axons_only=top_axons_only, query_count=int(os.getenv("AXONS_TO_QUERY", "12")))
    responses = asyncio.run(handler.query_miners(uids_to_query=uids_to_query, prompt=item.prompt, analyzer=analyzer))
    bt.logging.trace(f'Processing prompt: {item.prompt}')
    
    # Determine response
    res = handler.determine_singular_response(responses, item.prompt, analyzer)
    response.status_code = 200
    bt.logging.trace(f'Processed prompt with response: {res}')
    
    return res

@app.post("/prompt_injection/bulk")
async def analyze_prompt_injection_bulk(response: Response, item: BulkItem):
    """This method analyzes multiple strings with the prompt injection
    analyzer"""

    # Bulk analyzer has not been implemented yet but make the API endpoints available for development
    response.status_code = 501
    return {"message": "Not Implemented"}


@app.post("/sensitive_information")
async def analyze_sensitive_information(response: Response, item: SingularItem):
    """This method analyzes a single string with the sensitive
    information analyzer"""

    analyzer = "Sensitive Information"

    # Get UIDs to query and send out the request
    uids_to_query = handler.get_uids_to_query(query_count=12)
    responses = asyncio.run(handler.query_miners(uids_to_query=uids_to_query, prompt=item.prompt, analyzer=analyzer))
    bt.logging.trace(f'Processing prompt: {item.prompt}')
    
    # Determine response
    res = handler.determine_singular_response(responses, item.prompt, analyzer)
    response.status_code = 200
    bt.logging.trace(f'Processed prompt with response: {res}')
    
    return res


@app.post("/sensitive_information/bulk")
async def analyze_sensitive_information_bulk(response: Response, item: BulkItem):
    """This method analyzes multiple strings with the prompt injection
    analyzer"""

    # Bulk analyzer has not been implemented yet but make the API endpoints available for development
    response.status_code = 501
    return {"message": "Not Implemented"}

if __name__ == "__main__":
    uvicorn.run("main:app", host=os.getenv("UVICORN_HOST", "0.0.0.0"), port=os.getenv("UVICORN_PORT", "8080"), log_level=os.getenv("UVICORN_LOG_LEVEL", "info"))
