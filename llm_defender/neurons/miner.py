"""
asdf
"""
import time
from argparse import ArgumentParser
import traceback
import bittensor as bt

from llm_defender.core.miners.miner import PromptInjectionMiner


def main(miner: PromptInjectionMiner):
    """
    This function executes the main miner loop. The miner is configured
    upon the initialization of the miner. If you want to change the
    miner configuration, please adjust the initialization parameters.
    """

    # Link the miner to the Axon
    axon = bt.axon(wallet=miner.wallet, config=miner.neuron_config)
    bt.logging.info(f"Linked miner to Axon: {axon}")

    # Attach the miner functions to the Axon
    axon.attach(
        forward_fn=miner.forward,
        blacklist_fn=miner.blacklist,
        priority_fn=miner.priority,
    )
    bt.logging.info(f"Attached functions to Axon: {axon}")

    # Pass the Axon information to the network
    axon.serve(netuid=miner.neuron_config.netuid, subtensor=miner.subtensor)

    bt.logging.info(
        f"Axon {miner.forward} served on network: \
        {miner.neuron_config.subtensor.chain_endpoint} with netuid: {miner.neuron_config.netuid}"
    )
    # Activate the Miner on the network
    axon.start()
    bt.logging.info(f"Axon started on port: {miner.neuron_config.axon.port}")

    # Step 7: Keep the miner alive
    # This loop maintains the miner's operations until intentionally stopped.
    bt.logging.info(
        "Miner has been initialized and we are connected to the network. Start main loop."
    )

    step = 0
    while True:
        try:
            # TODO(developer): Define any additional operations to be performed by the miner.
            # Below: Periodically update our knowledge of the network graph.
            if step % 5 == 0:
                metagraph = miner.subtensor.metagraph(miner.neuron_config.netuid)
                log = (
                    f"Step:{step} | "
                    f"Block:{metagraph.block.item()} | "
                    f"Stake:{metagraph.S[miner.miner_uid]} | "
                    f"Rank:{metagraph.R[miner.miner_uid]} | "
                    f"Trust:{metagraph.T[miner.miner_uid]} | "
                    f"Consensus:{metagraph.C[miner.miner_uid] } | "
                    f"Incentive:{metagraph.I[miner.miner_uid]} | "
                    f"Emission:{metagraph.E[miner.miner_uid]}"
                )
                bt.logging.info(log)
            step += 1
            time.sleep(1)

        # If someone intentionally stops the miner, it'll safely terminate operations.
        except KeyboardInterrupt:
            axon.stop()
            bt.logging.success("Miner killed by keyboard interrupt.")
            break
        # In case of unforeseen errors, the miner will log the error and continue operations.
        except Exception:
            bt.logging.error(traceback.format_exc())
            continue


# This is the main function, which runs the miner.
if __name__ == "__main__":
    # Parse command line arguments
    parser = ArgumentParser()
    parser.add_argument("--netuid", type=int, default=1, help="The chain subnet uid")
    parser.add_argument(
        "--logging.logging_dir",
        type=str,
        default="/var/log/bittensor",
        help="Provide the log directory",
    )

    # Create a miner based on the Class definitions
    subnet_miner = PromptInjectionMiner(
        parser=parser
    )

    main(subnet_miner)
