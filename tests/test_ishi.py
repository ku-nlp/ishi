import pytest

from ishi import has_volition

test_cases = [
    ('自然言語処理の勉強をする', True),
    ('自然言語処理は楽しい', False),
    ('自然言語処理を学べる', False),
    ('自然言語処理の勉強を始めてびっくりした', False),
    ('自然言語処理の研究に必要なのは言語に対する深い洞察だ', False)
]


@pytest.mark.parametrize('text, expected', test_cases)
def test_ishi(text, expected):
    assert has_volition(text) == expected
