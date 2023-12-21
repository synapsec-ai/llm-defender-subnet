module.exports = {
    apps : [
        {
            name: "llm-defender-subnet-updater-dev",
            interpreter: "/bin/bash",
            script: "./scripts/updater.sh",
            env: {
                "UPDATE_INTERVAL": 1800,
                "BRANCH": "main"
            },
            max_restarts: 5
        }
    ]
} 
