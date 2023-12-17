module.exports = {
    apps : [
        {
            name: "llm-defender-subnet-updater-dev",
            interpreter: "/bin/bash",
            script: "./scripts/updater.sh",
            env: {
                "UPDATE_INTERVAL": 1800,
                "BRANCH": "dev/0.2.0"
            },
            max_restarts: 5
        }
    ]
} 