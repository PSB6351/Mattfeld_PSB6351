from pathlib import Path
import rfc3987_syntax as h
import json
import pytest


@pytest.fixture
def valid_syntax_data():
    with open(Path("tests", "valid_syntax.json"), "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def invalid_syntax_data():
    with open(Path("tests", "invalid_syntax.json"), "r", encoding="utf-8") as f:
        return json.load(f)


def test_is_valid_syntax(valid_syntax_data):
    for term, valid_examples in valid_syntax_data.items():
        for valid_example in valid_examples:
            actual = h.is_valid_syntax(term=term, value=valid_example["value"])
            print("")
            print(
                f"Testing {term} with {valid_example['value']} : {valid_example['reason']}"
            )
            assert (
                actual is True
            ), f"Failed term: {term} for '{valid_example['value']}' : {valid_example['reason']}"
    assert True


def test_not_is_valid_syntax(invalid_syntax_data):
    for term, invalid_examples in invalid_syntax_data.items():
        for invalid_example in invalid_examples:
            actual = h.is_valid_syntax(term=term, value=invalid_example["value"])
            print("")
            print(
                f"Testing {term} with {invalid_example['value']} : {invalid_example['reason']}"
            )
            assert (
                actual is False
            ), f"Failed term: {term} for '{invalid_example['value']}' : {invalid_example['reason']}"
