"""This helper script can be used to query miners from a validator. It
can be used for troubleshooting purposes."""
import argparse
import bittensor as bt
from llm_defender.base.protocol import LLMDefenderProtocol
import uuid
from llm_defender.base import utils
from llm_defender import __spec_version__ as subnet_version


def main(args, parser):
    config = bt.config(parser)
    bt.logging(trace=True)
    wallet = bt.wallet(config=config)
    dendrite = bt.dendrite(wallet=wallet)
    metagraph = bt.metagraph(netuid=args.netuid, network=args.network)

    axon_to_query = metagraph.axons[args.uid]
    bt.logging.info(f"Axon to query: {axon_to_query}")
    synapse_uuid = str(uuid.uuid4())

    responses = dendrite.query(
        axon_to_query,
        LLMDefenderProtocol(
            prompt=args.prompt,
            analyzer="Prompt Injection",
            subnet_version=subnet_version,
            synapse_uuid=synapse_uuid,
            synapse_signature=utils.sign_data(wallet=wallet, data=synapse_uuid),
        ),
        timeout=12,
        deserialize=True,
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

    main(args, parser)
