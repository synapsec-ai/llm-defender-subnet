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
import bittensor as bt


class HealthCheckResponse(BaseModel):
    status: bool
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
            "start_time": str(datetime.datetime.now()),
            "neuron_running": False,
            "iterations": 0,
            "prompts.total_count": 0,
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
            "responses.total_valid_responses": 0,
            "responses.total_invalid_responses": 0,
            "weights.targets": 0,
            "weights.last_set_timestamp": None
        }
        self.healthy = True
        self.health_events = {
            "warning": [],
            "error": [],
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
            self.healthy = self._get_health()

            # Return status
            return {"status": self.healthy, "timestamp": str(datetime.datetime.now())}
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
            return {"data": self.health_events, "timestamp": str(datetime.datetime.now())}
        except Exception:
            return {"status": False, "timestamp": str(datetime.datetime.now())}
        
    def _get_health(self):
        """This method is responsible for updating the health status based on the metrics"""

        # Is Neuron running?
        if self.health_metrics["neuron_running"] is not True:
            return False

        # If all checks passed we can conclude the neuron is healthy
        return True

    def run(self):
        """This method runs the HealthCheckAPI"""
        threading.Thread(target=uvicorn.run, args=(self.app,), kwargs={"host": self.host, "port": self.port}, daemon=True).start()

    def add_event(self, event_name: str, event_data: str):
        """This method adds an event to self.health_events dictionary"""
        if event_name == "warning" and isinstance(event_data, str):
            self.health_events["warning"].append(event_data)
        elif event_name == "error" and isinstance(event_data, str):
            self.health_events["error"].append(event_data)
        else:
            return False

        return True

    def append_metric(self, metric_name: str, value: int | bool):
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
