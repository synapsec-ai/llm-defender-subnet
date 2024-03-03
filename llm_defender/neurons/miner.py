"""
This miner script executes the main loop for the miner and keeps the
miner active in the bittensor network.
"""

import time
from argparse import ArgumentParser
import traceback
import bittensor as bt
import torch
import time

from llm_defender.core.miners.miner import LLMDefenderMiner
from llm_defender import __version__ as version


def main(miner: LLMDefenderMiner):
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
        f"Axon {miner.forward} served on network: {miner.neuron_config.subtensor.chain_endpoint} with netuid: {miner.neuron_config.netuid}"
    )
    # Activate the Miner on the network
    axon.start()
    bt.logging.info(f"Axon started on port: {miner.neuron_config.axon.port}")

    # Step 7: Keep the miner alive
    # This loop maintains the miner's operations until intentionally stopped.
    bt.logging.info(
        "Miner has been initialized and we are connected to the network. Start main loop."
    )

    # When we init, set last_updated_block to current_block
    miner.last_updated_block = miner.subtensor.block
    while True:
        try:
            # Below: Periodically update our knowledge of the network graph.
            if miner.step % 20 == 0:
                # Periodically update the weights on the Bittensor blockchain.
                current_block = miner.subtensor.block
                if (
                    current_block - miner.last_updated_block > 100
                    and miner.miner_set_weights == True
                ):
                    weights = torch.Tensor([0.0] * len(miner.metagraph.uids))
                    weights[miner.miner_uid] = 1.0

                    bt.logging.warning(
                        "DEPRECATION NOTICE: Miners do not need to set weights in this subnet. The capability to do so will be removed in a future release"
                    )
                    bt.logging.debug(
                        f"Setting weights with the following parameters: netuid={miner.neuron_config.netuid}, wallet={miner.wallet}, uids={miner.metagraph.uids}, weights={weights}, version_key={miner.subnet_version}"
                    )

                    result = miner.subtensor.set_weights(
                        netuid=miner.neuron_config.netuid,  # Subnet to set weights on.
                        wallet=miner.wallet,  # Wallet to sign set weights using hotkey.
                        uids=miner.metagraph.uids,  # Uids of the miners to set weights for.
                        weights=weights,  # Weights to set for the miners.
                        wait_for_inclusion=False,
                        version_key=miner.subnet_version,
                    )

                    if result:
                        bt.logging.success("Successfully set weights.")
                    else:
                        bt.logging.error("Failed to set weights.")

                    miner.last_updated_block = miner.subtensor.block

                if miner.step % 300 == 0:
                    # Check if the miners hotkey is on the remote blacklist
                    miner.check_remote_blacklist()

                if miner.step % 600 == 0:
                    bt.logging.debug(
                        f"Syncing metagraph: {miner.metagraph} with subtensor: {miner.subtensor}"
                    )

                    miner.metagraph.sync(subtensor=miner.subtensor)

                miner.metagraph = miner.subtensor.metagraph(miner.neuron_config.netuid)
                log = (
                    f"Version:{version} | "
                    f"Blacklist:{miner.hotkey_blacklisted} | "
                    f"Step:{miner.step} | "
                    f"Block:{miner.metagraph.block.item()} | "
                    f"Stake:{miner.metagraph.S[miner.miner_uid]} | "
                    f"Rank:{miner.metagraph.R[miner.miner_uid]} | "
                    f"Trust:{miner.metagraph.T[miner.miner_uid]} | "
                    f"Consensus:{miner.metagraph.C[miner.miner_uid] } | "
                    f"Incentive:{miner.metagraph.I[miner.miner_uid]} | "
                    f"Emission:{miner.metagraph.E[miner.miner_uid]}"
                )

                bt.logging.info(log)

                if miner.wandb_enabled:
                    wandb_logs = [
                        {
                            f"{miner.miner_uid}:{miner.wallet.hotkey.ss58_address}_rank": miner.metagraph.R[
                                miner.miner_uid
                            ].item()
                        },
                        {
                            f"{miner.miner_uid}:{miner.wallet.hotkey.ss58_address}_trust": miner.metagraph.T[
                                miner.miner_uid
                            ].item()
                        },
                        {
                            f"{miner.miner_uid}:{miner.wallet.hotkey.ss58_address}_consensus": miner.metagraph.C[
                                miner.miner_uid
                            ].item()
                        },
                        {
                            f"{miner.miner_uid}:{miner.wallet.hotkey.ss58_address}_incentive": miner.metagraph.I[
                                miner.miner_uid
                            ].item()
                        },
                        {
                            f"{miner.miner_uid}:{miner.wallet.hotkey.ss58_address}_emission": miner.metagraph.E[
                                miner.miner_uid
                            ].item()
                        },
                    ]
                    miner.wandb_handler.set_timestamp()
                    for wandb_log in wandb_logs:
                        miner.wandb_handler.log(data=wandb_log)
                    bt.logging.trace(f"Wandb logs added: {wandb_logs}")

            miner.step += 1
            time.sleep(1)

        # If someone intentionally stops the miner, it'll safely terminate operations.
        except KeyboardInterrupt:
            axon.stop()
            bt.logging.success("Miner killed by keyboard interrupt.")
            miner.wandb_handler.wandb_run.finish()
            break
        # In case of unforeseen errors, the miner will log the error and continue operations.
        except Exception:
            bt.logging.error(traceback.format_exc())
            continue


# This is the main function, which runs the miner.
if __name__ == "__main__":
    # Parse command line arguments
    parser = ArgumentParser()
    parser.add_argument("--netuid", type=int, default=14, help="The chain subnet uid")
    parser.add_argument(
        "--logging.logging_dir",
        type=str,
        default="/var/log/bittensor",
        help="Provide the log directory",
    )

    parser.add_argument(
        "--miner_set_weights",
        type=str,
        default="False",
        help="Determines if miner should set weights or not",
    )

    parser.add_argument(
        "--validator_min_stake",
        type=float,
        default=20000.0,
        help="Determine the minimum stake the validator should have to accept requests",
    )

    # Create a miner based on the Class definitions
    subnet_miner = LLMDefenderMiner(parser=parser)

    main(subnet_miner)
