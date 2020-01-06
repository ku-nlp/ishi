import pytest

from ishi import has_volition

test_cases = [
    ('自然言語処理の勉強をする', True),
    ('自然言語処理は楽しい', False),
    ('自然言語処理を学べる', False),
    ('自然言語処理の勉強を始めてびっくりした', False),
    ('自然言語処理の研究に必要なのは言語に対する深い洞察だ', False),
    ('１階のエレベーター横の部屋の住人が玄関前の廊下に傘だてやベビーカー、スケートボードなどを乱雑においておる', False),
    ('エレベーターや扉にたくさん張り紙を貼らないでほしい', True),
    ('一家庭２台までしか駐輪場が契約できない', False),
    ('ユニットバスが安っぽすぎる', False),
    ('下の階からは、くしゃみの音が、上の階からは足音がする', False),
    ('上の階からピアノの音や掃除機の音がバンバンする', False),
    ('隣近所のベランダから煙草の煙とにおいがする', False),
    ('フロントの質の差が激しすぎる', False),
    ('興味を持つ', False),
    ('ガチャと大きな音がする', False),
    ('好きな場所（壁）にクーラーが設置出来ない', False),
    ('何処に設置する', True),
    ('各戸で自由に契約できる', False),
    ('オーナーの都合だけで急に退去依頼が来る', False),
    ('簡単に引越', True),
    ('賃貸に住んでいる', True),
    ('窓が工夫されていない', False),
    ('マンションに標準でつけてほしい', True),
    ('ペットを飼っている', True),
    ('一生ここに住む', True),
    ('あと３０年は生活', True),
    ('家の中までする', True),
    ('部外者が勝手に停める', False),
    ('苦情が寄せられる', False),
]


@pytest.mark.parametrize('text, expected', test_cases)
def test_ishi(text, expected):
    assert has_volition(text) == expected, text
