import argparse
import os
from typing import List

from fastapi import FastAPI, Response
import uvicorn
import bittensor as bt
from pydantic import BaseModel

import llm_defender.subnet_api as LLMDefenderSubnetAPI


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
        default=os.getenv(
            "SUBTENSOR_CHAIN_ENDPOINT", "wss://entrypoint-finney.opentensor.ai"
        ),
    )
    parser.add_argument(
        "--wallet.name", type=str, default=os.getenv("WALLET_NAME", "validator")
    )
    parser.add_argument(
        "--wallet.path", type=str, default="/tmp/.bittensor/wallets"
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

@app.post("/")
async def default(response: Response, item: SingularItem):
    """This method analyzes a single string with the prompt injection
    analyzer"""

    res = handler.process_singular_prompt(item.prompt, analyzer="Prompt Injection")

    if res:
        response.status_code = 200
        bt.logging.trace(f"Processed prompt with response: {res}")
        return res

    # If we cant get the result, return HTTP/500
    bt.logging.trace(f"Failed to process request: {item}")
    response.status_code = 500
    return {"message": "Internal Server Error"}

@app.post("/prompt_injection")
async def analyze_prompt_injection(response: Response, item: SingularItem):
    """This method analyzes a single string with the prompt injection
    analyzer"""

    res = handler.process_singular_prompt(item.prompt, analyzer="Prompt Injection")

    if res:
        response.status_code = 200
        bt.logging.trace(f"Processed prompt with response: {res}")
        return res

    # If we cant get the result, return HTTP/500
    bt.logging.trace(f"Failed to process request: {item}")
    response.status_code = 500
    return {"message": "Internal Server Error"}


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

    res = handler.process_singular_prompt(item.prompt, analyzer="Sensitive Information")

    if res:
        response.status_code = 200
        bt.logging.trace(f"Processed prompt with response: {res}")
        return res

    # If we cant get the result, return HTTP/500
    bt.logging.trace(f"Failed to process request: {item}")
    response.status_code = 500
    return {"message": "Internal Server Error"}


@app.post("/sensitive_information/bulk")
async def analyze_sensitive_information_bulk(response: Response, item: BulkItem):
    """This method analyzes multiple strings with the prompt injection
    analyzer"""

    # Bulk analyzer has not been implemented yet but make the API endpoints available for development
    response.status_code = 501
    return {"message": "Not Implemented"}


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=os.getenv("UVICORN_HOST", "0.0.0.0"),
        port=os.getenv("UVICORN_PORT", "8080"),
        log_level=os.getenv("UVICORN_LOG_LEVEL", "info"),
    )
