module.exports = {
    apps: [
        {
            "name"                  : "validator",
            "script"                : "/home/m4k1/llm-defender-subnet/llm_defender/neurons/validator.py",
            "interpreter"           : "/home/m4k1/.venv-local/bin/python",
            "args"                  : "--netuid 38 --wallet.name m4k1_test_ck --wallet.hotkey m4k1_test_hk3 --subtensor.network test --logging.trace",
            "max_memory_restart"    : "5G"
        }
    ]
}
