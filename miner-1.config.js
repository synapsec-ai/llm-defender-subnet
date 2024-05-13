module.exports = {
    apps: [
        {
            "name"                  : "miner-1",
            "script"                : "/home/m4k1/llm-defender-subnet/llm_defender/neurons/miner.py",
            "interpreter"           : "/home/m4k1/.venv-local/bin/python",
            "args"                  : "--netuid 38 --wallet.name m4k1_test_ck --wallet.hotkey m4k1_test_hk2 --subtensor.network test --axon.port 15002 --logging.trace --validator_min_stake 0",
            "max_memory_restart"    : "10G"
        }
    ]
}
