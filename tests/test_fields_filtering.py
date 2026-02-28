from app.main import _select_dict_fields


def test_select_dict_fields_is_case_insensitive() -> None:
    data = {"Stars": 10, "forks": 4, "watchers": 7}
    assert _select_dict_fields(data, "stars,FORKS") == {"Stars": 10, "forks": 4}


def test_select_dict_fields_supports_none_sentinel() -> None:
    data = {"stars": 10, "forks": 4}
    assert _select_dict_fields(data, "__none__") == {}
    assert _select_dict_fields(data, "none") == {}
