import pytest


testdata = [
    ("tech", "Mid", 2, 35000, )
]


@pytest.fixture()
def test_main():
    assert True