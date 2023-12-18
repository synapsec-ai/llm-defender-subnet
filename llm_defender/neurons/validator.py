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
from uuid import uuid4


def main(validator: PromptInjectionValidator):
    """
    This function executes the main function for the validator.
    """

    # Step 7: The Main Validation Loop
    bt.logging.info("Starting validator loop")

    while True:
        try:
            # Periodically sync subtensor status and save the state file
            if validator.step % 5 == 0:
                bt.logging.debug(
                    f"Syncing metagraph: {validator.metagraph} with subtensor: {validator.subtensor}"
                )
                validator.metagraph.sync(subtensor=validator.subtensor)

                # Update local knowledge of the hotkeys
                validator.check_hotkeys()

                # Save state
                validator.save_state()

                # Save miners state
                validator.save_miner_state()

            if validator.step % 20 == 0:
                validator.truncate_miner_state()

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
            bt.logging.trace(f"UIDs to filter: {uids_with_stake}")

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
            bt.logging.trace(f"Invalid UIDs to filter: {invalid_uids}")

            # Define which UIDs to filter out from the valid list of uids
            uids_to_filter = torch.where(
                uids_with_stake == False, uids_with_stake, invalid_uids
            )

            bt.logging.trace(f"UIDs to select for the query: {uids_to_filter}")

            # Define UIDs to query
            uids_to_query = [
                axon
                for axon, keep_flag in zip(all_axons, uids_to_filter)
                if keep_flag.item()
            ]

            # Reduce the number of simultaneous UIDs to query
            if validator.max_targets < 256:
                start_idx = validator.max_targets * validator.target_group
                end_idx = min(len(uids_to_query), validator.max_targets * (validator.target_group + 1))
                if start_idx >= len(uids_to_query):
                    raise IndexError("Starting index for querying the miners is out-of-bounds")
                
                if end_idx >= len(uids_to_query):
                    end_idx = len(uids_to_query)
                    validator.target_group = 0
                else:
                    validator.target_group += 1
                
                bt.logging.debug(f"List indices for UIDs to query starting from: '{start_idx}' ending with: '{end_idx}'")
                uids_to_query = uids_to_query[start_idx:end_idx] 

            list_of_uids = [
                validator.metagraph.hotkeys.index(axon.hotkey) for axon in uids_to_query
            ]
            list_of_hotkeys = [axon.hotkey for axon in uids_to_query]

            bt.logging.info(f"Sending query to the following UIDs: {list_of_uids}")
            bt.logging.trace(
                f"Sending query to the following hotkeys: {list_of_hotkeys}"
            )

            # Get the query to send to the valid Axons
            query = validator.serve_prompt().get_dict()

            # Broadcast query to valid Axons
            # synapse_uuid = str(uuid4())
            responses = validator.dendrite.query(
                uids_to_query,
                LLMDefenderProtocol(
                    prompt=query["prompt"],
                    engine=query["engine"],
                    roles=["internal"],
                    analyzer=["Prompt Injection"],
                    subnet_version=validator.subnet_version,
                    # synapse_uuid=synapse_uuid
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

            bt.logging.trace(f"Received responses: {responses}")

            # Process the responses
            # processed_uids = torch.nonzero(list_of_uids).squeeze()
            response_data = validator.process_responses(
                query=query, processed_uids=list_of_uids, responses=responses, 
                # synapse_uuid=synapse_uuid
            )

            for res in response_data:
                if validator.miner_responses:
                    if res["hotkey"] in validator.miner_responses:
                        validator.miner_responses[res["hotkey"]].append(res)
                    else:
                        validator.miner_responses[res["hotkey"]] = [res]
                else:
                    validator.miner_responses = {}
                    validator.miner_responses[res["hotkey"]] = [res]

            # Print stats
            bt.logging.debug(f"Scores: {validator.scores}")
            bt.logging.debug(f"Processed UIDs: {list(list_of_uids)}")

            # Periodically update the weights on the Bittensor blockchain.
            current_block = validator.subtensor.block
            bt.logging.debug(
                f"Current step: {validator.step}. Current block: {current_block}. Last updated block: {validator.last_updated_block}"
            )
            if current_block - validator.last_updated_block > 100:
                
                # Set weights for the miners
                try:
                    validator.set_weights()
                except TimeoutError as e:
                    bt.logging.error(f'Setting weights timed out: {e}')

            # End the current step and prepare for the next iteration.
            validator.step += 1
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
        "--load_state",
        type=bool,
        default=True,
        help="WARNING: Setting this value to False clears the old state.",
    )

    parser.add_argument(
        "--max-targets",
        type=int,
        default=64,
        help="Sets the value for the number of targets to query at once",
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
