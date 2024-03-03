"""
Validator docstring here
"""
import time
import traceback
import sys
import secrets
from argparse import ArgumentParser
from uuid import uuid4
import torch
import bittensor as bt
from llm_defender.base import utils
from llm_defender.base.protocol import LLMDefenderProtocol
from llm_defender.core.validators.validator import PromptInjectionValidator
from llm_defender import __version__ as version

def main(validator: PromptInjectionValidator):
    """
    This function executes the main function for the validator.
    """
    
    # Step 7: The Main Validation Loop
    bt.logging.info(f"Starting validator loop with version: {version}")
    while True:
        try:
            # Periodically sync subtensor status and save the state file
            if validator.step % 5 == 0:
                # Sync metagraph
                try:
                    validator.metagraph = validator.sync_metagraph(
                        validator.metagraph, validator.subtensor
                    )
                    bt.logging.debug(f'Metagraph synced: {validator.metagraph}')
                except TimeoutError as e:
                    bt.logging.error(f"Metagraph sync timed out: {e}")

                # Update local knowledge of the hotkeys
                validator.check_hotkeys()

                # Save state
                validator.save_state()

                # Save miners state
                validator.save_miner_state()

            if validator.step % 20 == 0:
                # Truncate local miner response state file
                validator.truncate_miner_state()

                # Update local knowledge of blacklisted miner hotkeys
                validator.check_blacklisted_miner_hotkeys()

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

            # Get the query to send to the valid Axons
            synapse_uuid = str(uuid4())
            query = validator.serve_prompt(synapse_uuid)

            # Get list of UIDs to query
            (
                uids_to_query,
                list_of_uids,
                blacklisted_uids,
                uids_not_to_query,
            ) = validator.get_uids_to_query(all_axons=all_axons)
            if not uids_to_query:
                bt.logging.warning(f"UIDs to query is empty: {uids_to_query}")

            bt.logging.debug(f"Serving query: {query}")

            # Broadcast query to valid Axons
            nonce = secrets.token_hex(24)
            timestamp = str(int(time.time()))
            data_to_sign = f'{synapse_uuid}{nonce}{timestamp}'
            
            responses = validator.dendrite.query(
                uids_to_query,
                LLMDefenderProtocol(
                    prompt=query["prompt"],
                    analyzer=query["analyzer"],
                    subnet_version=validator.subnet_version,
                    synapse_uuid=synapse_uuid,
                    synapse_signature=utils.sign_data(wallet=validator.wallet, data=data_to_sign),
                    synapse_nonce=nonce,
                    synapse_timestamp=timestamp
                ),
                timeout=validator.timeout,
                deserialize=True,
            )

            # Process blacklisted UIDs (set scores to 0)
            # for uid in blacklisted_uids:
            #     bt.logging.debug(f'Setting score for blacklisted UID: {uid}. Old score: {validator.scores[uid]}')
            #     validator.scores[uid] = (
            #         validator.neuron_config.alpha * validator.scores[uid]
            #         + (1 - validator.neuron_config.alpha) * 0.0
            #     )
            #     bt.logging.debug(f'Set score for blacklisted UID: {uid}. New score: {validator.scores[uid]}')

            # Process UIDs we did not query (set scores to 0)
            for uid in uids_not_to_query:
                bt.logging.trace(
                    f"Setting score for not queried UID: {uid}. Old score: {validator.scores[uid]}"
                )
                validator.scores[uid] = (
                    validator.neuron_config.alpha * validator.scores[uid]
                    + (1 - validator.neuron_config.alpha) * 0.0
                )
                bt.logging.trace(
                    f"Set score for not queried UID: {uid}. New score: {validator.scores[uid]}"
                )

            # Log the results for monitoring purposes.
            if all(item.output is None for item in responses):
                bt.logging.info("Received empty response from all miners")
                bt.logging.debug(f"Sleeping for: {bt.__blocktime__} seconds")
                time.sleep(bt.__blocktime__)
                # If we receive empty responses from all axons, we can just set the scores to none for all the uids we queried
                for uid in list_of_uids:
                    bt.logging.trace(
                        f"Setting score for empty response from UID: {uid}. Old score: {validator.scores[uid]}"
                    )
                    validator.scores[uid] = (
                        validator.neuron_config.alpha * validator.scores[uid]
                        + (1 - validator.neuron_config.alpha) * 0.0
                    )
                    bt.logging.trace(
                        f"Set score for empty response from UID: {uid}. New score: {validator.scores[uid]}"
                    )
                continue

            bt.logging.trace(f"Received responses: {responses}")

            # Process the responses
            # processed_uids = torch.nonzero(list_of_uids).squeeze()
            response_data = validator.process_responses(
                query=query,
                processed_uids=list_of_uids,
                responses=responses,
                synapse_uuid=synapse_uuid,
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

            current_block = validator.subtensor.block
            bt.logging.debug(
                f"Current step: {validator.step}. Current block: {current_block}. Last updated block: {validator.last_updated_block}"
            )

            if current_block - validator.last_updated_block > 100:
                # Periodically update the weights on the Bittensor blockchain.
                try:
                    validator.set_weights()
                    # Update validators knowledge of the last updated block
                    validator.last_updated_block = validator.subtensor.block
                except TimeoutError as e:
                    bt.logging.error(f"Setting weights timed out: {e}")

            # End the current step and prepare for the next iteration.
            validator.step += 1

            # Sleep for a duration equivalent to the block time (i.e., time between successive blocks).
            bt.logging.debug(f"Sleeping for: {bt.__blocktime__} seconds")
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
        type=str,
        default="True",
        help="WARNING: Setting this value to False clears the old state.",
    )

    parser.add_argument(
        "--max_targets",
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
