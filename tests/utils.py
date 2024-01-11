import llm_defender.base.utils as utils


def test_uid_validation():
    valid_uids = range(0,256)
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
        set([1,2]),
        set()
    ]
    for _,uid in enumerate(valid_uids):
        assert utils.validate_uid(uid=uid) is True
    
    for _,uid in enumerate(invalid_uids):
        assert utils.validate_uid(uid=uid) is False

