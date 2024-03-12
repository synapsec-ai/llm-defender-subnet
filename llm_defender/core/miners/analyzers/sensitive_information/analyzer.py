import bittensor as bt

# Load wandb library only if it is enabled
from llm_defender import __wandb__ as wandb

if wandb is True:
    from llm_defender.base.wandb_handler import WandbHandler


class SensitiveInformationAnalyzer:

    def __init__(self, wallet: bt.wallet, subnet_version: int, wandb_handler, miner_uid: str):
        self.wallet = wallet
        self.miner_hotkey = self.wallet.hotkey.ss58_address
        self.subnet_version = subnet_version
        self.miner_uid = miner_uid

        # Enable wandb if it has been configured
        if wandb is True:
            self.wandb_enabled = True
            self.wandb_handler = wandb_handler
        else:
            self.wandb_enabled = False
            self.wandb_handler = None

    def execute(self):
        pass
