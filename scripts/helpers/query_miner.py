"""This helper script can be used to query miners from a validator. It
can be used for troubleshooting purposes."""

import argparse
import bittensor as bt
import uuid
import llm_defender as LLMDefender
import secrets
import hashlib
import time
import asyncio


def send_notification_synapse(
    synapse_uuid, wallet, dendrite, axons_with_valid_ip, prompt_to_analyze
):
    encoded_prompt = prompt_to_analyze.get("prompt").encode("utf-8")
    prompt_hash = hashlib.sha256(encoded_prompt).hexdigest()
    nonce = secrets.token_hex(24)
    timestamp = str(int(time.time()))
    data_to_sign = f"{synapse_uuid}{nonce}{wallet.hotkey.ss58_address}{timestamp}"
    bt.logging.trace(
        f"Sent notification synapse to: {axons_with_valid_ip} with encoded prompt: {encoded_prompt} for prompt: {prompt_to_analyze}."
    )
    responses = dendrite.query(
        axons_with_valid_ip,
        LLMDefender.SubnetProtocol(
            subnet_version=LLMDefender.config["module_version"],
            synapse_uuid=synapse_uuid,
            synapse_signature=LLMDefender.sign_data(
                hotkey=wallet.hotkey, data=data_to_sign
            ),
            synapse_nonce=nonce,
            synapse_timestamp=timestamp,
            synapse_hash=prompt_hash,
        ),
        timeout=6.0,
        deserialize=True,
    )
    return responses


async def send_payload_message(
    synapse_uuid, uids_to_query, wallet, dendrite, prompt_to_analyze
):
    # Broadcast query to valid Axons
    nonce = secrets.token_hex(24)
    timestamp = str(int(time.time()))
    data_to_sign = f"{synapse_uuid}{nonce}{wallet.hotkey.ss58_address}{timestamp}"
    bt.logging.trace(
        f"Sent payload synapse to: {uids_to_query} with prompt: {prompt_to_analyze}."
    )
    responses = await dendrite.forward(
        uids_to_query,
        LLMDefender.SubnetProtocol(
            analyzer=prompt_to_analyze["analyzer"],
            subnet_version=LLMDefender.config["module_version"],
            synapse_uuid=synapse_uuid,
            synapse_signature=LLMDefender.sign_data(
                hotkey=wallet.hotkey, data=data_to_sign
            ),
            synapse_nonce=nonce,
            synapse_timestamp=timestamp,
            synapse_prompt=prompt_to_analyze["prompt"],
        ),
        timeout=12.0,
        deserialize=True,
    )
    return responses


async def main(args, parser):
    config = bt.config(parser)
    bt.logging(trace=True)
    wallet = bt.wallet(config=config)
    dendrite = bt.dendrite(wallet=wallet)
    metagraph = bt.metagraph(netuid=args.netuid, network=args.network)

    axon_to_query = metagraph.axons[args.uid]
    bt.logging.info(f"Axon to query: {axon_to_query}")
    synapse_uuid = str(uuid.uuid4())
    prompt_to_analyze = {"prompt": args.prompt, "analyzer": "Prompt Injection"}

    send_notification_synapse(
        synapse_uuid=synapse_uuid,
        dendrite=dendrite,
        wallet=wallet,
        axons_with_valid_ip=axon_to_query,
        prompt_to_analyze=prompt_to_analyze,
    )

    responses = await send_payload_message(
        synapse_uuid=synapse_uuid,
        uids_to_query=axon_to_query,
        dendrite=dendrite,
        wallet=wallet,
        prompt_to_analyze=prompt_to_analyze,
    )

    for response in responses:
        bt.logging.info(response)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("--netuid", type=int, default=14)
    parser.add_argument("--network", type=str, default="finney")
    parser.add_argument("--uid", type=int)

    parser.add_argument("--wallet.name", type=str, default="validator")
    parser.add_argument("--wallet.hotkey", type=str, default="default")

    parser.add_argument("--prompt", type=str, default="What is the meaning of life?")

    args = parser.parse_args()

    asyncio.run(main(args, parser))
