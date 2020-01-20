import pytest

from ishi import has_volition

test_cases = [
    # examples in the README
    ('自然言語処理の勉強をする', True),
    ('自然言語処理は楽しい', False),
    ('自然言語処理を学べる', False),
    ('自然言語処理の勉強を始めてびっくりした', False),
    ('自然言語処理の研究に必要なのは言語に対する深い洞察だ', False),
    # modality-based
    ('考えるつもりだ', True),
    ('考えなさい', True),
    ('考えて下さい', True),
    ('考えいただきたい', True),
    ('考えてもいい', True),
    ('考えるべきだ', True),
    # voice-based
    ('考えさせる', True),
    ('推論される', False),
    ('熟考できる', False),
    ('考えられる', False),
    ('走らされる', False),
    ('考えさせられる', False),
    # suffix-based
    ('考えがちだ', False),
    ('考えない', True),
    ('考えたい', True),
    ('考えやすい', False),
    ('考えておける', False),
    ('考えなくなる', False),
    ('考えてくれる', False),
    ('考えてしまう', False),
    ('考えて下さる', False),
    ('考え得る', False),
    ('考えすぎる', False),
    ('考えかねる', False),
    ('攻めあぐむ', False),
    ('攻めあぐねる', False),
    ('書きそびれる', False),
    ('罪人めく', False),
    ('考えちまう', False),
    ('考えやがる', False),
    # type-based
    ('美しい', False),
    ('花火だ', False),
    # meaning-based
    ('気付く', False),
    ('びっくりする', False),
    ('飲める', False),
    ('飲める', False),
    ('温まる', False),
    # real examples
    ('隣の住人が荷物を乱雑においている', True),
    ('扉に張り紙を貼らないでほしい', True),
    ('２台までしか契約できない', False),
    ('ユニットバスが安っぽすぎる', False),
    ('上の階から足音がする', False),
    ('各戸で自由に契約できる', False),
    ('オーナーの都合だけで急に退去依頼が来る', False),
    ('賃貸に住んでいる', True),
    ('窓が工夫されていない', False),
    ('マンションに標準でつけてほしい', True),
    ('ペットを飼っている', True),
    ('一生ここに住む', True),
    ('部外者が勝手に停める', True),
    ('興味を持つ', False),  # 2020/01/08: future work
    ('待ち時間を減らすことは出来ない', False)  # 2020/01/16
]


@pytest.mark.parametrize('text, expected', test_cases)
def test_ishi(text, expected):
    assert has_volition(text) == expected, text
