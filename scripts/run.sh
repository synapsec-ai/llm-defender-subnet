#!/bin/bash
declare -A args

parse_arguments() {

    while [[ $# -gt 0 ]]; do
        if [[ $1 == "--"* ]]; then
            arg_name=${1:2}  # Remove leading "--" from the argument name

            # Special handling for logging argument
            if [[ "$arg_name" == "logging"* ]]; then
                shift
                if [[ $1 != "--"* ]]; then
                    args["$arg_name"]=$1
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
    local branch="${args['branch']}"

    # Pull the latest repository
    git pull

    # Change to the specified branch if provided
    if [[ -n "$branch" ]]; then
        echo "Switching to branch: $branch"
        git checkout "$branch" || { echo "Branch '$branch' does not exist."; exit 1; }
    fi
}

install_packages() {
    local cfg_version=$(grep -oP 'version\s*=\s*\K[^ ]+' setup.cfg)
    local installed_version=$(pip show prompt-defender | grep -oP 'Version:\s*\K[^ ]+')

    if [[ "$cfg_version" == "$installed_version" ]]; then
        echo "Versions match: No action required."
    else
        echo "Installing package with pip"
        pip install -e .

        # Uvloop re-implements asyncio module which breaks bittensor. It is
        # not needed by the default implementation of the
        # prompt-defender-subnet, so we can uninstall it.
        if pip show uvloop &>/dev/null; then
            echo "Uninstalling conflicting module uvloop"
            pip uninstall -y uvloop
        fi

        echo "Packages installed successfully"
    fi
}

run_neuron() {
    local profile="${args['profile']}"
    local netuid="${args['netuid']}"
    local subtensor_chain_endpoint="${args['subtensor.chain_endpoint']}"
    local wallet_name="${args['wallet.name']}"
    local wallet_hotkey="${args['wallet.hotkey']}"
    local logging_value="${args['logging']}"
    local subtensor_network="${args['subtensor.network']}"

    if [[ -z "$netuid" || -z "$wallet_name" || -z "$wallet_hotkey" ]]; then
        echo "netuid, wallet.name, and wallet.hotkey are mandatory arguments."
        exit 1
    fi

    if [[ "$profile" != "miner" && "$profile" != "validator" ]]; then
        echo "Invalid profile provided."
        exit 1
    fi

    local script_path="prompt_defender/prompt_injection/miner/miner.py"
    if [[ "$profile" == "validator" ]]; then
        script_path="prompt_defender/prompt_injection/validator/validator.py"
    fi

    local command="python $script_path --netuid $netuid --wallet.name $wallet_name --wallet.hotkey $wallet_hotkey"

    if [[ -n "$subtensor_chain_endpoint" ]]; then
        command+=" --subtensor.chain_endpoint $subtensor_chain_endpoint"
    fi

    if [[ -n "$subtensor_network" ]]; then
        command+=" --subtensor.network $subtensor_network"
    fi

    if [[ -n "$logging_value" ]]; then
        command+=" --logging.$logging_value"
    fi

    echo "Running command: $command"
    eval "$command"
}

# Parse arguments and assign to associative array
parse_arguments "$@"

pull_repo_and_checkout_branch
install_packages
run_neuron
