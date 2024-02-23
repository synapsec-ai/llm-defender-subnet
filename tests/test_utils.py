import llm_defender.base.utils as utils
import bittensor as bt
import pytest

def test_uid_validation():
    valid_uids = range(0, 256)
    invalid_uids = [
        -1,
        256,
        1.0,
        255.0,
        256.0,
        -1.0,
        True,
        False,
        [],
        {},
        [1],
        ["foo"],
        {"foo": "bar"},
        set([1, 2]),
        set(),
    ]
    for _, uid in enumerate(valid_uids):
        assert utils.validate_uid(uid=uid) is True

    for _, uid in enumerate(invalid_uids):
        assert utils.validate_uid(uid=uid) is False


def test_numerical_value_validation():

    # Valid combinations
    value = [
        0.0,
        0.0000000000000000000000001,
        0.1,
        0.5,
        0.9,
        1.0,
        0.9999999999999999999999999999999999,
        0,
        1,
    ]
    value_type = [float, float, float, float, float, float, float, int, int]
    min_value = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0, 0]
    max_value = [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1, 1]

    for i, _ in enumerate(value):
        print(value[i])
        assert (
            utils.validate_numerical_value(
                value=value[i],
                value_type=value_type[i],
                min_value=min_value[i],
                max_value=max_value[i],
            )
            is True
        )

    # Invalid combinations
    value = [-0.1, 1.1, -1, 2, "foo", None, True, False, {}, []]
    value_type = [float, float, int, int, float, float, float, float, float, float]
    min_value = [0.0, 0.0, 0, 0, 0, 0, 0, 0, 0, 0]
    max_value = [1.0, 1.0, 1, 1, 1, 1, 1, 1, 1, 1]

    for i, _ in enumerate(value):
        print(value[i])
        assert (
            utils.validate_numerical_value(
                value=value[i],
                value_type=value_type[i],
                min_value=min_value[i],
                max_value=max_value[i],
            )
            is False
        )


def _get_engine_response(name, confidence, data):
    engine_response = {
        "name": name,
        "confidence": confidence,
        "data": data,
    }
    return engine_response


def test_response_data_validation():

    # Valid combinations
    engine_response = _get_engine_response(
        name="engine:text_classification",
        confidence=0.0,
        data={"outcome": "SAFE", "score": 0.9999998807907104},
    )
    assert utils.validate_response_data(engine_response=engine_response) is True

    # Invalid combinations
    for _,value in enumerate([None, "", True, False, [], {}]):
        engine_response = _get_engine_response(
            name=value,
            confidence=0.0,
            data={"outcome": "SAFE", "score": 0.9999998807907104},
        )
        assert utils.validate_response_data(engine_response=engine_response) is False

    engine_response = _get_engine_response(
        name="engine:text_classification",
        confidence=0.0,
        data={"outcome": "SAFE", "score": 0.9999998807907104},
    )
    engine_response.pop("name")
    assert utils.validate_response_data(engine_response=engine_response) is False

    # Invalid combinations
    for _,value in enumerate([None, "", True, False, [], {}, [1,2,3], {"foo": "bar"}]):
        engine_response = value
        assert utils.validate_response_data(engine_response=engine_response) is False

def test_signatures_and_validation():
    # Setup
    wallet = bt.wallet(name="test_coldkey", hotkey="test_hotkey").create_if_non_existent(coldkey_use_password=False, hotkey_use_password=False)

    # Valid combinations
    data = "foobar"
    signature = utils.sign_data(data=data, wallet=wallet)
    assert utils.validate_signature(hotkey=wallet.hotkey.ss58_address, data=data, signature=signature) is True

    assert utils.validate_signature(hotkey="5EjwQEJtbhcbZmWtpTVhQV8NGbYULS6djErtLbH8EJY1v9vg", data=data, signature="524e982b34b15fc96f680878c5c7ab38b784a1f49c80316f505b1f440a2f2e121e3a5f4aa23d373b009ec85a191e2de3a3ed0c6d3355a591ed5e841803100687") is True

    # Invalid combinations
    for _,entry in enumerate([True, False, 1, "foo", [], {}, "a293f9502c45fff1460f451f3c43472824300beb947fe595502fc5ff8e48b7592349b89d08cc170852120f69141e9c9425200ba104b11c850b710e7ee64e2a88", "5EjwQEJtbhcbZmWtpTVhQV8NGbYULS6djErtLbH8EJY1v9vg", {"foo": "bar"}, 0.0, -1, 0]):
        assert utils.validate_signature(hotkey=entry, data=data, signature=signature) is False
        assert utils.validate_signature(hotkey=wallet.hotkey.ss58_address, data=entry, signature=signature) is False
        assert utils.validate_signature(hotkey=wallet.hotkey.ss58_address, data=data, signature=entry) is False
        assert utils.validate_signature(hotkey=entry, data=entry, signature=entry) is False
        assert utils.validate_signature(hotkey=wallet.hotkey.ss58_address, data=entry, signature=entry) is False
        assert utils.validate_signature(hotkey=entry, data=entry, signature=signature) is False
        assert utils.validate_signature(hotkey=entry, data=data, signature=signature) is False

        with pytest.raises(AttributeError):
            utils.sign_data(data=data, wallet=entry)
    
    for _,entry in enumerate([True, False, 1, [], {}, {"foo": "bar"}, [1,2], ["foo", "bar"]]):
        with pytest.raises(AttributeError):
                utils.sign_data(data=entry, wallet=wallet)
