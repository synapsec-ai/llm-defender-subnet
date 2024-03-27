from llm_defender.core.miners import miner
from argparse import ArgumentParser
import pytest
import uuid
from unittest.mock import MagicMock
from pathlib import Path
import bittensor as bt
import shutil
import torch 

class TestMiner:

    @classmethod
    def setup_class(cls):

        cls.wallet = MagicMock(spec=bt.wallet)
        cls.wallet.name = "test-wallet"
        cls.wallet.hotkey = "rzmejftlbjtdukjfjxygklcccmovxrra"

        cls.tmp_dir = Path(f"/tmp/pytest-{uuid.uuid4()}")
        cls.tmp_dir.mkdir(parents=True, exist_ok=True)

        cls.netuid = 38

        cls.netuid = 38

        cls.parser = ArgumentParser()
        cls.parser.add_argument(
            "--logging.logging_dir", type=str, default=str(cls.tmp_dir)
        )
        cls.parser.add_argument("--wallet.name", type=str, default=cls.wallet.name)
        cls.parser.add_argument("--wallet.hotkey", type=str, default=cls.wallet.hotkey)
        cls.parser.add_argument("--wallet.path", type=str, default=str(cls.tmp_dir))
        cls.parser.add_argument("--netuid", type=int, default=cls.netuid)
        cls.parser.add_argument(
            "--subtensor.network", type=str, default="test"
        )

        cls.mock_config = bt.config(cls.parser)

        # Setup mock wallet
        cls.mock_wallet = bt.wallet(
            name=cls.wallet.name, hotkey=cls.wallet.hotkey, path=str(cls.tmp_dir)
        )
        cls.mock_wallet.create_if_non_existent(
            coldkey_use_password=False, hotkey_use_password=False
        )

        # Setup mock subtensor
        cls.mock_subtensor = bt.subtensor(config=cls.mock_config)

        # Setup mock dendrite
        cls.mock_dendrite = bt.dendrite(wallet=cls.mock_wallet)

        # Setup mock metagraph
        cls.mock_metagraph = MagicMock(spec=bt.metagraph)
        cls.mock_metagraph.netuid = 38
        cls.mock_metagraph.hotkeys = [cls.mock_wallet.hotkey.ss58_address]
        cls.mock_metagraph.S = torch.zeros(256)
        
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
            default="False",
            help="Determines if miner should set weights or not",
        )

        parser.add_argument(
            "--validator_min_stake",
            type=float,
            default=5120.0,
            help="Determine the minimum stake the validator should have to accept requests",
        )

        pytest_miner = miner.LLMDefenderMiner(parser=parser)
        

        yield pytest_miner

    @classmethod
    def teardown_class(cls):
        """Teardowns the test class"""

        shutil.rmtree(cls.tmp_dir, ignore_errors=False, onerror=None)

    def test_whitelist(self, pytest_miner):
        assert pytest_miner.check_whitelist(hotkey="5G4gJgvAJCRS6ReaH9QxTCvXAuc4ho5fuobR7CMcHs4PRbbX") is True