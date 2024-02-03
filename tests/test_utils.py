import llm_defender.base.utils as utils


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


