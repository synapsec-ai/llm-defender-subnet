#!/bin/bash

# Get the update interval from the environment variable, defaulting to 60 seconds
update_interval="${UPDATE_INTERVAL}"

while true; do
    git pull --all
    sleep "$update_interval"
done
