module.exports = {
    apps: [
        {
            "name"                  : "",
            "script"                : "/mnt/llm-defender-subnet/llm_defender/neurons/validator.py",
            "interpreter"           : "/home/vboxuser/llm-defender-subnet/.venv/bin/python",
            "args"                  : "--netuid 38 --wallet.name validator --wallet.hotkey default --subtensor.network test --logging.debug",
            "max_memory_restart"    : ""
        }
    ]
}
