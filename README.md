# Ishi: A volition classifier for Japanese

## Requirements

- Python v3.6 or later
- [Jumanpp](https://github.com/ku-nlp/jumanpp)

## Installation

To install Ishi, use pip.

```
$ pip install .
```

## Use Ishi as a CLI application

```
$ echo '自然言語処理の勉強をする' | ishi
```

```
$ echo '自然言語処理は難しい' | ishi
```

## Use Ishi as a Python library

```python
from ishi import is_volition

string = '自然言語処理の勉強をする'
print(is_volition(string))
```
