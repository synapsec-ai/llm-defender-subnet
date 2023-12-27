#!/bin/bash
declare -A args

parse_arguments() {
    local pm2_instance_names=false

    while [[ $# -gt 0 ]]; do
        if [[ $1 == "--pm2_instance_names" ]]; then
            pm2_instance_names=true
            shift
            continue
        elif [[ $1 == "--"* ]]; then
            pm2_instance_names=false
            arg_name=${1:2}  # Remove leading "--" from the argument name
        fi

        if [ "$pm2_instance_names" = true ]; then
            if [[ $1 == "--"* ]]; then
                pm2_instance_names=false
            else
                args["pm2_instance_names"]+=" $1"  # Concatenate values
            fi
        else
            args[$arg_name]=$1
        fi

        shift
    done

    for key in "${!args[@]}"; do
        echo "Argument: $key, Value: ${args[$key]}"
    done
}


generate_pm2_launch_file_and_launch() {
    echo "Generating PM2 launch file"
    local cwd=$(pwd)
    local neuron_script="${cwd}/llm_defender/neurons/${profile}.py"
    local interpreter="${VIRTUAL_ENV}/bin/python"
    local branch="${args['branch']}"
    local update_interval="${args['update_interval']}"
    local pm2_instance_names="${args['pm2_instance_names']}"
    
    cat <<EOF > llm-defender-auto-updater.config.js
module.exports = {
    apps: [
        {
            "name"                  : "llm-defender-auto-updater",
            "script"                : "${cwd}/scripts/auto_updater.py",
            "interpreter"           : "${interpreter}",
            "args"                  : "--branch ${branch} --pm2_instance_names ${pm2_instance_names} --update_interval ${update_interval}"
        }
    ]
}
EOF
    echo "Starting PM2 process"
    eval "pm2 start llm-defender-auto-updater.config.js"
}

echo "### START OF EXECUTION ###"
# Parse arguments and assign to associative array
parse_arguments "$@"

generate_pm2_launch_file_and_launch