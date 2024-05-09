import pytest

from llm_defender.base.protocol import LLMDefenderProtocol


@pytest.fixture
def sample_protocol_instance():
    return LLMDefenderProtocol(
        output={"result": "sample_output"},
        synapse_uuid="sample_uuid",
        synapse_nonce="sample_nonce",
        synapse_timestamp="sample_timestamp",
        subnet_version=1,
        analyzer="sample_analyzer",
        synapse_signature="sample_signature",
        synapse_prompt="sample_prompt",
        synapse_hash="sample_hash"
    )


@pytest.fixture
def instance_with_null_values():
    return LLMDefenderProtocol(
        output=None,
        synapse_uuid="sample_uuid",
        synapse_nonce="sample_nonce",
        synapse_timestamp="sample_timestamp",
        subnet_version=1,
        analyzer=None,
        synapse_signature="sample_signature",
        synapse_prompt=None,
        synapse_hash=None
    )


def test_deserialize(sample_protocol_instance):
    deserialized_instance = sample_protocol_instance.deserialize()
    assert isinstance(deserialized_instance, LLMDefenderProtocol)
    assert deserialized_instance == sample_protocol_instance


def test_nullable_fields_with_values(sample_protocol_instance):
    assert isinstance(sample_protocol_instance.output, (dict, type(None)))
    assert isinstance(sample_protocol_instance.analyzer, (str, type(None)))
    assert isinstance(sample_protocol_instance.synapse_prompt, (str, type(None)))
    assert isinstance(sample_protocol_instance.synapse_hash, (str, type(None)))


def test_synapse_uuid_required():
    with pytest.raises(ValueError):
        LLMDefenderProtocol(
            output={"result": "sample_output"},
            synapse_nonce="sample_nonce",
            synapse_timestamp="sample_timestamp",
            subnet_version=1,
            analyzer="sample_analyzer",
            synapse_signature="sample_signature",
            synapse_prompt="sample_prompt",
            synapse_hash="sample_hash"
        )


def test_synapse_nonce_required():
    with pytest.raises(ValueError):
        LLMDefenderProtocol(
            synapse_uuid="sample_uuid",
            synapse_timestamp="sample_timestamp",
            subnet_version=1,
            analyzer="sample_analyzer",
            synapse_signature="sample_signature",
            synapse_prompt="sample_prompt",
            synapse_hash="sample_hash"
        )


def test_synapse_timestamp_required():
    with pytest.raises(ValueError):
        LLMDefenderProtocol(
            synapse_uuid="sample_uuid",
            subnet_version=1,
            analyzer="sample_analyzer",
            synapse_signature="sample_signature",
            synapse_prompt="sample_prompt",
            synapse_hash="sample_hash"
        )


def test_subnet_version_required():
    with pytest.raises(ValueError):
        LLMDefenderProtocol(
            synapse_uuid="sample_uuid",
            synapse_timestamp="sample_timestamp",
            analyzer="sample_analyzer",
            synapse_signature="sample_signature",
            synapse_prompt="sample_prompt",
            synapse_hash="sample_hash"
        )


def test_synapse_signature_required():
    with pytest.raises(ValueError):
        LLMDefenderProtocol(
            synapse_uuid="sample_uuid",
            synapse_timestamp="sample_timestamp",
            subnet_version=1,
            analyzer="sample_analyzer",
            synapse_prompt="sample_prompt",
            synapse_hash="sample_hash"
        )


def test_optional_fields_not_provided(instance_with_null_values):
    assert instance_with_null_values.output is None
    assert instance_with_null_values.analyzer is None
    assert instance_with_null_values.synapse_prompt is None
    assert instance_with_null_values.synapse_hash is None