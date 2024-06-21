import llm_defender.core.validator as LLMDefenderCore
import bittensor as bt
import uuid
import numpy as np
import os
import asyncio
import time


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

        self.wallet, self.subtensor, self.dendrite, self.metagraph = (
            self.validator.setup_bittensor_objects(self.neuron_config)
        )

        # Store metagraph last-update timestamp
        self.metagraph_updated = time.time()

    def _check_metagraph_update(self):

        # Update metagraph if updated more than 10 minutes ago
        if self.metagraph_updated < (time.time()):
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
        return loop.run_in_executor(None, self.metagraph.sync)

    def get_uids_to_query(
        self, query_count: int = 12, top_axons_only: bool = False
    ) -> list:

        # Check if metagraph needs to be updated
        self._check_metagraph_update()
    
        # All Axons
        raw_axons = self.metagraph.axons
        
        axons_to_query = []

        # Get the best axons available
        sorted_incentives = np.argsort(self.metagraph.I)
        for _, sorted_incentive in enumerate(sorted_incentives):

            # If we have enough axons to query we can end the iteration
            if len(axons_to_query) >= query_count:
                break
            bt.logging.trace(
                f"Adding the following axon based on incentive rank: {raw_axons[sorted_incentive]}"
            )
            axons_to_query.append(raw_axons[sorted_incentive])

        # Additionally get one axon per coldkey
        if not top_axons_only:
            coldkeys = set()
            for _, raw_axon in enumerate(raw_axons):
                if raw_axon.coldkey not in coldkeys:
                    bt.logging.trace(
                        f"Adding the following axon based on coldkey: {raw_axon}"
                    )
                    axons_to_query.append(raw_axon)

        valid_axons = self.validator.determine_valid_axons(axons=axons_to_query)

        return valid_axons

    async def query_miners(
        self, uids_to_query: list, prompt: str, analyzer: str
    ) -> list:

        prompt_to_analyze = {"prompt": prompt, "analyzer": analyzer}
        synapse_uuid = str(uuid.uuid4())
        
        bt.logging.info("Querying miners")
        responses = await self.validator.send_payload_message(
            synapse_uuid=synapse_uuid,
            uids_to_query=uids_to_query,
            prompt_to_analyze=prompt_to_analyze,
            timeout=2
        )

        return responses

    def process_singular_prompt(self, prompt: str, analyzer: str) -> dict:

        try:
            # Determine if we want to query only the top axons
            if os.getenv("TOP_AXONS_ONLY", "FALSE") == "TRUE":
                top_axons_only = True
            else:
                top_axons_only = False

            bt.logging.info(f'OS TOP_AXONS_ONLY: {os.environ["TOP_AXONS_ONLY"]}')
            bt.logging.info(f'OS AXONS_TO_QUERY: {os.environ["AXONS_TO_QUERY"]}')
            # Get UIDs to query and send out the request
            uids_to_query = self.get_uids_to_query(
                top_axons_only=top_axons_only,
                query_count=int(os.getenv("AXONS_TO_QUERY", "12")),
            )
            responses = asyncio.run(
                self.query_miners(
                    uids_to_query=uids_to_query, prompt=prompt, analyzer=analyzer
                )
            )
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

            print(outputs)

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
