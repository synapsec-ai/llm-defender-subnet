"""
Validator docstring here
"""
import time
import traceback
import sys
from argparse import ArgumentParser
import torch
import bittensor as bt
from llm_defender.base.protocol import LLMDefenderProtocol
from llm_defender.core.validators.validator import PromptInjectionValidator


def main(validator: PromptInjectionValidator):
    """
    This function executes the main function for the validator.
    """

    # Step 7: The Main Validation Loop
    bt.logging.info("Starting validator loop")

    step = 0
    last_updated_block = 0
    while True:
        try:
            # Periodically sync subtensor state
            if step % 5 == 0:
                bt.logging.debug(
                    f"Syncing metagraph: {validator.metagraph} with subtensor: {validator.subtensor}"
                )
                validator.metagraph.sync(subtensor=validator.subtensor)

            # Get all axons
            all_axons = validator.metagraph.axons
            bt.logging.trace(f"All axons: {all_axons}")

            # If there are more axons than scores, append the scores list
            if len(validator.metagraph.uids.tolist()) > len(validator.scores):
                bt.logging.info(
                    f"Discovered new Axons, current scores: {validator.scores}"
                )
                validator.scores = torch.cat(
                    (
                        validator.scores,
                        torch.zeros(
                            (
                                len(validator.metagraph.uids.tolist())
                                - len(validator.scores)
                            ),
                            dtype=torch.float32,
                        ),
                    )
                )
                bt.logging.info(f"Updated scores, new scores: {validator.scores}")

            # Filter uids to send the request to
            uids_with_stake = validator.metagraph.total_stake >= 0.0
            bt.logging.debug(f"UIDs to filter: {uids_with_stake}")

            # Filter out uids with an IP address of 0.0.0.0
            invalid_uids = torch.tensor(
                [
                    bool(value)
                    for value in [
                        ip != "0.0.0.0"
                        for ip in [
                            validator.metagraph.neurons[uid].axon_info.ip
                            for uid in validator.metagraph.uids.tolist()
                        ]
                    ]
                ],
                dtype=torch.bool,
            )
            bt.logging.debug(f"Invalid UIDs to filter: {invalid_uids}")

            # Define which UIDs to filter out from the valid list of uids
            uids_to_filter = torch.where(
                uids_with_stake == False, uids_with_stake, invalid_uids
            )

            bt.logging.debug(f"UIDs to select for the query: {uids_to_filter}")

            # Define UIDs to query
            uids_to_query = [
                axon
                for axon, keep_flag in zip(all_axons, uids_to_filter)
                if keep_flag.item()
            ]
            bt.logging.info(f"UIDs to query: {uids_to_query}")

            # Get the query to send to the valid Axons
            query = validator.serve_prompt().get_dict()

            # Broadcast query to valid Axons
            responses = validator.dendrite.query(
                uids_to_query,
                LLMDefenderProtocol(
                    prompt=query["prompt"],
                    engine=query["engine"],
                    roles=["internal"],
                    analyzer=["Prompt Injection"],
                ),
                timeout=validator.timeout,
                deserialize=True,
            )

            # Log the results for monitoring purposes.
            if all(item.output is None for item in responses):
                bt.logging.info("Received empty response from all miners")
                time.sleep(bt.__blocktime__)
                # If we receive empty responses from all axons we do not need to proceed further, as there is nothing to do
                continue

            bt.logging.info(f"Received responses: {responses}")

            # Process the responses
            validator.process_responses(query=query, responses=responses)


            # Print stats
            bt.logging.debug(f'Scores: {validator.scores}')
            bt.logging.debug(f'All UIDs: {validator.metagraph.uids}')
            bt.logging.debug(f'Processed UIDs: kukkuu')
            
            bt.logging.debug(f"Current step: {step}")
            # Periodically update the weights on the Bittensor blockchain.
            current_block = validator.subtensor.block
            if current_block - last_updated_block > 100:
                bt.logging.debug(f'We are currently in block {validator.subtensor.block} and last updated block was {last_updated_block}')
                weights = torch.nn.functional.normalize(validator.scores, p=1.0, dim=0)
                bt.logging.info(f"Setting weights: {weights}")

                bt.logging.debug(
                    f"Setting weights with the following parameters: netuid={validator.neuron_config.netuid}, wallet={validator.wallet}, uids={validator.metagraph.uids}, weights={weights}"
                )
                # This is a crucial step that updates the incentive mechanism on the Bittensor blockchain.
                # Miners with higher scores (or weights) receive a larger share of TAO rewards on this subnet.
                result = validator.subtensor.set_weights(
                    netuid=validator.neuron_config.netuid,  # Subnet to set weights on.
                    wallet=validator.wallet,  # Wallet to sign set weights using hotkey.
                    uids=validator.metagraph.uids,  # Uids of the miners to set weights for.
                    weights=weights,  # Weights to set for the miners.
                    wait_for_inclusion=True,
                )
                if result:
                    bt.logging.success("Successfully set weights.")
                else:
                    bt.logging.error("Failed to set weights.")
                
                last_updated_block = current_block

            # End the current step and prepare for the next iteration.
            step += 1
            # Resync our local state with the latest state from the blockchain.
            validator.metagraph = validator.subtensor.metagraph(
                validator.neuron_config.netuid
            )
            # Sleep for a duration equivalent to the block time (i.e., time between successive blocks).
            time.sleep(bt.__blocktime__)

        # If we encounter an unexpected error, log it for debugging.
        except RuntimeError as e:
            bt.logging.error(e)
            traceback.print_exc()

        # If the user interrupts the program, gracefully exit.
        except KeyboardInterrupt:
            bt.logging.success("Keyboard interrupt detected. Exiting validator.")
            sys.exit()

        except Exception as e:
            bt.logging.error(e)
            traceback.print_exc()


# The main function parses the configuration and runs the validator.
if __name__ == "__main__":
    # Parse command line arguments
    parser = ArgumentParser()
    parser.add_argument(
        "--alpha",
        default=0.9,
        type=float,
        help="The weight moving average scoring.",
    )
    parser.add_argument("--netuid", type=int, default=14, help="The chain subnet uid.")
    parser.add_argument(
        "--logging.logging_dir",
        type=str,
        default="/var/log/bittensor",
        help="Provide the log directory",
    )

    # Create a validator based on the Class definitions and initialize it
    subnet_validator = PromptInjectionValidator(parser=parser)
    if (
        not subnet_validator.apply_config(
            bt_classes=[bt.subtensor, bt.logging, bt.wallet]
        )
        or not subnet_validator.initialize_neuron()
    ):
        bt.logging.error("Unable to initialize Validator. Exiting.")
        sys.exit()

    main(subnet_validator)
