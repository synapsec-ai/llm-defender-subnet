module.exports = {
    apps : [
        {
            name: "llm-defender-subnet-miner",
            interpreter: "/bin/bash",
            script: "./scripts/run.sh",
            watch: ["./llm_defender", "./scripts/run.sh", "./scripts/prep.py", "setup.cfg"],
            env: {
                "branch": "main",
                "netuid": "14",
                "profile": "miner"
            },
            max_restarts: 5
        }
    ]
} 