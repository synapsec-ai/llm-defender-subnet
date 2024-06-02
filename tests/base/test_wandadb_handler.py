from unittest.mock import Mock, patch

from llm_defender import WandbHandler


sample_env_vars = {
    "WANDB_KEY": "sample_key",
    "WANDB_PROJECT": "sample_project",
    "WANDB_ENTITY": "sample_entity"
}

mocked_run = Mock()

def test_wandb_handler_init():
    with patch("os.environ.get", side_effect=sample_env_vars.get):
        with patch("wandb.login"), patch("wandb.init", return_value=mocked_run):
            handler = WandbHandler()

    assert handler.wandb_run == mocked_run

def test_wandb_handler_set_timestamp():
    with patch("wandb.login"), patch("wandb.init", return_value=mocked_run):
        handler = WandbHandler()
        handler.set_timestamp()
        assert isinstance(handler.log_timestamp, int)

def test_wandb_handler_log():
    with patch("wandb.login"), patch("wandb.init", return_value=mocked_run):
        handler = WandbHandler()
        handler.set_timestamp()

        with patch.object(handler.wandb_run, "log") as mocked_log:
            handler.log({"test_metric": 42})

        mocked_log.assert_called_once_with({"test_metric": 42}, handler.log_timestamp)
