from argparse import ArgumentParser
import bittensor as bt
from unittest.mock import MagicMock
from llm_defender.core.validators import validator
from pathlib import Path
import uuid
import shutil
import torch
import pytest
from unittest.mock import patch
class TestValidator:
    @classmethod
    def setup_class(cls):
        """Setups the testing class

        We are creating mockup instances of the bittensor classes to
        execute the tests.
        """

        cls.subtensor = MagicMock(spec=bt.subtensor)
        cls.logging = MagicMock(spec=bt.logging)
        cls.wallet = MagicMock(spec=bt.wallet)
        cls.metagraph = MagicMock(spec=bt.metagraph)

        cls.wallet.name = "test-wallet"
        cls.wallet.hotkey = "rzmejftlbjtdukjfjxygklcccmovxrra"

        cls.tmp_dir = Path(f"/tmp/pytest-{uuid.uuid4()}")
        cls.tmp_dir.mkdir(parents=True, exist_ok=True)

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

    @classmethod
    def teardown_class(cls):
        """Teardowns the test class"""

        shutil.rmtree(cls.tmp_dir, ignore_errors=False, onerror=None)

    def test_validator_init_argparser(self):
        # Invalid argument parser parameters
        with pytest.raises(AttributeError):
            # Invalid type
            parser = "foo"
            subnet_validator = validator.PromptInjectionValidator(parser=parser)
            subnet_validator.apply_config(
                bt_classes=[self.subtensor, self.logging, self.wallet]
            )

            # Empty argparser
            parser = ArgumentParser()
            subnet_validator = validator.PromptInjectionValidator(parser=parser)
            subnet_validator.apply_config(
                bt_classes=[self.subtensor, self.logging, self.wallet]
            )

            # Invalid logpath
            parser = ArgumentParser()
            parser = ArgumentParser()
            parser.add_argument(
                "--logging.logging_dir", type=str, default="X:\\Foo\\Bar"
            )
            parser.add_argument("--wallet.name", type=str, default=self.wallet.name)
            parser.add_argument("--wallet.hotkey", type=str, default=self.wallet.hotkey)
            parser.add_argument("--netuid", type=int, default=self.netuid)
            subnet_validator = validator.PromptInjectionValidator(parser=parser)
            subnet_validator.apply_config(
                bt_classes=[self.subtensor, self.logging, self.wallet]
            )

    # def test_validator_init_check_invalid_logdir(self):
    #     # Invalid logging directory
    #     with pytest.raises(OSError):
    #         parser = ArgumentParser()
    #         parser.add_argument("--logging.logging_dir", type=str, default="/foo/bar")
    #         parser.add_argument("--wallet.name", type=str, default=self.wallet.name)
    #         parser.add_argument("--wallet.hotkey", type=str, default=self.wallet.hotkey)
    #         parser.add_argument("--netuid", type=int, default=self.netuid)

    #         subnet_validator = validator.PromptInjectionValidator(parser=parser)
    #         subnet_validator.apply_config(
    #             bt_classes=[self.subtensor, self.logging, self.wallet]
    #         )

    @pytest.fixture
    def setup_validator(self):
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

        valid_validator = validator.PromptInjectionValidator(parser=parser)

        yield valid_validator

    def test_validator_init_valid_config(self, setup_validator):
        assert (
            setup_validator.apply_config(
                bt_classes=[self.subtensor, self.logging, self.wallet]
            )
            is True
        )

    def test_validator_bittensor_setup_invalid_config(self, setup_validator):
        
        with pytest.raises(AttributeError):
            setup_validator.setup_bittensor_objects(neuron_config="foo")

    def test_validator_init_invalid_neuron(self, setup_validator):
        # Invalid neuron configuration
        with pytest.raises(AttributeError):
            # Invalid wallet
            setup_validator.apply_config(
                bt_classes=[self.subtensor, self.logging, self.wallet]
            )
            setup_validator.neuron_config = "foo"
            setup_validator.initialize_neuron()

        # Validate validator validation
        assert (
            setup_validator.validator_validation(
                self.metagraph, self.mock_wallet, self.subtensor
            )
            is False
        )

        with pytest.raises(IndexError):
            setup_validator.apply_config(
                bt_classes=[self.subtensor, self.logging, self.wallet]
            )
            setup_validator.initialize_neuron()

        self.metagraph.hotkeys = [
            str(uuid.uuid4()),
            self.mock_wallet.hotkey.ss58_address,
            str(uuid.uuid4()),
        ]
        assert (
            setup_validator.validator_validation(
                self.metagraph, self.mock_wallet, self.subtensor
            )
            is True
        )

    def test_validator_full_init(self, setup_validator):
        # Validate the validator can initialize correctly
        setup_validator.apply_config(
            bt_classes=[self.subtensor, self.logging, self.wallet]
        )

        setup_validator.setup_bittensor_objects = MagicMock(name="method")

        setup_validator.setup_bittensor_objects.return_value = (
            self.mock_wallet,
            self.mock_subtensor,
            self.mock_dendrite,
            self.mock_metagraph,
        )

        with patch.object(setup_validator, "_parse_args", return_value=None):
            assert setup_validator.initialize_neuron() is True
        assert setup_validator.wallet is self.mock_wallet
        assert setup_validator.subtensor is self.mock_subtensor
        assert setup_validator.dendrite is self.mock_dendrite
        assert setup_validator.metagraph is self.mock_metagraph
        assert torch.equal(
            setup_validator.scores,
            torch.zeros_like(self.mock_metagraph.S, dtype=torch.float32),
        )
    
