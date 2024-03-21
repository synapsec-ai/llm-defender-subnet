from llm_defender.base.protocol import LLMDefenderProtocol


def test_llm_defender_protocol():
    synapse_data = {
        "synapse_uuid": "sample_uuid",
        "synapse_nonce": "sample_nonce",
        "synapse_timestamp": "sample_timestamp",
        "subnet_version": 1,
        "analyzer": "sample_analyzer",
        "synapse_signature": "sample_signature"
    }
    protocol_instance = LLMDefenderProtocol(**synapse_data)
    assert protocol_instance.synapse_uuid == "sample_uuid"
    assert protocol_instance.synapse_nonce == "sample_nonce"
    assert protocol_instance.synapse_timestamp == "sample_timestamp"
    assert protocol_instance.subnet_version == 1
    assert protocol_instance.analyzer == "sample_analyzer"
    assert protocol_instance.synapse_signature == "sample_signature"
