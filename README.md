# Ishi: A volition classifier for Japanese

## Requirements

- Python v3.6 or later
- [Jumanpp](https://github.com/ku-nlp/jumanpp)

## Installation

To install Ishi, use pip.

```
$ pip install .
```

## Use Ishi as a Python library

```python
from ishi import Ishi

ishi = Ishi()

string = '自然言語処理の勉強をする'
print(ishi(string))  # True

string = '自然言語処理は楽しい'
print(ishi(string))  # False

string = '自然言語処理の勉強を始めてびっくりした'
print(ishi(string))  # False

string = 'もっと構文解析の精度を上げてほしい'
print(ishi(string))  # True
```
