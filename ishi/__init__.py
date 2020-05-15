from pathlib import Path
__version__ = Path(__file__).parent.joinpath('VERSION').open().read().rstrip()

from .ishi import Ishi
from .ishi import has_volition
