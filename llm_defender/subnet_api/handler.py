import llm_defender.core.validator as LLMDefenderCore
import bittensor as bt
import uuid
import numpy as np
import os
import asyncio
import time
import logging

class SuppressPydanticFrozenFieldFilter(logging.Filter):
    def filter(self, record):
        return 'Ignoring error when setting attribute: 1 validation error for SubnetProtocol' not in record.getMessage()

class Handler:
    """This class implements the handler for the llm-defender-subnet
    API used to interact with the miners in the subnet"""

    def __init__(self, parser):

        self.args = parser.parse_args()
        # Setup logging
        if self.args.api_log_level == "DEBUG":
            bt.logging.enable_debug()
        elif self.args.api_log_level == "TRACE":
            bt.logging.enable_trace()
        else:
            bt.logging.enable_default()

        # Generate a SubnetValidator class
        self.validator = LLMDefenderCore.SubnetValidator(parser=parser)

        # Configure and initialize the SubnetValidator class
        self.neuron_config = self.validator.config(
            bt_classes=[bt.subtensor, bt.logging, bt.wallet]
        )
        bt.logging._logger.addFilter(SuppressPydanticFrozenFieldFilter())

        self.wallet, self.subtensor, self.dendrite, self.metagraph = (
            self.validator.setup_bittensor_objects(self.neuron_config)
        )

        # Store metagraph last-update timestamp
        self.metagraph_updated = time.time()

    def _check_metagraph_update(self):

        # Update metagraph if updated more than 10 minutes ago
        if (time.time() - self.metagraph_updated) > 600:
            bt.logging.info(
                f"Updating metagraph. Current block: {self.metagraph.block}"
            )

            # Use asyncio and create fire-and-forget sync task
            background_tasks = set()
            task = asyncio.create_task(self._refresh_metagraph())

            # Add task to the set. This creates a strong reference.
            background_tasks.add(task)

            # To prevent keeping references to finished tasks forever,
            # make each task remove its own reference from the set after
            # completion:
            task.add_done_callback(background_tasks.discard)

    async def _refresh_metagraph(self):
        loop = asyncio.get_event_loop()
        
        # Store metagraph last-update timestamp
        self.metagraph_updated = time.time()

        return loop.run_in_executor(None, self.metagraph.sync)

    def get_uids_to_query(
        self, query_count: int = 12, top_axons_only: bool = False
    ) -> list:

        # Check if metagraph needs to be updated
        self._check_metagraph_update()
        
        # All Axons
        raw_axons = self.metagraph.axons
        bt.logging.trace(f'Raw axons to filter from: {raw_axons}')

        # Remove invalid axons
        valid_axons = self.validator.determine_valid_axons(axons=raw_axons)
        bt.logging.trace(f'Valid axons selected for query: {valid_axons}')

        axons_to_query = []
        
        # Get the best axons available
        sorted_incentives = np.argsort(self.metagraph.I)[::-1]
        for _, sorted_incentive in enumerate(sorted_incentives):

            # If we have enough axons to query we can end the iteration
            if len(axons_to_query) >= query_count:
                break
            bt.logging.trace(
                f"Adding the following axon based on incentive rank: {valid_axons[sorted_incentive]}"
            )
            axons_to_query.append(valid_axons[sorted_incentive])
        
        # Additionally get one axon per coldkey
        if not top_axons_only:
            coldkeys = set()
            for _, raw_axon in enumerate(valid_axons):
                if raw_axon.coldkey not in coldkeys:
                    bt.logging.trace(
                        f"Adding the following axon based on coldkey: {raw_axon}"
                    )
                    axons_to_query.append(raw_axon)
            bt.logging.trace(f'Axons to query based on incentive rank and coldkeys: {axons_to_query}')
            bt.logging.trace(f'Coldkeys included in the query: {coldkeys}')
        else:
            bt.logging.trace(f'Axons to query based on incentive rank: {axons_to_query}')

        return valid_axons

    
    async def query_miners(
        self, uids_to_query: list, prompt: str, analyzer: str
    ) -> list:
        
        # Helper for collecting the responses
        async def collect_response(uid):
            response = await self.validator.send_payload_message(
                synapse_uuid=synapse_uuid,
                uids_to_query=uid,
                prompt_to_analyze=prompt_to_analyze,
                timeout=6
            )
            return response
        
        prompt_to_analyze = {"prompt": prompt, "analyzer": analyzer}
        synapse_uuid = str(uuid.uuid4())
        miners_to_query =  int(os.getenv("AXONS_TO_QUERY", "12"))

        bt.logging.info(f"Querying {miners_to_query} miners using the following analyzer: {analyzer}")
        
        # Collect responses until enough responses have been received
        min_response_count = miners_to_query/2
        
        tasks = [collect_response(uid) for uid in uids_to_query]

        responses = []
        for future in asyncio.as_completed(tasks):
            response = await future

            # Only take response with an output into account
            if response.output is not None:
                responses.append(response)
            if len(responses) >= min_response_count:
                break
        
        bt.logging.info(f'Received {len(responses)} replies from the miners')

        return responses

    def process_singular_prompt(self, prompt: str, analyzer: str) -> dict:

        try:
            # Determine if we want to query only the top axons
            if os.getenv("TOP_AXONS_ONLY", "FALSE") == "TRUE":
                top_axons_only = True
            else:
                top_axons_only = False

            # Get UIDs to query and send out the request
            uids_to_query = self.get_uids_to_query(
                top_axons_only=top_axons_only,
                query_count=int(os.getenv("AXONS_TO_QUERY", "12")),
            )

            bt.logging.trace(f'Sending query to uids: {uids_to_query}')

            responses = asyncio.run(
                self.query_miners(
                    uids_to_query=uids_to_query, prompt=prompt, analyzer=analyzer
                )
            )
            bt.logging.trace(f'Received responses: {responses}')
            bt.logging.trace(f"Processing prompt: {prompt}")

            # Determine response
            res = self.determine_singular_response(responses, prompt, analyzer)

            return res
        except Exception as e:
            bt.logging.error(f"Error occurred while processing singular request: {e}")
            return {}

    def determine_singular_response(self, responses, prompt, analyzer):
        try:
            outputs = [response.output for response in responses if response.output]

            # If zero responses contained an output the response cant be determined
            if len(outputs) < 1:
                bt.logging.warning(
                    f"Received less than 1 responses with an output: {responses}"
                )
                return {
                    "prompt": prompt,
                    "num_responses": 0,
                    "average_confidence": 0,
                    "max_confidence": 0,
                    "min_confidence": 0,
                    "verdict": "UNKNOWN",
                }

            confidences = [output["confidence"] for output in outputs]
            if sum(confidences) / len(confidences) > 0.90:
                verdict = "MALICIOUS"
            else:
                verdict = "SAFE"

            res = {
                "prompt": prompt,
                "num_responses": len(confidences),
                "average_confidence": sum(confidences) / len(confidences),
                "max_confidence": max(confidences),
                "min_confidence": min(confidences),
                "verdict": verdict,
            }

            if analyzer == "Sensitive Information":
                sensitive_information = {}
                for output in outputs:
                    for token_data in output["engines"][0]["data"]["token_data"]:
                        if (
                            token_data["entity_group"]
                            not in sensitive_information.keys()
                        ):
                            sensitive_information[token_data["entity_group"]] = set(
                                {token_data["word"].strip()}
                            )
                        else:
                            sensitive_information[token_data["entity_group"]].add(
                                token_data["word"].strip()
                            )

                res["sensitive_information"] = sensitive_information
            bt.logging.trace(f"Returning response: {res}")

            return res

        except Exception as e:
            bt.logging.error(f"Failure processing outputs: {e}")

            return {
                "prompt": prompt,
                "num_responses": 0,
                "average_confidence": 0,
                "max_confidence": 0,
                "min_confidence": 0,
                "verdict": "UNKNOWN",
            }
