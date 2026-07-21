from dataclasses import dataclass, field
from typing import Optional, Literal, Tuple
from enum import Enum

@dataclass
class StatsTable:
    hp: int = 0
    atk: int = 0
    def_: int = 0  # Mapped from 'def'
    spa: int = 0
    spd: int = 0
    spe: int = 0

@dataclass
class BoostsTable:
    atk: int = 0
    def_: int = 0
    spa: int = 0
    spd: int = 0
    spe: int = 0
    evasion: int = 0
    accuracy: int = 0