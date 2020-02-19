import pytest

from ishi import has_volition
from .test_cases import test_cases


@pytest.mark.parametrize('text, expected', test_cases)
def test_ishi(text, expected):
    assert has_volition(text) == expected, text
