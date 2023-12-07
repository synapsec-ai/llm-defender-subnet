#!/bin/bash

# Get the update interval from the environment variable, defaulting to 60 seconds
update_interval="${UPDATE_INTERVAL}"

while true; do
    branch="$BRANCH"
    # Change to the specified branch if provided
    if [[ -n "$branch" ]]; then
        echo "Switching to branch: $branch"
        git checkout "$branch" || { echo "Branch '$branch' does not exist."; exit 1; }
    fi
    git pull --all
    sleep "$update_interval"
done
