"""
Validator docstring here
"""
import time
import traceback
import sys
from argparse import ArgumentParser
import torch
import bittensor as bt
from prompt_defender.prompt_injection.protocol import PromptInjectionProtocol
from prompt_defender.prompt_injection.neurons import PromptInjectionValidator


def main(validator: PromptInjectionValidator):
    """
    This function executes the main function for the validator.
    """

    # Step 7: The Main Validation Loop
    bt.logging.info("Starting validator loop")

    step = 0
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

            # Filter out validators from the queryable Axons
            validator_uids = validator.metagraph.total_stake == 0.0
            bt.logging.trace(f"Validators UIDs to filter: {validator_uids}")

            # Filter out axons with an IP address of 0.0.0.0
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
            bt.logging.trace(f"Invalid UIDs to filter: {invalid_uids}")

            # Define which UIDs to filter out from the valid list of Axons
            uids_to_filter = torch.where(
                validator_uids == False, validator_uids, invalid_uids
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
                PromptInjectionProtocol(prompt=query["prompt"], engine=query["engine"], roles=["internal"]),
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
            # Periodically update the weights on the Bittensor blockchain.
            if (step + 1) % 10 == 0:
                # TODO(developer): Define how the validator normalizes scores before setting weights.
                weights = torch.nn.functional.normalize(validator.scores, p=1.0, dim=0)
                bt.logging.info(f"Setting weights: {weights}")
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
    parser.add_argument("--netuid", type=int, default=1, help="The chain subnet uid.")
    parser.add_argument(
        "--logging.logging_dir",
        type=str,
        default="/var/log/bittensor",
        help="Provide the log directory",
    )

    # Create a validator based on the Class definitions
    subnet_validator = PromptInjectionValidator(parser=parser)

    main(subnet_validator)
