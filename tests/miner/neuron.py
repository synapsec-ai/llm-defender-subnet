from llm_defender.core.miners import miner
from argparse import ArgumentParser
import pytest
import uuid
from unittest.mock import MagicMock
from pathlib import Path
import bittensor as bt

class TestMiner:

    @classmethod
    def setup_class(cls):

        cls.wallet = MagicMock(spec=bt.wallet)
        cls.wallet.name = "test-wallet"
        cls.wallet.hotkey = "rzmejftlbjtdukjfjxygklcccmovxrra"

        cls.tmp_dir = Path(f"/tmp/pytest-{uuid.uuid4()}")
        cls.tmp_dir.mkdir(parents=True, exist_ok=True)

        cls.netuid = 38
        
    @pytest.fixture
    def pytest_miner(self):
        # Initialize validator with valid configuration
        parser = ArgumentParser()
        parser.add_argument(
            "--logging.logging_dir", type=str, default=str(self.tmp_dir)
        )
        parser.add_argument("--wallet.name", type=str, default=self.wallet.name)
        parser.add_argument("--wallet.hotkey", type=str, default=self.wallet.hotkey)
        parser.add_argument("--wallet.path", type=str, default=str(self.tmp_dir))
        parser.add_argument("--netuid", type=int, default=self.netuid)
        parser.add_argument(
            "--subtensor.network", type=str, default="test"
        )

        parser.add_argument(
            "--miner_set_weights",
            type=str,
            default="True",
            help="Determines if miner should set weights or not",
        )

        parser.add_argument(
            "--validator_min_stake",
            type=float,
            default=5120.0,
            help="Determine the minimum stake the validator should have to accept requests",
        )

        pytest_miner = miner.PromptInjectionMiner(parser=parser)

        yield pytest_miner

    def test_whitelist(self, pytest_miner):
        assert pytest_miner.check_whitelist(hotkey="5G4gJgvAJCRS6ReaH9QxTCvXAuc4ho5fuobR7CMcHs4PRbbX") is True