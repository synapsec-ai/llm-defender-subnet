module.exports = {
    apps : [
        {
            name: "llm-defender-subnet-validator",
            interpreter: "/bin/bash",
            script: "./scripts/run.sh",
            watch: ["./llm_defender", "./scripts/run.sh", "./scripts/prep.py", "setup.cfg"],
            env: {
                "BRANCH": "dev/auto_update_and_prepare_script",
                "NETUID": "14",
                "PROFILE": "validator"
            },
            max_restarts: 5
        }
    ]
} 