from pathlib import Path
"""
_bot_package_path = Path()

def _set_bot_package_path(path: str):
    global _bot_package_path
    _bot_package_path = Path(path)

_set_bot_package_path(__path__[0])
"""
from .soundboardt import *
#from .soundboardt_collections import *
from .soundboard_bot import SoundBot

