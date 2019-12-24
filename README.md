# Ishi: A volition classifier for Japanese

## Requirements

- Python v3.6 or later
- [Jumanpp](https://github.com/ku-nlp/jumanpp)

## Installation

To install Ishi, use pip.

```
$ pip install .
```

## How to Use

```python
from ishi import Ishi

ishi = Ishi()

# Ishi accepts strings
print(ishi('自然言語処理の勉強をする'))  # True
print(ishi('自然言語処理は楽しい'))  # False because "楽しい" is an adjective
print(ishi('自然言語処理を学べる'))  # False because "学べる" is a potential verb
print(ishi('自然言語処理の勉強を始めてびっくりした'))  # False because "びっくり (した)" is in a non-volition dictionary

# Ishi also accepts KNP outputs
from pyknp import KNP
knp = KNP()
knp_output = knp.parse('自然言語処理の研究に必要なのは言語に対する深い洞察だ')
print(ishi(knp_output))  # False
```
