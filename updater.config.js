module.exports = {
    apps : [
        {
            name: "llm-defender-subnet-updater",
            interpreter: "/bin/bash",
            script: "./scripts/updater.sh",
            env: {
                "UPDATE_INTERVAL": 1800,
                "BRANCH": "dev/engine_refactoring"
            },
            max_restarts: 5
        }
    ]
} 