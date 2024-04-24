"""
Validator docstring here
"""
import asyncio
import os
import secrets
import sys
import time
import traceback
from argparse import ArgumentParser
from uuid import uuid4

import bittensor as bt
import torch

from llm_defender import __version__ as version
from llm_defender.base import utils
from llm_defender.base.protocol import LLMDefenderProtocol
from llm_defender.core.validators.validator import LLMDefenderValidator


def update_metagraph(validator: LLMDefenderValidator) -> None:
    try:
        validator.metagraph = validator.sync_metagraph(validator.metagraph, validator.subtensor)
        bt.logging.debug(f'Metagraph synced: {validator.metagraph}')
    except TimeoutError as e:
        bt.logging.error(f"Metagraph sync timed out: {e}")


async def update_metagraph_async(validator: LLMDefenderValidator) -> None:
    await asyncio.to_thread(update_metagraph, validator)


def update_and_check_hotkeys(validator: LLMDefenderValidator) -> None:
    validator.check_hotkeys()
    if validator.wallet.hotkey.ss58_address not in validator.metagraph.hotkeys:
        bt.logging.error(f"Hotkey is not registered on metagraph: {validator.wallet.hotkey.ss58_address}.")


async def update_and_check_hotkeys_async(validator: LLMDefenderValidator) -> None:
    await asyncio.to_thread(update_and_check_hotkeys, validator)


def save_validator_state(validator: LLMDefenderValidator) -> None:
    # This could be async, as the underlying implementation writes to a file
    validator.save_state()


async def save_validator_state_async(validator: LLMDefenderValidator) -> None:
    await asyncio.to_thread(save_validator_state, validator)


def save_miner_state(validator: LLMDefenderValidator):
    # This could be async, as the underlying implementation writes to a file
    validator.save_miner_state()


async def save_miner_state_async(validator: LLMDefenderValidator):
    await asyncio.to_thread(save_miner_state, validator)


def truncate_miner_state(validator: LLMDefenderValidator):
    # This could be async, as it changes the miner_responses variable which will not be used immediately
    validator.truncate_miner_state()


async def truncate_miner_state_async(validator: LLMDefenderValidator):
    await asyncio.to_thread(truncate_miner_state, validator)


def save_used_nonces(validator: LLMDefenderValidator):
    # This could be async, as the underlying implementation writes to a file
    validator.save_used_nonces()


async def save_used_nonces_async(validator: LLMDefenderValidator):
    await asyncio.to_thread(save_used_nonces, validator)


def validate_query(list_of_all_hotkeys, synapse_uuid, validator):
    # This could be async, serve_prompt method calls an endpoint
    # Get the query to send to the valid Axons)
    if validator.query is None:
        validator.query = validator.serve_prompt(synapse_uuid=synapse_uuid, miner_hotkeys=list_of_all_hotkeys)
    bt.logging.debug(f"Serving query: {validator.query}")


async def validate_query_async(list_of_all_hotkeys, synapse_uuid, validator):
    await asyncio.to_thread(validate_query, list_of_all_hotkeys, synapse_uuid, validator)


def query_axons(synapse_uuid, uids_to_query, validator):
    #
    # Broadcast query to valid Axons
    nonce = secrets.token_hex(24)
    timestamp = str(int(time.time()))
    data_to_sign = f'{synapse_uuid}{nonce}{validator.wallet.hotkey.ss58_address}{timestamp}'
    # query['analyzer'] = "Sensitive Information"
    responses = validator.dendrite.query(
        uids_to_query,
        LLMDefenderProtocol(
            analyzer=validator.query['analyzer'],
            subnet_version=validator.subnet_version,
            synapse_uuid=synapse_uuid,
            synapse_signature=utils.sign_data(hotkey=validator.wallet.hotkey, data=data_to_sign),
            synapse_nonce=nonce,
            synapse_timestamp=timestamp
        ),
        timeout=validator.timeout,
        deserialize=True,
    )
    return responses


async def query_axons_async(synapse_uuid, uids_to_query, validator):
    # Broadcast query to valid Axons
    nonce = secrets.token_hex(24)
    timestamp = str(int(time.time()))
    data_to_sign = f'{synapse_uuid}{nonce}{validator.wallet.hotkey.ss58_address}{timestamp}'
    # query['analyzer'] = "Sensitive Information"
    responses = await validator.dendrite.forward(
        uids_to_query,
        LLMDefenderProtocol(
            analyzer=validator.query['analyzer'],
            subnet_version=validator.subnet_version,
            synapse_uuid=synapse_uuid,
            synapse_signature=utils.sign_data(hotkey=validator.wallet.hotkey, data=data_to_sign),
            synapse_nonce=nonce,
            synapse_timestamp=timestamp
        ),
        timeout=validator.timeout,
        deserialize=True,
    )
    return responses



def score_unused_axons(validator, uids_not_to_query):
    # This could be async
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


async def score_unused_axons_async(validator, uids_not_to_query):
    await asyncio.to_thread(score_unused_axons, validator, uids_not_to_query)


def handle_empty_responses(validator, list_of_uids):
    # This must be SYNC process, because we need to wait until the subnetwork syncs
    # Handle all responses empty
    bt.logging.info("Received empty response from all miners")
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
    bt.logging.debug(f"Sleeping for: {1.5 * bt.__blocktime__} seconds")
    time.sleep(1.5 * bt.__blocktime__)


def format_responses(validator, list_of_uids, responses, synapse_uuid):
    # Process the responses
    # processed_uids = torch.nonzero(list_of_uids).squeeze()
    response_data = validator.process_responses(
        query=validator.query,
        processed_uids=list_of_uids,
        responses=responses,
        synapse_uuid=synapse_uuid,
    )
    return response_data


def handle_invalid_prompt(validator):
    # This must be SYNC process
    # If we cannot get a valid prompt, sleep for a moment and retry the loop
    bt.logging.warning(
        f'Unable to get a valid query from the Prompt API, received: {validator.query}. Please report this to subnet developers if the issue persists.')

    # Sleep and retry
    bt.logging.debug(f"Sleeping for: {1.5 * bt.__blocktime__} seconds")
    time.sleep(1.5 * bt.__blocktime__)


def attach_response_to_validator(validator, response_data):
    for res in response_data:
        if validator.miner_responses:
            if res["hotkey"] in validator.miner_responses:
                validator.miner_responses[res["hotkey"]].append(res)
            else:
                validator.miner_responses[res["hotkey"]] = [res]
        else:
            validator.miner_responses = {}
            validator.miner_responses[res["hotkey"]] = [res]


def update_weights(validator):
    # This could be async
    # Periodically update the weights on the Bittensor blockchain.
    try:
        validator.set_weights()
        # Update validators knowledge of the last updated block
        validator.last_updated_block = validator.subtensor.block
    except TimeoutError as e:
        bt.logging.error(f"Setting weights timed out: {e}")


async def update_weights_async(validator):
    await asyncio.to_thread(update_weights, validator)


async def main(validator: LLMDefenderValidator):
    """
    This function executes the main function for the validator.
    """

    # Step 7: The Main Validation Loop
    bt.logging.info(f"Starting validator loop with version: {version}")

    while True:
        try:
            # Periodically sync subtensor status and save the state file
            if validator.step % 5 == 0:
                await update_metagraph_async(validator)
                await update_and_check_hotkeys_async(validator)
                await asyncio.gather(
                    save_validator_state_async(validator),
                    save_miner_state_async(validator)
                )
            if validator.step % 20 == 0:
                await asyncio.gather(
                    truncate_miner_state_async(validator),
                    save_used_nonces_async(validator),
                    validator.check_blacklisted_miner_hotkeys()
                )

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

            # Get list of UIDs to query
            (
                uids_to_query,
                list_of_uids,
                blacklisted_uids,
                uids_not_to_query,
                list_of_all_hotkeys
            ) = await validator.get_uids_to_query_async(all_axons=all_axons)
            if not uids_to_query:
                bt.logging.warning(f"UIDs to query is empty: {uids_to_query}")

            synapse_uuid = str(uuid4())
            await validate_query_async(list_of_all_hotkeys, synapse_uuid, validator)

            is_prompt_invalid = (
                validator.query is None
                or "analyzer" not in validator.query.keys()
                or "label" not in validator.query.keys()
                or "weight" not in validator.query.keys()
            )
            if is_prompt_invalid:
                handle_invalid_prompt(validator)
                continue

            await score_unused_axons_async(validator, uids_not_to_query)
            responses = await query_axons_async(synapse_uuid, uids_to_query, validator)
            are_responses_empty = all(item.output is None for item in responses)

            if are_responses_empty:
                handle_empty_responses(validator, list_of_uids)
                continue

            bt.logging.trace(f"Received responses: {responses}")

            response_data = format_responses(validator, list_of_uids, responses, synapse_uuid)
            attach_response_to_validator(validator, response_data)

            # Print stats
            bt.logging.debug(f"Scores: {validator.scores}")
            bt.logging.debug(f"Processed UIDs: {list(list_of_uids)}")

            current_block = validator.subtensor.block
            bt.logging.debug(
                f"Current step: {validator.step}. Current block: {current_block}. Last updated block: {validator.last_updated_block}"
            )

            if current_block - validator.last_updated_block > 100:
                await update_weights_async(validator)

            # End the current step and prepare for the next iteration.
            validator.step += 1

            # Sleep for a duration equivalent to the block time (i.e., time between successive blocks).
            bt.logging.debug(f"Sleeping for: {1.5 * bt.__blocktime__} seconds")
            time.sleep(1.5 * bt.__blocktime__)

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

    parser.add_argument(
        "--disable_remote_logging",
        action='store_true',
        help="This flag must be set if you want to disable remote logging",
    )

    # Disable TOKENIZERS_PARALLELISM
    os.environ["TOKENIZERS_PARALLELISM"] = "false"

    # Create a validator based on the Class definitions and initialize it
    subnet_validator = LLMDefenderValidator(parser=parser)
    if (
        not subnet_validator.apply_config(
            bt_classes=[bt.subtensor, bt.logging, bt.wallet]
        )
        or not subnet_validator.initialize_neuron()
    ):
        bt.logging.error("Unable to initialize Validator. Exiting.")
        sys.exit()

    asyncio.run(main(subnet_validator))
