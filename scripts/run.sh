#!/bin/bash
declare -A args

check_python_and_venv() {
    if [ -n "$VIRTUAL_ENV" ]; then
        echo "Virtual environment is activated: $VIRTUAL_ENV"
    else
        echo "WARNING: Virtual environment is not activated. It is recommended to run this script in a python venv."
    fi

    if ! python --version "$1" &>/dev/null; then
        echo "ERROR: Python is not available. Make sure Python is installed and venv has been activated."
        exit 1
    fi
}

parse_arguments() {

    while [[ $# -gt 0 ]]; do
        if [[ $1 == "--"* ]]; then
            arg_name=${1:2}  # Remove leading "--" from the argument name

            # Special handling for logging argument
            if [[ "$arg_name" == "logging"* ]]; then
                shift
                if [[ $1 != "--"* ]]; then
                    IFS='.' read -ra parts <<< "$arg_name"
                    echo ${parts[1]}
                    args[${parts[0]}]=${parts[1]}
                fi
            else
                shift
                args[$arg_name]="$1"  # Assign the argument value to the argument name
            fi
        fi
        shift
    done

    for key in "${!args[@]}"; do
        echo "Argument: $key, Value: ${args[$key]}"
    done
}

pull_repo_and_checkout_branch() {
    local script_path="scripts/run.sh"

    branch="$BRANCH"

    initial_hash=$(md5sum "$script_path" | awk '{ print $1 }')

    # Pull the latest repository
    git pull --all

    # Change to the specified branch if provided
    if [[ -n "$branch" ]]; thenlocal
        echo "Switching to branch: $branch"
        git checkout "$branch" || { echo "Branch '$branch' does not exist."; exit 1; }
    fi

    local current_branch=$(git symbolic-ref --short HEAD)
    git fetch &>/dev/null  # Silence output from fetch command
    if ! git rev-parse --quiet --verify "origin/$current_branch" >/dev/null; then
        echo "You are using a branch that does not exists in remote. Make sure your local branch is up-to-date with the latest version in the main branch."
    fi

    current_hash=$(md5sum "$script_path" | awk '{ print $1 }')

    if [ "$initial_hash" != "$current_hash" ]; then
        echo "The run.sh script has changed, exiting and letting pm2 to relaunch with the updated script"
        exit 2
    fi
}

install_packages() {
    local cfg_version=$(grep -oP 'version\s*=\s*\K[^ ]+' setup.cfg)
    local installed_version=$(pip show llm-defender | grep -oP 'Version:\s*\K[^ ]+')

    if [[ "$cfg_version" == "$installed_version" ]]; then
        echo "Subnet versions "$cfg_version" and "$installed_version" are matching: No installation is required."
    else
        echo "Installing package with pip"
        pip install -e .
    fi

    # Uvloop re-implements asyncio module which breaks bittensor. It is
    # not needed by the default implementation of the
    # llm-defender-subnet, so we can uninstall it.
    if pip show uvloop &>/dev/null; then
        echo "Uninstalling conflicting module uvloop"
        pip uninstall -y uvloop
    fi

    echo "Packages installed successfully"
}

run_preparation() {
    echo "Executing the preparation script"
    python scripts/prep.py

    if [ $? -eq 1 ]; then
        echo "Preparation script did not execute correctly"
        exit 1
    fi
    
    echo "Preparation script executed correctly"
}

run_neuron() {
    local subtensor_chain_endpoint="${args['subtensor.chain_endpoint']}"
    local wallet_name="${args['wallet.name']}"
    local wallet_hotkey="${args['wallet.hotkey']}"
    local logging_value="${args['logging']}"
    local subtensor_network="${args['subtensor.network']}"
    local axon_port="${args['axon.port']}"

    profile="$PROFILE"
    netuid="$NETUID"

    if [[ -z "$netuid" || -z "$wallet_name" || -z "$wallet_hotkey" ]]; then
        echo "netuid, wallet.name, and wallet.hotkey are mandatory arguments."
        exit 1
    fi

    if [[ "$profile" != "miner" && "$profile" != "validator" ]]; then
        echo "Invalid profile provided."
        exit 1
    fi

    local script_path="llm_defender/neurons/miner.py"
    if [[ "$profile" == "validator" ]]; then
        script_path="llm_defender/neurons/validator.py"
    fi

    local command="python $script_path --netuid $netuid --wallet.name $wallet_name --wallet.hotkey $wallet_hotkey"

    if [[ -n "$subtensor_chain_endpoint" ]]; then
        command+=" --subtensor.chain_endpoint $subtensor_chain_endpoint"
    fi

    if [[ -n "$subtensor_network" ]]; then
        command+=" --subtensor.network $subtensor_network"
    fi

    if [[ -n "$axon_port" ]]; then
        command+=" --axon.port $axon_port"
    fi

    if [[ -n "$logging_value" ]]; then
        command+=" --logging.$logging_value"
    fi

    echo "Running command: $command"
    eval "$command"
}

# Parse arguments and assign to associative array
parse_arguments "$@"

profile="${args['profile']}"

check_python_and_venv
echo "Python venv checks completed. Sleeping 2 seconds."
sleep 2
pull_repo_and_checkout_branch
echo "Repo pulled and branch checkout done. Sleeping 2 seconds."
sleep 2
install_packages
echo "Installation done. Sleeping 2 seconds."
sleep 2

if [[ "$profile" == "miner" ]]; then
    run_preparation
    echo "Preparation done. Sleeping 2 seconds."
fi

echo "Running neutron"
run_neuron
