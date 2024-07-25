"""
This module implements a health check API for the LLM Defender Subnet
neurons. The purpose of the health check API is to provide key
information about the health of the neuron to enable easier
troubleshooting. 

It is highly recommended to connect the health check API into the
monitoring tools used to monitor the server. The health metrics are not
persistent and will be lost if neuron is restarted.

Endpoints:
    /healthcheck
        Returns boolean depicting the health of the neuron based on the
        health metrics
    /healthcheck/metrics
        Returns a dictionary of the metrics the health is derived from
    /healthcheck/events
        Returns list of relevant events related to the health metrics
        (error and warning)

The health check API can be disabled by adding --disable_healthcheck to
the neuron run command. 

Port and host can be controlled with --healthcheck_port and
--healthcheck_host parameters.
"""

from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict
import datetime
import uvicorn
import threading


class HealthCheckResponse(BaseModel):
    status: bool
    checks: Dict
    timestamp: str


class HealthCheckDataResponse(BaseModel):
    data: Dict
    timestamp: str


class HealthCheckAPI:
    def __init__(self, host: str, port: int):

        # Variables
        self.host = host
        self.port = port

        # Status variables
        self.health_metrics = {
            "start_time": datetime.datetime.now().timestamp(),
            "neuron_running": False,
            "iterations": 0,
            "prompts.total_count": 0,
            "prompts.generated_per_second":0.0,
            "prompts.sensitive_information.count": 0,
            "prompts.sensitive_information.total_generated": 0,
            "prompts.sensitive_information.total_fallback": 0,
            "prompts.prompt_injection.count": 0,
            "prompts.prompt_injection.total_generated": 0,
            "prompts.prompt_injection.total_fallback": 0,
            "log_entries.success": 0,
            "log_entries.warning": 0,
            "log_entries.error": 0,
            "axons.total_filtered_axons": 0,
            "axons.total_queried_axons": 0,
            "axons.queries_per_second":0.0,
            "responses.total_valid_responses": 0,
            "responses.total_invalid_responses": 0,
            "responses.valid_responses_per_second":0.0,
            "responses.invalid_responses_per_second":0.0,
            "weights.targets": 0,
            "weights.last_set_timestamp": None,
            "weights.total_count":0,
        }
        self.healthy = True
        self.health_events = {
            "warning": [],
            "error": [],
            "success": []
        }

        # App
        self.app = FastAPI()
        self._setup_routes()

    def _setup_routes(self):
        self.app.add_api_route(
            "/healthcheck", self._healthcheck, response_model=HealthCheckResponse
        )
        self.app.add_api_route(
            "/healthcheck/metrics",
            self._healthcheck_metrics,
            response_model=HealthCheckDataResponse,
        )
        self.app.add_api_route(
            "/healthcheck/events",
            self._healthcheck_events,
            response_model=HealthCheckDataResponse,
        )

    def _healthcheck(self):
        try:
            # Update health status when the /healthcheck API is invoked
            self.healthy, checks = self.get_health()

            # Return status
            return {"status": self.healthy, "checks": checks, "timestamp": str(datetime.datetime.now())}
        except Exception:
            return {"status": False, "timestamp": str(datetime.datetime.now())}

    def _healthcheck_metrics(self):
        try:
            # Return the metrics collected by the HealthCheckAPI
            return {
                "data": self.health_metrics,
                "timestamp": str(datetime.datetime.now()),
            }
        except Exception:
            return {"status": False, "timestamp": str(datetime.datetime.now())}

    def _healthcheck_events(self):
        try:
            # Return the events collected by the HealthCheckAPI
            return {
                "data": self.health_events,
                "timestamp": str(datetime.datetime.now()),
            }
        except Exception:
            return {"status": False, "timestamp": str(datetime.datetime.now())}

    def get_health(self) -> tuple[bool,dict]:
        """This method is responsible for updating the health status based on the metrics"""
        
        # By default everything is healthy
        health_checks = {
            "is_neuron_running": True,
            "is_llm_used": True,
        }
        health_status = True

        # Is Neuron running?
        if self.health_metrics["neuron_running"] is not True:
            health_checks["is_neuron_running"] = False
            health_status = False
        
        # Does the validator use LLM to generate prompts?
        fallback_prompts = self.health_metrics["prompts.prompt_injection.total_fallback"] + self.health_metrics["prompts.sensitive_information.total_fallback"]
        generated_prompts = self.health_metrics["prompts.prompt_injection.total_generated"] + self.health_metrics["prompts.sensitive_information.total_generated"]

        # If the validator doesnt generate prompts, set health status to false
        if generated_prompts == 0:
            health_checks["is_llm_used"] = False
            health_status = False
        
        # If more than 20% of the prompts issued by the validator are from dataset, set health status to false
        elif (fallback_prompts > 0) and (fallback_prompts/(fallback_prompts + generated_prompts) > 0.50):
            health_checks["is_llm_used"] = False
            health_status = False

        # If all checks passed we can conclude the neuron is healthy
        return health_status, health_checks

    def run(self):
        """This method runs the HealthCheckAPI"""
        threading.Thread(
            target=uvicorn.run,
            args=(self.app,),
            kwargs={"host": self.host, "port": self.port},
            daemon=True,
        ).start()

    def add_event(self, event_name: str, event_data: str) -> bool:
        """This method adds an event to self.health_events dictionary"""
        if isinstance(event_name, str) and event_name.upper() in (
            "SUCCESS",
            "ERROR",
            "WARNING",
        ):

            # Append the received event under the correct key if it is str
            if isinstance(event_data, str) and not isinstance(event_data, bool):
                event_severity = event_name.lower()
                self.health_events[event_severity].append(
                    {"timestamp": str(datetime.datetime.now()), "message": event_data}
                )

                # Reduce the number of events if more than 250
                if len(self.health_events[event_severity]) > 250:
                    self.health_events[event_severity] = self.health_events[
                        event_severity
                    ][-250:]

                return True

        return True

    def append_metric(self, metric_name: str, value: int | bool) -> bool:
        """This method increases the metric counter by the value defined
        in the counter. If the counter is bool, sets the metric value to
        the provided value. This function must be executed whenever the
        counters for the given metrics wants to be updated"""

        if metric_name in self.health_metrics.keys() and value > 0:
            if isinstance(value, bool):
                self.health_metrics[metric_name] = value
            else:
                self.health_metrics[metric_name] += value
        else:
            return False

        return True

    def update_rates(self):

        current_time = datetime.datetime.now().timestamp()
        start_time = self.health_metrics['start_time']
        time_passed = current_time - start_time

        # Calculate prompts per second 
        self.health_metrics['prompts.generated_per_second'] = self.health_metrics['prompts.total_count'] / time_passed

        # Calculate queries per second 
        self.health_metrics['axons.queries_per_second'] = self.health_metrics['axons.total_queried_axons'] / time_passed

        # Calculate valid responses per second 
        self.health_metrics['responses.valid_responses_per_second'] = self.health_metrics['responses.total_valid_responses'] / time_passed

        # Calculate invalid responses per second 
        self.health_metrics['responses.invalid_responses_per_second'] = self.health_metrics['responses.total_invalid_responses'] / time_passed